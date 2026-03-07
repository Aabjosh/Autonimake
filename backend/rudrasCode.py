### WRITE UR STUFF FOR MANAGING THE HAND TRAKCING ROIS HERE

# Import  libraries
import cv2
import mediapipe as mp

# Initialize video capture
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Initialize Mediapipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

try:
    while cv2.waitKey(1) & 0xFF != ord('q'):
        success, frame = cap.read()
        if not success:
            break

        # Flip for mirror effect and convert to RGB
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process frame to detect hands
        result = hands.process(rgb_frame)

        if result.multi_hand_landmarks and result.multi_handedness:
            for idx, hand_landmarks in enumerate(result.multi_hand_landmarks):
                # Draw hand landmarks and connections
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Get hand label (Left or Right)
                hand_label = result.multi_handedness[idx].classification[0].label

                # Display label on top of wrist (landmark 0)
                wrist = hand_landmarks.landmark[0]
                x = int(wrist.x * 640)
                y = int(wrist.y * 480)
                cv2.putText(frame, hand_label, (x - 30, y - 10),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Show the frame
        cv2.imshow("Two-Hand Tracking", frame)

finally:
    cap.release()
    hands.close()
    cv2.destroyAllWindows()