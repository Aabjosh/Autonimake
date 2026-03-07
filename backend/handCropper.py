import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os
import sys
import ssl
import urllib.request

# Resolve model path relative to THIS script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, "hand_landmarker.task")

if not os.path.exists(MODEL_PATH):
    print("Downloading hand landmark model (~5MB)...")
    # Workaround for macOS SSL certificate issue
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        MODEL_PATH
    )
    print("Model downloaded.")

if len(sys.argv) > 1:
    SUBFOLDER = sys.argv[1].strip()
else:
    SUBFOLDER = input("Enter a label with no special characters or anything...\n").strip()

folder = os.path.join('pytorch_dataset', SUBFOLDER)
os.makedirs(folder, exist_ok=True)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# New MediaPipe Tasks API
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)
detector = vision.HandLandmarker.create_from_options(options)

frame_count = 0
saved_count = 0
save_interval = 5

print("Press Q to quit")

try:
    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        height, width, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        results = detector.detect(mp_image)

        if results.hand_landmarks:
            hand_landmarks = results.hand_landmarks[0]

            xs = [int(lm.x * width) for lm in hand_landmarks]
            ys = [int(lm.y * height) for lm in hand_landmarks]

            x_min = max(min(xs) - 20, 0)
            x_max = min(max(xs) + 20, width)
            y_min = max(min(ys) - 20, 0)
            y_max = min(max(ys) + 20, height)

            # Draw bounding box
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)

            # Draw landmarks manually (replaces mp_drawing)
            for lm in hand_landmarks:
                cx, cy = int(lm.x * width), int(lm.y * height)
                cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

            roi = frame[y_min:y_max, x_min:x_max]

            if roi.size != 0 and frame_count % save_interval == 0:
                filename = os.path.join(folder, f"frame_{saved_count:04d}.jpg")
                cv2.imwrite(filename, roi)
                saved_count += 1

        frame_count += 1

        cv2.putText(frame, f"Saved: {saved_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.imshow("Hand Dataset Capture", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    detector.close()
    cv2.destroyAllWindows()

print(f"Done. Saved {saved_count} frames to '{folder}/'")








"""
import cv2
import mediapipe as mp
import os
import sys

if len(sys.argv) > 1:
    SUBFOLDER = sys.argv[1].strip()
else:
    SUBFOLDER = input("Enter a label with no special characters or anything...\n").strip()

folder = os.path.join('pytorch_dataset', SUBFOLDER)
os.makedirs(folder, exist_ok=True)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Mediapipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

frame_count = 0
saved_count = 0
save_interval = 5

print("Press Q to quit")

try:
    while True:

        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        height, width, _ = frame.shape

        results = hands.process(rgb)

        if results.multi_hand_landmarks:

            # Use first detected hand
            hand_landmarks = results.multi_hand_landmarks[0]
            mp.solutions.drawing_utils.draw_landmarks(frame,hand_landmarks,mp.solutions.hands.HAND_CONNECTIONS)
            xs = []
            ys = []

            for lm in hand_landmarks.landmark:
                xs.append(int(lm.x * width))
                ys.append(int(lm.y * height))

            # Dynamic bounding box (your method)
            x_min = max(min(xs) - 20, 0)
            x_max = min(max(xs) + 20, width)
            y_min = max(min(ys) - 20, 0)
            y_max = min(max(ys) + 20, height)

            # Draw bounding box
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255,0,0), 2)

            # Crop ROI
            roi = frame[y_min:y_max, x_min:x_max]

            if roi.size != 0:

                if frame_count % save_interval == 0:
                    filename = os.path.join(folder,
                                f"frame_{saved_count:04d}.jpg")
                    cv2.imwrite(filename, roi)
                    saved_count += 1

        frame_count += 1

        cv2.putText(frame, f"Saved: {saved_count}", (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

        cv2.imshow("Hand Dataset Capture", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    hands.close()
    cv2.destroyAllWindows()

print(f"Done. Saved {saved_count} frames to '{folder}/'")"""