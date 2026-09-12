import cv2
import os

INPUT = "input/sample.png"
OUTPUT = "input/tampered_sample.png"

image = cv2.imread(INPUT)

if image is None:
    print("ERROR: Could not load input image.")
    raise SystemExit(1)

# Create a controlled modification:
# Add a small white rectangle over part of the document
# and write replacement text over that region.
h, w = image.shape[:2]

x1 = int(w * 0.45)
y1 = int(h * 0.30)
x2 = int(w * 0.70)
y2 = int(h * 0.37)

# Cover the original area
cv2.rectangle(
    image,
    (x1, y1),
    (x2, y2),
    (255, 255, 255),
    -1
)

# Add replacement text
cv2.putText(
    image,
    "MODIFIED",
    (x1 + 10, y1 + 35),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.9,
    (0, 0, 0),
    2,
    cv2.LINE_AA
)

cv2.imwrite(OUTPUT, image)

print("Tampered test image created successfully.")
print(f"Output: {OUTPUT}")