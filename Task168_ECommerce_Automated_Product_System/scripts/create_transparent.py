from pathlib import Path
import numpy as np
from PIL import Image
from PIL import ImageFilter


BASE_DIR = Path(__file__).resolve().parent.parent


# Original image
image_path = BASE_DIR / "images" / "product3.jpg"

# SAM 2 mask
mask_path = BASE_DIR / "images" / "shoe_mask.png"

# Output
output_path = BASE_DIR / "images" / "product3_transparent.png"


# Load original image
image = Image.open(image_path).convert("RGBA")


# Load mask
mask = Image.open(mask_path).convert("L")


# --------------------------------------------------
# Clean the edge of the mask
# --------------------------------------------------
# Slightly shrink the mask to remove the blue edge
mask = mask.filter(ImageFilter.MinFilter(5))

# Remove weak/partial edge pixels
mask = mask.point(lambda p: 255 if p > 128 else 0)

# Convert to NumPy AFTER filtering
image_array = np.array(image)
mask_array = np.array(mask)


# Put cleaned mask into alpha channel
image_array[:, :, 3] = mask_array


# Convert back to PIL image
transparent_image = Image.fromarray(image_array)


# Save as PNG
transparent_image.save(output_path)


print("Transparent product saved to:")
print(output_path)
transparent_image.show()