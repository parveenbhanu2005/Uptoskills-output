from pathlib import Path
from PIL import Image


# --------------------------------------------------
# 1. Project directory
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------
# 2. Input image
# --------------------------------------------------

input_path = BASE_DIR / "images" / "shoe_studio.png"


# --------------------------------------------------
# 3. Output directory
# --------------------------------------------------

output_dir = BASE_DIR / "images" / "resized"

output_dir.mkdir(exist_ok=True)


# --------------------------------------------------
# 4. Load image
# --------------------------------------------------

image = Image.open(input_path).convert("RGB")

print("Original image:", image.size)


# --------------------------------------------------
# 5. Create required resolutions
# --------------------------------------------------

sizes = [800, 600, 400]

for size in sizes:

    resized_image = image.resize(
        (size, size),
        Image.Resampling.LANCZOS
    )

    output_path = output_dir / f"product_{size}x{size}.jpg"

    resized_image.save(
        output_path,
        quality=95
    )

    print(f"Created: {output_path}")


print("\nAll resolutions created successfully!")