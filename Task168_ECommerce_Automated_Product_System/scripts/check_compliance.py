from pathlib import Path
from PIL import Image
import numpy as np


# --------------------------------------------------
# 1. Project directory
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

studio_path = BASE_DIR / "images" / "shoe_studio.png"


# --------------------------------------------------
# 2. Load image
# --------------------------------------------------

image = Image.open(studio_path).convert("RGB")
image_array = np.array(image)

width, height = image.size

print("Image size:", image.size)


# --------------------------------------------------
# 3. Check image resolution
# --------------------------------------------------

resolution_pass = width >= 800 and height >= 800

print("\nResolution check:")
print("PASS" if resolution_pass else "FAIL")


# --------------------------------------------------
# 4. Check background
# --------------------------------------------------

# Since our studio background is light gray/white,
# calculate how many pixels are close to white.

background_pixels = np.all(image_array > 230, axis=2)

background_ratio = np.mean(background_pixels)

background_pass = background_ratio >= 0.70

print("\nBackground check:")
print(f"Light background ratio: {background_ratio:.2%}")
print("PASS" if background_pass else "FAIL")


# --------------------------------------------------
# 5. Find product region
# --------------------------------------------------

# Pixels that are significantly darker than the
# light studio background are considered product pixels.

product_pixels = np.any(image_array < 210, axis=2)

ys, xs = np.where(product_pixels)


if len(xs) > 0:

    x_min = xs.min()
    x_max = xs.max()
    y_min = ys.min()
    y_max = ys.max()

    product_width = x_max - x_min
    product_height = y_max - y_min

    print("\nProduct bounding box:")
    print(
        f"x={x_min}, y={y_min}, "
        f"width={product_width}, height={product_height}"
    )

else:

    product_width = 0
    product_height = 0

    print("\nProduct bounding box:")
    print("No product detected")


# --------------------------------------------------
# 6. Check product size
# --------------------------------------------------

if product_width > 0 and product_height > 0:

    product_area_ratio = (
        product_width * product_height
    ) / (width * height)

else:

    product_area_ratio = 0


size_pass = 0.05 <= product_area_ratio <= 0.80

print("\nProduct size check:")
print(f"Product area ratio: {product_area_ratio:.2%}")
print("PASS" if size_pass else "FAIL")


# --------------------------------------------------
# 7. Check product position
# --------------------------------------------------

if product_width > 0 and product_height > 0:

    product_center_x = (x_min + x_max) / 2
    product_center_y = (y_min + y_max) / 2

    image_center_x = width / 2
    image_center_y = height / 2

    center_x_difference = abs(
        product_center_x - image_center_x
    ) / width

    center_y_difference = abs(
        product_center_y - image_center_y
    ) / height

    centered_pass = (
        center_x_difference <= 0.20
        and center_y_difference <= 0.20
    )

else:

    centered_pass = False


print("\nProduct position check:")
print("PASS" if centered_pass else "FAIL")

# --------------------------------------------------
# 8. Overall compliance
# --------------------------------------------------

compliant = (
    resolution_pass
    and background_pass
    and size_pass
    and centered_pass
)


print("\n==============================")
print("COMPLIANCE RESULT")
print("==============================")


if compliant:
    compliance_status = "COMPLIANT"
else:
    compliance_status = "NOT COMPLIANT"


print("Status:", compliance_status)


# --------------------------------------------------
# Function for other scripts
# --------------------------------------------------

def check_image_compliance(studio_path):
    return compliance_status