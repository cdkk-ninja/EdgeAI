from ultralytics import YOLO

# Load a pre-trained YOLO classification model (or your custom trained weights)
model = YOLO("ImageRecognition/yolov8n-cls.pt") 

# Predict what the sketch image is
results = model("ImageRecognition/my_sketch.png")
results = model("ImageRecognition/cat.jpg")
results = model("ImageRecognition/banana.jpg")
print(results[0].names[results[0].probs.top1])