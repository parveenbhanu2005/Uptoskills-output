from pathlib import Path
import json
import csv

from check_compliance import check_image_compliance


# --------------------------------------------------
# 1. Project directory
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------
# 2. Product configuration
# --------------------------------------------------

PRODUCTS = [
    {
        "id": "P001",
        "metadata": "product_metadata.json",
        "studio": "studio_product.png",
        "image_800": "product_800x800.jpg",
        "image_600": "product_600x600.jpg",
        "image_400": "product_400x400.jpg"
    },

    {
        "id": "P002",
        "metadata": "shoe_metadata.json",
        "studio": "shoe_studio.png",
        "image_800": "shoe_800x800.jpg",
        "image_600": "shoe_600x600.jpg",
        "image_400": "shoe_400x400.jpg"
    }
]


# --------------------------------------------------
# 3. CSV path
# --------------------------------------------------

csv_path = BASE_DIR / "product_catalog.csv"


# --------------------------------------------------
# 4. CSV columns
# --------------------------------------------------

fieldnames = [
    "Product ID",
    "Category",
    "Color",
    "Material",
    "Pattern",
    "Title",
    "Tags",
    "Compliance",
    "Studio Image",
    "800x800",
    "600x600",
    "400x400"
]


# --------------------------------------------------
# 5. Create product records
# --------------------------------------------------

products = []


for item in PRODUCTS:

    metadata_path = BASE_DIR / "images" / item["metadata"]

    # Load metadata
    with open(metadata_path, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    # Studio image path
    studio_path = BASE_DIR / "images" / item["studio"]

    # Check compliance
    compliance_status = check_image_compliance(studio_path)

    # Create product record
    product = {
        "Product ID": item["id"],
        "Category": metadata["category"],
        "Color": metadata["color"],
        "Material": metadata["material"],
        "Pattern": metadata["pattern"],
        "Title": metadata["title"],
        "Tags": ", ".join(metadata["tags"]),
        "Compliance": compliance_status,
        "Studio Image": f"images/{item['studio']}",
        "800x800": f"images/resized/{item['image_800']}",
        "600x600": f"images/resized/{item['image_600']}",
        "400x400": f"images/resized/{item['image_400']}"
    }

    products.append(product)


# --------------------------------------------------
# 6. Save CSV
# --------------------------------------------------

with open(
    csv_path,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(products)


print("Product catalog created successfully!")
print(csv_path)

print("\nProducts added:")

for product in products:
    print(
        product["Product ID"],
        "-",
        product["Title"],
        "-",
        product["Compliance"]
    )