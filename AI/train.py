from ultralytics import YOLO

# Load pretrained YOLO11 nano model
model = YOLO("yolo11n.pt")

# Train on fire + smoke dataset
model.train(
    data="fire-smoke-detection.v1-v1.yolov11/data.yaml",
    epochs=50,
    imgsz=640,
    batch=8,
    project="runs",
    name="fire_smoke"
)

print("\nTRAINING COMPLETED!")
print("Best model saved at:")
print("runs/fire_smoke/weights/best.pt")