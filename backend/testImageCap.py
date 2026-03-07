import cv2
import os

# Open the default webcam (index 0)
cap = cv2.VideoCapture(0)
frame_count = 0
saved_count = 0
save_interval = 5


folder = 'pytorch_dataset'
if not os.path.exists(folder):
    os.makedirs(folder)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("Press 'q' to quit | Press 's' to save a frame")


while True:
    ret, frame = cap.read()

    if not ret:
        print("Error: Failed to read frame.")
        break

    if frame_count % save_interval == 0:
        filename = os.path.join(folder, f"frame_{frame_count:04d}.jpg")
        cv2.imwrite(filename,frame)
        saved_count += 1

    frame_count +=1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()