from ultralytics import YOLO

# Load a model
model = YOLO("yolov8n.yaml")  # build a new model from scratch

# Train the model using the annotated data
results = model.train(data="data.yaml", epochs=1)  