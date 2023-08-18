from ultralytics import YOLO

model = YOLO('models/best.pt')


def predict(image_path):
    return model.predict(image_path, conf=0.5)
