from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt


def get_product_box():

    BASE_DIR = Path(__file__).resolve().parent.parent

    image_path = BASE_DIR / "images" / "product3.jpg"

    image = Image.open(image_path)

    plt.imshow(image)
    plt.title("Click TOP-LEFT and BOTTOM-RIGHT of the product")
    plt.axis("on")

    points = plt.ginput(2, timeout=0)

    plt.close()

    x1 = points[0][0]
    y1 = points[0][1]

    x2 = points[1][0]
    y2 = points[1][1]

    print("Top-left:", (x1, y1))
    print("Bottom-right:", (x2, y2))

    box = [x1, y1, x2, y2]

    return box