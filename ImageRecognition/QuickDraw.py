import torch
import torchvision.transforms as transforms
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights
from PIL import Image

print("Loading PyTorch MobileNetV2...")
# Load a pre-trained standard vision model compatible with standard Python PyTorch
weights = MobileNet_V2_Weights.DEFAULT
model = mobilenet_v2(weights=weights)
model.eval()

# Standard preprocessing pipeline for torchvision models
preprocess = weights.transforms()

def recognize_sketch(image_path):
    try:
        # 1. Load image and ensure RGB
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Error loading image at {image_path}: {e}")
        return None, 0.0

    # 2. Apply standard transformations (Resize, Normalize, Tensor conversion)
    input_tensor = preprocess(img).unsqueeze(0)  # Shape: (1, 3, 224, 224)

    # 3. Run Inference
    with torch.no_grad():
        output = model(input_tensor)

    # 4. Get probabilities using Softmax
    probabilities = torch.nn.functional.softmax(output[0], dim=0)
    top_prob, top_catid = torch.max(probabilities, dim=0)

    # Get class name using torchvision metadata
    category_name = weights.meta["categories"][top_catid]
    confidence = top_prob.item() * 100

    print(f"\n--- AI Guess ---")
    print(f"Prediction: {category_name.upper()} ({confidence:.2f}% confidence)")
    return category_name, confidence

if __name__ == "__main__":
    recognize_sketch("ImageRecognition/banana.jpg")
    recognize_sketch("ImageRecognition/cat.jpg")
    recognize_sketch("ImageRecognition/my_sketch.png")