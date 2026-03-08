import cv2
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import os
import mediapipe as mp
import socket

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATASET_DIR  = os.path.join(PROJECT_ROOT, "pytorch_dataset_hand")
MODEL_PATH   = os.path.join(PROJECT_ROOT, "test_model.pth")

KERNEL_SIZE = 3
CONFIDENCE_THRESHOLD = 60.0

HUB_IP = '172.20.10.8'
PORT = 8000

# wifi stuff for connecting to pi
wifi_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
wifi_server.connect((HUB_IP, PORT))

# load classes
classes = sorted(os.listdir(DATASET_DIR))
num_classes = len(classes)
print(f"Classes: {classes}")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# model architecture
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

# load weights
model = neural_network(num_classes).to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()

infer_transforms = transforms.Compose([
    transforms.Resize((256,256)),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],
                         [0.229,0.224,0.225])
])

def preprocess(frame):
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    return infer_transforms(img).unsqueeze(0).to(device)

# Mediapipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7,
                       min_tracking_confidence=0.7)

# webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)

while True:

    ret, frame = cap.read()
    frame = cv2.flip(frame,1)

    if not ret:
        break

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb)

    display = frame.copy()

    if results.multi_hand_landmarks:
        
        hand_landmarks = results.multi_hand_landmarks[0]
        mp.solutions.drawing_utils.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
        xs = []
        ys = []

        for lm in hand_landmarks.landmark:
            xs.append(int(lm.x * w))
            ys.append(int(lm.y * h))

        x_min = max(min(xs) - 20, 0)
        x_max = min(max(xs) + 20, w)
        y_min = max(min(ys) - 20, 0)
        y_max = min(max(ys) + 20, h)

        roi = frame[y_min:y_max, x_min:x_max]

        if roi.size != 0:

            with torch.no_grad():

                outputs = model(preprocess(roi))
                probs   = torch.softmax(outputs, dim=1)

                conf, pred = torch.max(probs,1)

                label = classes[pred.item()]
                conf  = conf.item()*100

            color = (0,255,0) if conf >= CONFIDENCE_THRESHOLD else (0,0,255)

            cv2.rectangle(display,(x_min,y_min),(x_max,y_max),color,2)

            if conf >= CONFIDENCE_THRESHOLD:
                text = f"{label} {conf:.1f}%"
                wifi_server.sendall((f"ESP32_SCREEN,{label}").encode())
            else:
                text = "unknown"

            cv2.putText(display,text,(x_min,y_min-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.9,color,2)

    cv2.imshow("Recognition", display)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
hands.close()
wifi_server.close()
cv2.destroyAllWindows()