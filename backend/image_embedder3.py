import os
import torch
from PIL import Image
from transformers.image_utils import load_image
import open_clip
import numpy as np

# All values must be valid OpenCLIP "MODEL::PRETRAINED" pairs (see https://github.com/mlfoundations/open_clip)
MODEL_PRESETS = {
    "fastest": "ViT-B-32::laion2b_e16",
    "fast": "ViT-B-32::laion2b_e16",
    "balanced": "ViT-L-14::laion2b_s32b_b82k",
    "best": "ViT-H-14::laion2B-s32B-b79K",
    "semantic": "ViT-B-16::openai",
    "nextbest": "ViT-H-14::laion2B-s32B-b79K",
    "newbest": "ViT-bigG-14::laion2B-s39B-b160K",
    # Aliases for SigLIP (optional high-quality preset)
    "siglip": "ViT-SO400M-14-SigLIP-384::webli",
    # DINOv2 is not in open_clip presets; map to a strong LAION ViT for backward compatibility
    "newest": "ViT-H-14::laion2B-s32B-b79K",
}


def _center_crop_fraction(img: Image.Image, frac: float = 0.88) -> Image.Image:
    w, h = img.size
    nw, nh = max(1, int(w * frac)), max(1, int(h * frac))
    left = max(0, (w - nw) // 2)
    top = max(0, (h - nh) // 2)
    return img.crop((left, top, left + nw, top + nh))


class ImageEmbedder3:
    def __init__(self, preset="balanced", device=None):
        preset_name = MODEL_PRESETS.get(preset, preset)
        print(f"Loading model: {preset_name}")

        if "::" not in preset_name:
            raise ValueError(
                f"MODEL_PRESET must map to 'MODEL::PRETRAINED' for OpenCLIP; got {preset_name!r}. "
                f"Known keys: {sorted(MODEL_PRESETS.keys())}"
            )

        model_name, pretrained = preset_name.split("::", 1)
        print(f"Loading OpenCLIP model: {model_name} ({pretrained})")

        dev = device if device else torch.device("cpu")
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name,
            pretrained=pretrained,
            device=dev,
        )
        self.device = dev
        self.model.to(dev)
        self.model.eval()
        self.model_key = preset_name

        self.embed_dim = self.model.visual.output_dim
        print(f"✅ Model loaded successfully — embedding dimension: {self.embed_dim}")

    def _encode_tensor(self, img_tensor: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            image_features = self.model.encode_image(img_tensor)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        return image_features

    def get_embedding(self, image_url, multi_crop: bool = False):
        """Extract normalized embedding from a single image URL."""
        use_mc = multi_crop or (
            os.getenv("EMBEDDER_MULTI_CROP", "").lower() in ("1", "true", "yes")
        )
        try:
            img = load_image(image_url)
            if not isinstance(img, Image.Image):
                img = Image.fromarray(np.array(img))

            tensors = [self.preprocess(img).unsqueeze(0).to(self.device)]
            if use_mc:
                cropped = _center_crop_fraction(img.convert("RGB"), 0.88)
                tensors.append(self.preprocess(cropped).unsqueeze(0).to(self.device))

            feats = [self._encode_tensor(t) for t in tensors]
            combined = torch.mean(torch.cat(feats, dim=0), dim=0, keepdim=True)
            combined = combined / combined.norm(dim=-1, keepdim=True)
            return combined.cpu().numpy().flatten()

        except Exception as e:
            print(f"❌ Error processing {image_url}: {e}")
            return None
