import os
os.environ['GLOG_minloglevel'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import torch
import torchvision.transforms as transforms
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
from PIL import Image
import cv2
import numpy as np

print("Loading PyTorch MobileNetV3 (Small)...")
# Load pre-trained MobileNetV3 Small with default ImageNet weights
weights = MobileNet_V3_Small_Weights.DEFAULT
model = mobilenet_v3_small(weights=weights)
model.eval()

# Retrieve standard transformation pipeline from weights
preprocess = weights.transforms()

# Complete category label list matching the Quick, Draw! MobileViT / sketch classes 
# (Note: Standard ImageNet weights contain 1000 general classes. If you want specific 
# Pictionary / Quick Draw classes, a fine-tuned checkpoint or label map is required).
class_labels = weights.meta["categories"]

def recognize_sketch(image_path):
    # 1. Load sketch image
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Error: Could not read image at {image_path}")
        return None, 0.0

    # 2. Preprocess: Resize and invert (Quick, Draw! expects white lines on black background,
    # whereas ImageNet models expect dark features on light backgrounds or standard RGB objects).
    resized = cv2.resize(img, (224, 224))
    
    # Depending on how your sketch is drawn, you can toggle inversion:
    # If drawing is black ink on white paper, keep as is or invert to match training distribution.
    # PIL expects RGB image format.
    pil_img = Image.fromarray(resized).convert("RGB")

    # 3. Apply standard torchvision transforms (Resize, CenterCrop, Normalize to ImageNet stats)
    input_tensor = preprocess(pil_img).unsqueeze(0)  # Shape: (1, 3, 224, 224)

    # 4. Run Inference via PyTorch
    with torch.no_grad():
        output = model(input_tensor)

    # 5. Convert raw logits to probabilities using Softmax
    probabilities = torch.nn.functional.softmax(output[0], dim=0)
    top_prob, top_catid = torch.max(probabilities, dim=0)

    confidence = top_prob.item() * 100
    label = class_labels[top_catid]

    print(f"\n--- PyTorch MobileNetV3 Guess ---")
    print(f"Prediction: {label.upper()} ({confidence:.2f}% confidence)")
    return label, confidence

if __name__ == "__main__":
    recognize_sketch("ImageRecognition/my_sketch.png")
    recognize_sketch("ImageRecognition/banana.jpg")
    recognize_sketch("ImageRecognition/cat.jpg")