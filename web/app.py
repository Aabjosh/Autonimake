from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import sys
import shutil
import json

app = Flask(__name__)
CORS(app)  # Allow CORS for local testing

from flask import Flask, request, jsonify, send_from_directory

@app.route('/')
def index():
    return send_from_directory(SCRIPT_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(SCRIPT_DIR, filename)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# SCRIPT_DIR is /Users/ayushgandhi/AutoIMake
BACKEND_DIR = os.path.join(SCRIPT_DIR, "..", "backend")  # go up one, then into backend

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
    hand_dir = os.path.join(SCRIPT_DIR, "Autonimake", "pytorch_dataset_hand")
    obj_dir = os.path.join(SCRIPT_DIR, "Autonimake", "pytorch_dataset_object")
    model_path = os.path.join(SCRIPT_DIR, "Autonimake", "test_model.pth")
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
    dataset_name = "pytorch_dataset_hand" if mode == "hands" else "pytorch_dataset_object"
    dataset_dir = os.path.join(SCRIPT_DIR, "Autonimake", dataset_name)
    
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
        
    dataset_name = "pytorch_dataset_hand" if mode == "hands" else "pytorch_dataset_object"
    target_dir = os.path.join(SCRIPT_DIR, "Autonimake", dataset_name, name)
    
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
        return jsonify({"message": f"Deleted {name}"}), 200
    return jsonify({"error": "Folder not found"}), 404

@app.route('/api/rename_gesture', methods=['POST'])
def rename_gesture():
    data = request.json or {}
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    mode = data.get('mode', 'hands')
    
    if not old_name or not new_name:
        return jsonify({"error": "old_name and new_name required"}), 400
        
    dataset_name = "pytorch_dataset_hand" if mode == "hands" else "pytorch_dataset_object"
    base_dir = os.path.join(SCRIPT_DIR, "Autonimake", dataset_name)
    old_dir = os.path.join(base_dir, old_name)
    new_dir = os.path.join(base_dir, new_name)
    
    if not os.path.exists(old_dir):
        return jsonify({"error": "Original folder not found"}), 404
    if os.path.exists(new_dir):
        return jsonify({"error": "Destination name already exists"}), 400
        
    os.rename(old_dir, new_dir)
    return jsonify({"message": f"Renamed to {new_name}"}), 200

    
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
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            return jsonify({"message": "Model trained successfully!"}), 200
        else:
            return jsonify({"error": "Training failed", "details": stderr.decode()}), 500
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

if __name__ == '__main__':
    app.run(debug=True, port=5001)
