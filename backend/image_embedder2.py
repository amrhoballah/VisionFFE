import torch
import numpy as np
from transformers import AutoImageProcessor, AutoModel
from transformers.image_utils import load_image
from huggingface_hub import login


MODEL_PRESETS = {
    'best': 'convnextv2_huge.fcmae_ft_in22k_in1k_512',
    'balanced': 'convnextv2_base.fcmae_ft_in22k_in1k_384',
    'fast': 'efficientnet_b3.ra2_in1k',
    'fastest': 'mobilenetv3_large_100.ra_in1k',
    'semantic': 'vit_base_patch16_clip_224.openai',
    'newest': 'facebook/dinov3-vith16plus-pretrain-lvd1689m'
}

class ImageEmbedder2:
    def __init__(self, preset='balanced', device=None):
        login(new_session=False)
        model_name = MODEL_PRESETS.get(preset, preset)
        print(f"Loading model: {model_name}")
        
        # Load model without classification head
        self.model = AutoModel.from_pretrained(
            model_name
        )
        self.processor = AutoImageProcessor.from_pretrained(model_name)
        self.model.to(device)
        self.model.eval()

        
        print(f"Model loaded successfully!")
        
    def get_embedding(self, image_url):
        try:
            image = load_image(image_url)

            inputs = self.processor(images=image, return_tensors="pt").to(self.model.device)
            with torch.inference_mode():
                outputs = self.model(**inputs)

            embedding = outputs.pooler_output
            
            # Convert to numpy and flatten
            embedding = embedding.cpu().numpy().flatten()
            return embedding
        except Exception as e:
            print(f"Error processing {image_url}: {e}")
            return None