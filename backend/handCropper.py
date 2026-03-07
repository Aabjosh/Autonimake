import cv2
import mediapipe as mp
import os

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

print(f"Done. Saved {saved_count} frames to '{folder}/'")