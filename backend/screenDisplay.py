import cv2

# Open the default webcam (index 0)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("Press 'q' to quit | Press 's' to save a frame")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Error: Failed to read frame.")
        break

    # Show the frame
    cv2.imshow("Video Frame - Press Q to quit", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif key == ord('s'):
        cv2.imwrite("saved_frame.jpg", frame)
        print("Frame saved as saved_frame.jpg")

# Cleanup
cap.release()
cv2.destroyAllWindows()