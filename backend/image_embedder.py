import torch
from PIL import Image
import numpy as np
import timm
import requests
from io import BytesIO

MODEL_PRESETS = {
    'best': 'convnextv2_huge.fcmae_ft_in22k_in1k_384',
    'balanced': 'convnextv2_base.fcmae_ft_in22k_in1k_384',
    'fast': 'efficientnet_b3.ra2_in1k',
    'fastest': 'mobilenetv3_small_075.lamb_in1k',
    'semantic': 'vit_base_patch16_clip_224.openai',
    'newest': 'facebook/dinov3-vith16plus-pretrain-lvd1689m',
    'nextbest': 'ViT-H-14::laion2B-s32B-b79K'
}

class ImageEmbedder:
    def __init__(self, preset='balanced', device=None):
        model_name = MODEL_PRESETS.get(preset, preset)
        print(f"Loading model: {model_name}")
        
        self.model = timm.create_model(
            model_name,
            pretrained=True,
            num_classes=0,
        )
        
        self.device = device if device else torch.device('cpu')
        self.model.to(device)
        self.model.eval()
        
        data_config = timm.data.resolve_model_data_config(self.model)
        self.transform = timm.data.create_transform(**data_config, is_training=False)
        
        print(f"Model loaded! Embedding dimension: {self.model.num_features}")
    
    def get_embedding(self, image_url):
        try:
            # Fetch image from URL
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            # Load as Pillow image
            img = Image.open(BytesIO(response.content)).convert("RGB")
            img_tensor = self.transform(img).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                embedding = self.model(img_tensor)
            
            embedding = embedding.cpu().numpy().flatten()
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
        except Exception as e:
            print(f"Error processing image: {e}")
            return None