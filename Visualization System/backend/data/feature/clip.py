import torch
import clip
from PIL import Image
import torchvision.transforms as transforms
import torch

def clip_load_model():
    # 选择设备（如果有 GPU 则使用 GPU）
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(device)
    # 加载 CLIP 模型
    model, preprocess = clip.load("ViT-B/32", device=device)
    
    return {"model": model, "preprocess": preprocess, "device": device}


def clip_model_get_feature(clip_model, image_path, boxes):
    model, preprocess, device = clip_model["model"], clip_model["preprocess"], clip_model["device"]

    image = Image.open(image_path).convert("RGB")
    cropped_images = [image.crop(box) for box in boxes]
    preprocessed_images = [preprocess(img) for img in cropped_images]

    image_tensor = torch.stack(preprocessed_images).to(device)

    with torch.no_grad():
        image_features = model.encode_image(image_tensor)
    image_features /= image_features.norm(dim=-1, keepdim=True)

    return image_features.cpu().numpy()