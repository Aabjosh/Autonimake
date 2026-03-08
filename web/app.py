from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import os
import sys
import shutil
import json
import zipfile
import io

app = Flask(__name__)
CORS(app)  # Allow CORS for local testing

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
OBJ_DATASET_DIR = os.path.join(PROJECT_ROOT, "pytorch_dataset_object")
HAND_DATASET_DIR = os.path.join(PROJECT_ROOT, "pytorch_dataset_hand")
MODEL_PATH = os.path.join(BACKEND_DIR, "test_model.pth")

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "connected"}), 200

@app.route('/api/train_trigger', methods=['POST'])
def train_trigger():
    data = request.json
    label = data.get('label')
    mode = data.get('mode', 'hands')

    if not label:
        return jsonify({"error": "Label is required"}), 400
    
    if mode == 'hands':
        script_name = "handCropper.py"
    else:
        script_name = "customObjectCropper.py"
        
    script_path = os.path.join(BACKEND_DIR, script_name)
    if not os.path.exists(script_path):
        return jsonify({"error": f"{script_name} not found"}), 500

    try:
        # Run it and pass the label as a command line argument natively
        process = subprocess.Popen([sys.executable, script_path, label], cwd=BACKEND_DIR)
        return jsonify({"message": f"Cropper started for label {label} in {mode} mode"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset_dataset', methods=['POST'])
def reset_dataset():
    """Wipe both dataset folders so users can start fresh."""
    hand_dir = HAND_DATASET_DIR
    obj_dir = OBJ_DATASET_DIR
    model_path = MODEL_PATH
    try:
        for d in [hand_dir, obj_dir]:
            if os.path.exists(d):
                shutil.rmtree(d)
            os.makedirs(d, exist_ok=True)
        if os.path.exists(model_path):
            os.remove(model_path)
        return jsonify({"message": "Dataset and model cleared."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/training_progress', methods=['GET'])
def training_progress():
    progress_file = os.path.join(BACKEND_DIR, "training_progress.json")
    if not os.path.exists(progress_file):
        return jsonify({"epoch": 0, "total_epochs": 1, "elapsed_seconds": 0}), 200
    try:
        with open(progress_file, "r") as f:
            data = json.load(f)
        return jsonify(data), 200
    except:
        return jsonify({"epoch": 0, "total_epochs": 1, "elapsed_seconds": 0}), 200

@app.route('/api/list_gestures', methods=['GET'])
def list_gestures():
    """List existing populated gesture folders for the given mode."""
    mode = request.args.get('mode', 'hands')
    dataset_dir = HAND_DATASET_DIR if mode == "hands" else OBJ_DATASET_DIR
    
    if not os.path.exists(dataset_dir):
        return jsonify({"gestures": []}), 200
        
    gestures = []
    for d in os.listdir(dataset_dir):
        d_path = os.path.join(dataset_dir, d)
        if os.path.isdir(d_path):
            count = len([f for f in os.listdir(d_path) if f.lower().endswith(('.jpg','.jpeg','.png','.webp'))])
            gestures.append({"name": d, "count": count})
            
    return jsonify({"gestures": gestures}), 200

@app.route('/api/delete_gesture', methods=['POST'])
def delete_gesture():
    data = request.json or {}
    name = data.get('name')
    mode = data.get('mode', 'hands')
    
    if not name:
        return jsonify({"error": "Name required"}), 400

    # Sanitize: only allow alphanumeric, underscore, hyphen (prevent path traversal)
    safe_name = "".join(c for c in name if c.isalnum() or c in "_-").strip() or name
        
    base_dir = os.path.abspath(HAND_DATASET_DIR if mode == "hands" else OBJ_DATASET_DIR)
    target_dir = os.path.abspath(os.path.join(base_dir, safe_name))
    
    # Security: ensure we're deleting within the dataset directory
    if not target_dir.startswith(base_dir):
        return jsonify({"error": "Invalid path"}), 400
    
    if os.path.exists(target_dir) and os.path.isdir(target_dir):
        try:
            shutil.rmtree(target_dir)
            return jsonify({"message": f"Deleted {safe_name}"}), 200
        except Exception as e:
            return jsonify({"error": f"Failed to delete: {str(e)}"}), 500
    return jsonify({"error": f"Folder '{safe_name}' not found"}), 404

@app.route('/api/rename_gesture', methods=['POST'])
def rename_gesture():
    data = request.json or {}
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    mode = data.get('mode', 'hands')
    
    if not old_name or not new_name:
        return jsonify({"error": "old_name and new_name required"}), 400
        
    base_dir = HAND_DATASET_DIR if mode == "hands" else OBJ_DATASET_DIR
    old_dir = os.path.join(base_dir, old_name)
    new_dir = os.path.join(base_dir, new_name)
    
    if not os.path.exists(old_dir):
        return jsonify({"error": "Original folder not found"}), 404
    if os.path.exists(new_dir):
        return jsonify({"error": "Destination name already exists"}), 400
        
    os.rename(old_dir, new_dir)
    return jsonify({"message": f"Renamed to {new_name}"}), 200


@app.route('/api/upload_marker_images', methods=['POST'])
def upload_marker_images():
    """
    Upload images for ML training. The label/identity tag you give becomes the trigger
    when the camera detects that pattern. Accepts multiple images or a .zip file.
    """
    # Accept both 'label' (identity tag) and 'direction' (legacy)
    label = request.form.get('label', '').strip() or request.form.get('direction', '').strip()
    if not label:
        return jsonify({"error": "Identity tag (label) is required. e.g. forward, stop, wave_left"}), 400

    # Sanitize to valid folder name: alphanumeric, underscore, hyphen only
    safe_label = "".join(c for c in label if c.isalnum() or c in "_-").strip().lower() or "untitled"
    if len(safe_label) > 64:
        safe_label = safe_label[:64]

    target_dir = os.path.join(OBJ_DATASET_DIR, safe_label)
    os.makedirs(target_dir, exist_ok=True)

    saved_count = 0
    image_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')

    # Check for zip file first
    zip_file = request.files.get('zip') or request.files.get('zipfile') or request.files.get('file')
    if zip_file and zip_file.filename and zip_file.filename.lower().endswith('.zip'):
        try:
            with zipfile.ZipFile(zip_file.stream, 'r') as zf:
                for name in zf.namelist():
                    if name.lower().endswith(image_extensions) and not name.startswith('__'):
                        try:
                            data = zf.read(name)
                            safe_name = os.path.basename(name)
                            if not safe_name:
                                continue
                            out_path = os.path.join(target_dir, safe_name)
                            # Avoid overwrite collisions
                            base, ext = os.path.splitext(safe_name)
                            idx = 0
                            while os.path.exists(out_path):
                                idx += 1
                                out_path = os.path.join(target_dir, f"{base}_{idx}{ext}")
                            with open(out_path, 'wb') as f:
                                f.write(data)
                            saved_count += 1
                        except Exception as e:
                            continue
        except zipfile.BadZipFile:
            return jsonify({"error": "Invalid or corrupted zip file"}), 400
        except Exception as e:
            return jsonify({"error": f"Failed to extract zip: {str(e)}"}), 500

    # Otherwise, accept multiple image files
    if saved_count == 0:
        files = request.files.getlist('files') or request.files.getlist('images') or request.files.getlist('file')
        if not files:
            files = [request.files.get('file'), request.files.get('image')]
            files = [f for f in files if f and f.filename]

        for f in files:
            if not f or not f.filename:
                continue
            if f.filename.lower().endswith(image_extensions):
                safe_name = os.path.basename(f.filename)
                out_path = os.path.join(target_dir, safe_name)
                base, ext = os.path.splitext(safe_name)
                idx = 0
                while os.path.exists(out_path):
                    idx += 1
                    out_path = os.path.join(target_dir, f"{base}_{idx}{ext}")
                try:
                    f.save(out_path)
                    saved_count += 1
                except Exception:
                    pass

    if saved_count == 0:
        return jsonify({"error": "No valid images found. Upload images or a zip file."}), 400

    return jsonify({
        "message": f"Saved {saved_count} image(s) to identity '{safe_label}'",
        "saved_count": saved_count,
        "label": safe_label
    }), 200

    
@app.route('/api/build_model', methods=['POST'])
def build_model():
    data = request.json or {}
    mode = data.get('mode', 'hands')
    # Pass 'h' or 'o' as first arg so pytorchBase doesn't block on input()
    mode_arg = "h" if mode == "hands" else "o"

    script_path = os.path.join(BACKEND_DIR, "pytorchBase.py")
    if not os.path.exists(script_path):
        return jsonify({"error": "pytorchBase.py not found"}), 500

    try:
        process = subprocess.Popen(
            [sys.executable, script_path, mode_arg],
            cwd=BACKEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ}
        )
        stdout, stderr = process.communicate(timeout=600)
        err_text = (stderr or b"").decode(errors="replace")
        out_text = (stdout or b"").decode(errors="replace")
        if process.returncode == 0:
            return jsonify({"message": "Model trained successfully!"}), 200
        else:
            if "ModuleNotFoundError" in err_text and "torch" in err_text:
                return jsonify({
                    "error": "PyTorch not installed. Run: pip install torch torchvision",
                    "details": err_text[:500]
                }), 500
            if "Need at least 2 populated classes" in err_text:
                return jsonify({
                    "error": "Need at least 2 identity tags with images. Upload images for 2+ different labels (e.g. forward, stop).",
                    "details": err_text[:300]
                }), 500
            return jsonify({"error": "Training failed", "details": err_text[:500] or out_text[:300]}), 500
    except subprocess.TimeoutExpired:
        process.kill()
        return jsonify({"error": "Training timed out (10 min)"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/start_detection', methods=['POST'])
def start_detection():
    """Launch the real-time handDisplay.py or objectDisplay.py detection window."""
    data = request.json or {}
    mode = data.get('mode', 'hands')

    if mode == 'hands':
        script_name = "handDispay.py"  # Note: original filename has typo
    else:
        script_name = "objectDisplay.py"

    script_path = os.path.join(BACKEND_DIR, script_name)
    if not os.path.exists(script_path):
        return jsonify({"error": f"{script_name} not found"}), 500

    # Clean old detection output
    det_file = os.path.join(BACKEND_DIR, "detection_output.json")
    if os.path.exists(det_file):
        os.remove(det_file)

    try:
        process = subprocess.Popen([sys.executable, script_path], cwd=BACKEND_DIR)
        return jsonify({"message": f"Detection started in {mode} mode"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/detection_feed', methods=['GET'])
def detection_feed():
    """Return the latest detection result from the shared JSON file."""
    det_file = os.path.join(BACKEND_DIR, "detection_output.json")
    if not os.path.exists(det_file):
        return jsonify({"label": None}), 200
    try:
        with open(det_file, "r") as f:
            data = json.load(f)
        return jsonify(data), 200
    except:
        return jsonify({"label": None}), 200


@app.route('/')
def serve_index():
    """Serve the main desktop UI."""
    return send_from_directory(SCRIPT_DIR, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (css, js, etc)."""
    return send_from_directory(SCRIPT_DIR, path)


if __name__ == '__main__':
    app.run(debug=True, port=8080)
