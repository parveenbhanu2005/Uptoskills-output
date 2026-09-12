from pathlib import Path
from PIL import Image


BASE_DIR = Path(__file__).resolve().parent.parent

product_path = BASE_DIR / "images" / "product3_transparent.png"
output_path = BASE_DIR / "images" / "shoe_studio.png"


# --------------------------------------------------
# 1. Load transparent product
# --------------------------------------------------

product = Image.open(product_path).convert("RGBA")

print("Original image size:", product.size)


# --------------------------------------------------
# 2. Find the bounding box of the visible product
# --------------------------------------------------

bbox = product.getbbox()

print("Product bounding box:", bbox)


# --------------------------------------------------
# 3. Crop away transparent space
# --------------------------------------------------

product = product.crop(bbox)

print("Cropped product size:", product.size)


# --------------------------------------------------
# 4. Create studio background
# --------------------------------------------------

canvas_width = 800
canvas_height = 800

background = Image.new(
    "RGBA",
    (canvas_width, canvas_height),
    (245, 245, 245, 255)
)


# --------------------------------------------------
# 5. Resize product
# --------------------------------------------------

target_height = 500

scale = target_height / product.height

new_width = int(product.width * scale)
new_height = int(product.height * scale)

product = product.resize(
    (new_width, new_height),
    Image.Resampling.LANCZOS
)

print("Resized product:", product.size)

# --------------------------------------------------
# 6. Center product
# --------------------------------------------------

x = (canvas_width - product.width) // 2
y = (canvas_height - product.height) // 2


# --------------------------------------------------
# 7. Place product on background
# --------------------------------------------------

background.alpha_composite(
    product,
    (x, y)
)


# --------------------------------------------------
# 8. Save final image
# --------------------------------------------------

background.convert("RGB").save(output_path)

print("Studio image saved to:")
print(output_path)