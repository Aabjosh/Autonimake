import cv2
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import os

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATASET_DIR  = os.path.join(PROJECT_ROOT, "pytorch_dataset")
MODEL_PATH = os.path.join(PROJECT_ROOT, "test_model.pth")
KERNEL_SIZE = 3
CONFIDENCE_THRESHOLD = 60.0

# load class names directly from dataset folders
classes     = sorted(os.listdir(DATASET_DIR))
num_classes = len(classes)
print(f"Classes: {classes}")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# must match your training architecture exactly
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

# load trained weights
model = neural_network(num_classes).to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
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
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

ret, frame = cap.read()
h, w, _  = frame.shape
box_size = 600
x1 = (w // 2) - (box_size // 2)
y1 = (h // 2) - (box_size // 2)
x2 = (w // 2) + (box_size // 2)
y2 = (h // 2) + (box_size // 2)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    roi = frame[y1:y2, x1:x2]

    with torch.no_grad():
        outputs = model(preprocess(roi))
        probs   = torch.softmax(outputs, dim=1)
        conf, pred = torch.max(probs, 1)
        label  = classes[pred.item()]
        conf   = conf.item() * 100

    # green if confident, red if unsure
    color = (0, 255, 0) if conf >= CONFIDENCE_THRESHOLD else (0, 0, 255)

    # dim everything outside the box
    dimmed = (frame * 0.5).astype('uint8')
    dimmed[y1:y2, x1:x2] = frame[y1:y2, x1:x2]

    # draw box and label
    cv2.rectangle(dimmed, (x1, y1), (x2, y2), color, 2)
    cv2.putText(dimmed, f"{label}  {conf:.1f}%", (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    # if below threshold show "unknown"
    if conf < CONFIDENCE_THRESHOLD:
        cv2.putText(dimmed, "unknown", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

    cv2.imshow("Recognition", dimmed)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()