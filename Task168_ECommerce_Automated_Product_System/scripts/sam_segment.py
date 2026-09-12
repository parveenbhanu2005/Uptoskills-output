from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

# --------------------------------------------------
# 1. Find project directory
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------
# 2. File paths
# --------------------------------------------------

image_path = BASE_DIR / "images" / "product3.jpg"

checkpoint = BASE_DIR / "checkpoints" / "sam2_hiera_small.pt"


model_cfg = (
    BASE_DIR
    / "sam2"
    / "sam2"
    / "configs"
    / "sam2"
    / "sam2_hiera_s.yaml"
)
# The sam2_hiera_s.yaml file is the architectural blueprint that tells Python exactly how to build the "Small" version of the SAM 2 model before it loads any learned knowledge


# --------------------------------------------------
# 3. Select CPU or GPU
# --------------------------------------------------

device = "cuda" if torch.cuda.is_available() else "cpu"

print("Using device:", device)


print("Loading SAM 2...")

sam2_model = build_sam2(
    str(model_cfg),
    str(checkpoint),
    device=device
) #it expects data in very specific tensor formats
predictor = SAM2ImagePredictor(sam2_model)
# The raw sam2_model doesn't know how to handle images, resize them, or accept mouse clicks easily. The SAM2ImagePredictor class adds these missing features.
# Key Capabilities Added:
# set_image(): Automatically resizes and normalizes your photo so the model can read it.
# predict(): Accepts simple inputs like your bounding box points ([x1, y1, x2, y2]) and converts them into the complex mathematical format the raw model needs.
# Output Handling: It cleans up the result, giving you a simple mask array instead of raw tensor data.

print("SAM 2 loaded!")


image = np.array(Image.open(image_path).convert("RGB"))

print("Image shape:", image.shape)

predictor.set_image(image)

print("Image loaded into SAM 2!")
# --------------------------------------------------
# 7. Define bounding box
# --------------------------------------------------

from get_box import get_product_box

box = np.array(get_product_box())

print("Selected bounding box:", box)
masks, scores, logits = predictor.predict(
    box=box,
    multimask_output=True
) #please give me a mask for this box,confidence score for each mask


# --------------------------------------------------
# 9. Select the best mask
# --------------------------------------------------

best_index = np.argmax(scores)

best_mask = masks[best_index]

print("Mask shape:", best_mask.shape)
print("Score:", scores[best_index])

mask = (best_mask * 255).astype(np.uint8)

mask_image = Image.fromarray(mask)

output_path = BASE_DIR / "images" / "shoe_mask.png"

mask_image.save(output_path)

print("Mask saved to:", output_path)
mask_image.show()