import cv2
import os

# Open the default webcam (index 0)
cap = cv2.VideoCapture(0)
frame_count = 0
saved_count = 0
save_interval = 5

ret,frame = cap.read()
height, width, _ = frame.shape
box_height = 600
box_width = 600

x1 = (width // 2) - (box_width // 2)
y1 = (height // 2) - (box_height // 2)
x2 = (width // 2) + (box_width // 2)
y2 = (height // 2) + (box_height // 2)


folder = 'pytorch_dataset'
if not os.path.exists(folder):
    os.makedirs(folder)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("Press 'q' to quit")


while True:
    ret, frame = cap.read()


    if not ret:
        print("Error: Failed to read frame.")
        break

    cv2.rectangle(frame, (x1,y1), (x2,y2), (0, 0, 255), 2)
    roi = frame[y1:y2, x1:x2]
    dimmed_frame = (frame * 0.5).astype('uint8')
    dimmed_frame[y1:y2, x1:x2] = frame[y1:y2, x1:x2]

    cv2.imshow('frame', dimmed_frame)

    if frame_count % save_interval == 0:
        filename = os.path.join(folder, f"frame_{frame_count:04d}.jpg")
        cv2.imwrite(filename,roi)
        saved_count += 1



    frame_count +=1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()

######