import torch
from PIL import Image
from transformers.image_utils import load_image
import open_clip
import numpy as np
from io import BytesIO

MODEL_PRESETS = {
    'best': 'convnextv2_huge.fcmae_ft_in22k_in1k_384',
    'balanced': 'convnextv2_base.fcmae_ft_in22k_in1k_384',
    'fast': 'efficientnet_b3.ra2_in1k',
    'fastest': 'mobilenetv3_large_100.ra_in1k',
    'semantic': 'vit_base_patch16_clip_224.openai',
    'newest': 'facebook/dinov3-vith16plus-pretrain-lvd1689m',
    'nextbest': 'ViT-H-14::laion2B-s32B-b79K',
    'newbest': 'ViT-bigG-14::laion2B-s39B-b160K'
}

class ImageEmbedder3:
    def __init__(self, preset='balanced', device=None):
        # Custom model string in format "MODEL::PRETRAINED"
        preset_name = MODEL_PRESETS.get(preset, preset)
        print(f"Loading model: {preset_name}")

        if "::" in preset_name:
            model_name, pretrained = preset_name.split("::")
        else:
            raise ValueError("Custom model format must be 'MODEL::PRETRAINED'")

        print(f"Loading OpenCLIP model: {model_name} ({pretrained})")

        # --- Load model & preprocessing ---
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name,
            pretrained=pretrained,
            device=device
        )
        self.device = device if device else torch.device('cpu')
        self.model.to(device)
        self.model.eval()

        # --- Get embedding dimension ---
        self.embed_dim = self.model.visual.output_dim
        print(f"✅ Model loaded successfully — embedding dimension: {self.embed_dim}")
    
    def get_embedding(self, image_url):
        """Extract normalized embedding from a single image"""
        try:
            img = load_image(image_url)
            if not isinstance(img, Image.Image):
                img = Image.fromarray(np.array(img))
            img_tensor = self.preprocess(img).unsqueeze(0).to(self.device)

            with torch.no_grad():
                image_features = self.model.encode_image(img_tensor)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            return image_features.cpu().numpy().flatten()

        except Exception as e:
            print(f"❌ Error processing {image_url}: {e}")
            return None