from pathlib import Path
import json


from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText


# --------------------------------------------------
# 1. Project directory
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------
# 2. Image path
# --------------------------------------------------

image_path = BASE_DIR / "images" / "shoe_studio.png"


# --------------------------------------------------
# 3. Load VLM
# --------------------------------------------------

model_id = "HuggingFaceTB/SmolVLM-500M-Instruct"

print("Loading processor...")
processor = AutoProcessor.from_pretrained(model_id)

print("Loading model...")
model = AutoModelForImageTextToText.from_pretrained(model_id)

print("VLM loaded!")


# --------------------------------------------------
# 4. Load image
# --------------------------------------------------

image = Image.open(image_path).convert("RGB")

print("Image loaded:", image.size)


# --------------------------------------------------
# 5. Function to ask the VLM
# --------------------------------------------------

def ask_vlm(question):

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image"
                },
                {
                    "type": "text",
                    "text": question
                }
            ]
        }
    ]

    prompt = processor.apply_chat_template(
        messages,
        add_generation_prompt=True
    )

    inputs = processor(
        text=prompt,
        images=[image],
        return_tensors="pt"
    )

    generated_ids = model.generate(
       **inputs,
      max_new_tokens=50
)

    # Remove the input tokens.
    input_length = inputs["input_ids"].shape[1]

    generated_only = generated_ids[:, input_length:]

    answer = processor.batch_decode(
        generated_only,
        skip_special_tokens=True
        )[0]

    return  answer.strip()


# --------------------------------------------------
# 6. Ask product attribute questions
# --------------------------------------------------

print("\nAnalyzing product...\n")


category = ask_vlm(
    "Identify the exact product shown in the image. "
    "For example, answer Headphones, Shoes, Shirt, Watch, Bag, or Bottle. "
    "Answer with only the product name."
)

print("CATEGORY:")
print(category)


color = ask_vlm(
    "What is the primary color of the product? Answer briefly."
)

print("\nCOLOR:")
print(color)


material = ask_vlm(
    "What material does the product appear to be made of? Answer briefly."
)

print("\nMATERIAL:")
print(material)


pattern = ask_vlm(
    "Describe the visible surface pattern of the product. "
    "If there is no obvious pattern, answer exactly Plain. "
    "Answer with only the pattern."
)



print("\nPATTERN:")
print(pattern)
# --------------------------------------------------
# Generate title and tags from detected attributes
# --------------------------------------------------

# Remove unnecessary punctuation
clean_category = category.strip().rstrip(".,!?")
clean_color = color.strip().rstrip(".,!?")
clean_material = material.strip().rstrip(".,!?")
clean_pattern = pattern.strip().rstrip(".,!?")


# Product title
title = f"{clean_color} {clean_category}"


# Product tags
tags = [
    clean_category.lower(),
    clean_color.lower(),
    clean_material.lower()
]

if clean_pattern.lower() not in ["plain", "no pattern", "none"]:
    tags.append(clean_pattern.lower())

tags.extend([
    "product",
    "ecommerce"
])


# Remove duplicate tags
tags = list(dict.fromkeys(tags))


print("\nTITLE:")
print(title)

print("\nTAGS:")
print(", ".join(tags))

product_metadata = {
    "category": clean_category,
    "color": clean_color,
    "material": clean_material,
    "pattern": "Plain" if clean_pattern.lower() == "no pattern" else clean_pattern,
    "title": title,
    "tags": tags
}
print("\nProduct Metadata:")
print(product_metadata)

# --------------------------------------------------
# Save metadata as JSON
# --------------------------------------------------

metadata_path = BASE_DIR / "images" / "shoe_metadata.json"

with open(metadata_path, "w", encoding="utf-8") as file:
    json.dump(
        product_metadata,
        file,
        indent=4
    )

print("\nMetadata saved to:")
print(metadata_path)