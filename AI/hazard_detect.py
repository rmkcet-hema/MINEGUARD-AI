from ultralytics import YOLO
import cv2

# Load YOLO model
model = YOLO("yolo11n.pt")

# Open camera
cap = cv2.VideoCapture(0)

print("MINEGUARD AI - HAZARD DETECTION")
print("Press Q to exit")

while True:

    ret, frame = cap.read()

    if not ret:
        print("Camera not detected")
        break

    # YOLO detection
    results = model(frame)

    # Get detected objects
    detections = results[0].boxes

    person_count = 0

    for box in detections:

        cls = int(box.cls[0])
        confidence = float(box.conf[0])

        # COCO class 0 = person
        if cls == 0 and confidence > 0.50:
            person_count += 1

    # Draw detection results
    output = results[0].plot()

    # AI status
    if person_count > 0:

        cv2.putText(
            output,
            f"WORKER DETECTED: {person_count}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 0, 255),
            2
        )

    else:

        cv2.putText(
            output,
            "AREA CLEAR",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2
        )

    cv2.imshow(
        "MINEGUARD AI - HAZARD MONITOR",
        output
    )

    # Q = quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()