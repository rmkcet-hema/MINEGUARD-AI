from ultralytics import YOLO
import cv2
import os

# ============================================================
# MINEGUARD AI - FIRE & SMOKE DETECTION
# YOLO11 + Webcam
# ============================================================

# Path to trained model
MODEL_PATH = r"E:\MINEGUARD\AI\runs\detect\runs\fire_smoke\weights\best.pt"

# Check model exists
if not os.path.exists(MODEL_PATH):
    print("ERROR: best.pt not found!")
    print("Expected location:")
    print(MODEL_PATH)
    exit()

# Load trained YOLO model
print("Loading MINEGUARD AI model...")
model = YOLO(MODEL_PATH)

print("Model loaded successfully!")
print("Classes:", model.names)

# Open laptop webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Camera could not be opened.")
    print("Check whether another application is using the camera.")
    exit()

# Set camera resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print("\n===================================")
print("   MINEGUARD AI - LIVE DETECTION")
print("===================================")
print("Press Q to quit")
print("Press S to save the current frame")
print("===================================\n")


while True:

    # Read camera frame
    ret, frame = cap.read()

    if not ret:
        print("ERROR: Could not read camera frame.")
        break

    # --------------------------------------------------------
    # YOLO Detection
    # --------------------------------------------------------
    results = model(
        frame,
        conf=0.35,
        verbose=False
    )

    # Draw YOLO bounding boxes
    output = results[0].plot()

    # Detection flags
    fire_detected = False
    smoke_detected = False

    detected_objects = []

    # --------------------------------------------------------
    # Read detected objects
    # --------------------------------------------------------
    if results[0].boxes is not None:

        for box in results[0].boxes:

            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            class_name = model.names[class_id]

            detected_objects.append(
                f"{class_name}: {confidence * 100:.1f}%"
            )

            # Convert name to lowercase
            name = class_name.lower()

            if "fire" in name:
                fire_detected = True

            if "smoke" in name:
                smoke_detected = True

    # --------------------------------------------------------
    # Determine overall status
    # --------------------------------------------------------

    if fire_detected and smoke_detected:

        status = "FIRE + SMOKE DETECTED"
        status_color = (0, 0, 255)

    elif fire_detected:

        status = "FIRE DETECTED"
        status_color = (0, 0, 255)

    elif smoke_detected:

        status = "SMOKE DETECTED"
        status_color = (0, 165, 255)

    else:

        status = "AREA CLEAR"
        status_color = (0, 255, 0)

    # --------------------------------------------------------
    # Top status banner
    # --------------------------------------------------------

    cv2.rectangle(
        output,
        (0, 0),
        (output.shape[1], 70),
        (20, 20, 20),
        -1
    )

    cv2.putText(
        output,
        "MINEGUARD AI",
        (20, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        output,
        status,
        (20, 58),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        status_color,
        2
    )

    # --------------------------------------------------------
    # Detection information panel
    # --------------------------------------------------------

    panel_x = output.shape[1] - 360

    cv2.rectangle(
        output,
        (panel_x, 90),
        (output.shape[1] - 15, 230),
        (15, 20, 25),
        -1
    )

    cv2.putText(
        output,
        "AI DETECTION",
        (panel_x + 15, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    # Display detected objects
    if detected_objects:

        y = 155

        for obj in detected_objects[:4]:

            cv2.putText(
                output,
                obj,
                (panel_x + 15, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 255),
                2
            )

            y += 25

    else:

        cv2.putText(
            output,
            "No hazard detected",
            (panel_x + 15, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 0),
            2
        )

    # --------------------------------------------------------
    # Show live window
    # --------------------------------------------------------

    cv2.imshow(
        "MINEGUARD AI - Fire & Smoke Detection",
        output
    )

    # --------------------------------------------------------
    # Keyboard controls
    # --------------------------------------------------------

    key = cv2.waitKey(1) & 0xFF

    # Q = quit
    if key == ord("q"):
        break

    # S = save screenshot
    elif key == ord("s"):

        filename = "mineguard_detection.jpg"

        cv2.imwrite(
            filename,
            output
        )

        print(
            f"Detection screenshot saved: {filename}"
        )


# ------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------

cap.release()
cv2.destroyAllWindows()

print("\nMINEGUARD AI stopped.")