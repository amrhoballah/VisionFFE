from transformers import AutoProcessor, AutoModelForCausalLM  
import requests
from io import BytesIO
from PIL import Image
import copy
import torch

MODEL_PRESETS = {
    'best': 'convnextv2_huge.fcmae_ft_in22k_in1k_384',
    'balanced': 'convnextv2_base.fcmae_ft_in22k_in1k_384',
    'fast': 'efficientnet_b3.ra2_in1k',
    'fastest': 'mobilenetv3_small_075.lamb_in1k',
    'semantic': 'microsoft/Florence-2-large',
    'newest': 'facebook/dinov3-vith16plus-pretrain-lvd1689m',
    'nextbest': 'ViT-H-14::laion2B-s32B-b79K',
    'newbest': 'ViT-bigG-14::laion2B-s39B-b160K'
}

class ImageEmbedder2:
    def __init__(self, preset='semantic', device=None):
        # Custom model string in format "MODEL::PRETRAINED"
        model_id = MODEL_PRESETS.get(preset, "semantic")
        print(f"Loading model: {model_id}")

        model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, torch_dtype='auto').eval().cuda()
        processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

        # --- Load model & preprocessing ---
        self.model = model
        self.processor = processor

        # --- Get embedding dimension ---
        print(f"✅ Model loaded successfully")
    
    def get_embedding(self, image_url):
        """Extract normalized embedding from a single image"""
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content)).convert("RGB")
            inputs = self.processor(text="<MORE_DETAILED_CAPTION>", images=image, return_tensors="pt").to('cuda', torch.float16)
            generated_ids = self.model.generate(
                input_ids=inputs["input_ids"].cuda(),
                pixel_values=inputs["pixel_values"].cuda(),
                max_new_tokens=1024,
                early_stopping=False,
                do_sample=False,
                num_beams=3
            )
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
            
            return generated_text.replace('</s>', '').replace('<s>', '').strip()

        except Exception as e:
            print(f"❌ Error processing {image_url}: {e}")
            return None