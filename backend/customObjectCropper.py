import cv2
import os
import sys

# ensure dataset always goes to project root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATASET_DIR = os.path.join(PROJECT_ROOT, "pytorch_dataset_object")

if len(sys.argv) > 1:
    SUBFOLDER = sys.argv[1].strip()
else:
    SUBFOLDER = input("Enter a label with no special characters or anything...\n").strip()

# use DATASET_DIR 
folder = os.path.join(DATASET_DIR, SUBFOLDER)
os.makedirs(folder, exist_ok=True)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Get actual resolution after setting
ret, frame = cap.read()
height, width, _ = frame.shape
print(f"Resolution: {width}x{height}")

box_size = 600
x1 = (width // 2) - (box_size // 2)
y1 = (height // 2) - (box_size // 2)
x2 = (width // 2) + (box_size // 2)
y2 = (height // 2) + (box_size // 2)

frame_count = 0
saved_count = 0
save_interval = 10

print("Press 'q' to quit")

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    if not ret:
        print("Error: Failed to read frame.")
        break

    # 1. Dim the whole frame first
    dimmed_frame = (frame * 0.5).astype('uint8')

    # 2. Restore the ROI (bright box in the center)
    dimmed_frame[y1:y2, x1:x2] = frame[y1:y2, x1:x2]

    # 3. Draw rectangle on top of dimmed frame
    cv2.rectangle(dimmed_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

    # 4. Show saved count
    cv2.putText(dimmed_frame, f"Saved: {saved_count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow('frame', dimmed_frame)

    # Save ROI at interval
    if frame_count % save_interval == 0:
        roi = frame[y1:y2, x1:x2]
        filename = os.path.join(folder, f"frame_{frame_count:04d}.jpg")
        cv2.imwrite(filename, roi)
        saved_count += 1

    frame_count += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print(f"Done. Saved {saved_count} frames to '{folder}/'")