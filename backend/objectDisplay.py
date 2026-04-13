import cv2
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import os
import json
import time
import socket
import subprocess

# code for running powershell commands
subprocess.Popen(['ssh', 'pi@raspberrypi.local', 'python3', 'transferLayer.py'])
time.sleep(3)

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATASET_DIR  = os.path.join(PROJECT_ROOT, "pytorch_dataset_object")
MODEL_PATH   = os.path.join(SCRIPT_DIR, "test_model.pth")
DETECTION_OUTPUT = os.path.join(SCRIPT_DIR, "detection_output.json")
KERNEL_SIZE = 3
CONFIDENCE_THRESHOLD = 60.0

HUB_IP = '172.20.10.8'
PORT = 8000

# wifi stuff for connecting to pi (optional — won't crash if Pi is offline)
wifi_server = None
try:
    wifi_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    wifi_server.connect((HUB_IP, PORT))
    print(f"Connected to rover at {HUB_IP}:{PORT}")
except Exception as e:
    print(f"Warning: Could not connect to rover ({e}). Running in local-only mode.")
    wifi_server = None

def send_to_rover(label):
    global wifi_server
    if not wifi_server:
        try:
            wifi_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            wifi_server.connect((HUB_IP, PORT))
            print("Reconnected to rover")
        except Exception as e:
            wifi_server = None
            return
    try:
        wifi_server.sendall((f"ESP32_DRIVEBASE,{label}").encode())
        wifi_server.sendall((f"ESP32_SCREEN,1").encode())
        wifi_server.sendall((f"ESP32_SCREEN,driving!").encode())
    except Exception as e:
        print(f"Lost connection to rover: {e}, will retry next time")
        wifi_server = None

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class neural_network(nn.Module):
    def __init__(self, num_tags):
        super(neural_network, self).__init__()
        self.model = nn.Sequential(
            nn.Conv2d(3, 16, KERNEL_SIZE, padding=1),
            nn.BatchNorm2d(16), nn.ReLU(), nn.MaxPool2d(2,2),
            nn.Conv2d(16, 32, KERNEL_SIZE, padding=1),
            nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2,2),
            nn.Conv2d(32, 64, KERNEL_SIZE, padding=1),
            nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2,2),
            nn.Conv2d(64, 128, KERNEL_SIZE, padding=1),
            nn.BatchNorm2d(128), nn.ReLU(), nn.MaxPool2d(2,2),
            nn.Conv2d(128, 256, KERNEL_SIZE, padding=1),
            nn.BatchNorm2d(256), nn.ReLU(), nn.MaxPool2d(2,2),
            nn.Flatten(),
            nn.Linear(16384, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, num_tags)
        )

    def forward(self, x):
        return self.model(x)

def write_detection(label, confidence):
    try:
        with open(DETECTION_OUTPUT, "w") as f:
            json.dump({
                "label": label,
                "confidence": round(confidence, 1),
                "timestamp": time.time()
            }, f)
    except:
        pass

# load trained weights
checkpoint = torch.load(MODEL_PATH, map_location=device)
num_classes = checkpoint['model.24.bias'].shape[0]
classes = sorted([d for d in os.listdir(DATASET_DIR) if os.path.isdir(os.path.join(DATASET_DIR, d))])
model = neural_network(num_classes).to(device)
model.load_state_dict(checkpoint)
model.eval()

infer_transforms = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

def preprocess(frame):
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    return infer_transforms(img).unsqueeze(0).to(device)

# webcam setup
print("Initializing camera...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

ret, frame = cap.read()
h, w, _  = frame.shape
box_size = 240
x1 = (w // 2) - (box_size // 2)
y1 = (h // 2) - (box_size // 2)
x2 = (w // 2) + (box_size // 2)
y2 = (h // 2) + (box_size // 2)

# Throttle & Smoothing
last_sent_time = 0
SEND_INTERVAL = 3.0
smoothing_buffer = []
BUFFER_SIZE = 3
last_sent_label = None

try:
    while True:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)
        if not ret:
            break

        roi = frame[y1:y2, x1:x2]

        with torch.no_grad():
            outputs = model(preprocess(roi))
            probs   = torch.softmax(outputs, dim=1)
            conf, pred = torch.max(probs, 1)
            label = classes[pred.item()] if pred.item() < len(classes) else f"class_{pred.item()}"
            conf   = conf.item() * 100

        if conf >= CONFIDENCE_THRESHOLD:
            smoothing_buffer.append(label)
        else:
            smoothing_buffer.append("unknown")

        if len(smoothing_buffer) > BUFFER_SIZE:
            smoothing_buffer.pop(0)

        committed_label = smoothing_buffer[0] if len(smoothing_buffer) == BUFFER_SIZE and len(set(smoothing_buffer)) == 1 else "unknown"

        color = (0, 255, 0) if committed_label != "unknown" else (0, 0, 255)

        dimmed = (frame * 0.5).astype('uint8')
        dimmed[y1:y2, x1:x2] = frame[y1:y2, x1:x2]

        cv2.rectangle(dimmed, (x1, y1), (x2, y2), color, 2)

        if committed_label != "unknown":
            text = f"{committed_label}  {conf:.1f}%"

            # Only send to rover when label changes
            if committed_label != last_sent_label:
                send_to_rover(committed_label)
                last_sent_label = committed_label

            # Write to shared file for UI polling (throttled)
            now = time.time()
            if now - last_sent_time >= SEND_INTERVAL:
                write_detection(committed_label, conf)
                last_sent_time = now
        else:
            text = "unknown"

        cv2.putText(dimmed, text, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        cv2.imshow("Recognition", dimmed)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
    if os.path.exists(DETECTION_OUTPUT):
        os.remove(DETECTION_OUTPUT)