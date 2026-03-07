import cv2
import mediapipe as mp
import os

# Camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Mediapipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Dataset folder
folder = "pytorch_dataset"
os.makedirs(folder, exist_ok=True)

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

        results = hands.process(rgb)

        if results.multi_hand_landmarks:

            for hand_landmarks in results.multi_hand_landmarks:

                # mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Get bounding box from landmark extremes
                xs = []
                ys = []

                for lm in hand_landmarks.landmark:
                    xs.append(int(lm.x * 640))
                    ys.append(int(lm.y * 480))

                x_min = max(min(xs) - 20, 0)
                x_max = min(max(xs) + 20, 640)
                y_min = max(min(ys) - 20, 0)
                y_max = min(max(ys) + 20, 480)

                # Draw bounding box
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255,0,0), 2)

                # Crop hand ROI
                hand_crop = frame[y_min:y_max, x_min:x_max]

                # Save every 5th frame
                if frame_count % save_interval == 0 and hand_crop.size != 0:

                    filename = os.path.join(folder, f"hand_{saved_count:04d}.jpg")
                    cv2.imwrite(filename, hand_crop)
                    saved_count += 1

        frame_count += 1

        cv2.imshow("Hand Dataset Capture", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    hands.close()
    cv2.destroyAllWindows()