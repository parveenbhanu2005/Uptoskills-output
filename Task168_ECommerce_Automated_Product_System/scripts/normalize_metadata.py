# --------------------------------------------------
# Normalize product metadata
# --------------------------------------------------

def normalize_text(value):
    """
    Remove unnecessary spaces and punctuation.
    """

    value = value.strip()
    value = value.rstrip(".,!?")

    return value

def normalize_category(value):
    value = normalize_text(value)
    value_lower = value.lower()

    categories = {
        "headphone": "Headphones",
        "earphone": "Earphones",
        "earbud": "Earbuds",
        "shoe": "Shoes",
        "sneaker": "Sneakers",
        "shirt": "Shirt",
        "t-shirt": "T-Shirt",
        "tshirt": "T-Shirt",
        "jeans": "Jeans",
        "watch": "Watch",
        "bag": "Bag",
        "backpack": "Backpack",
        "bottle": "Bottle",
        "camera": "Camera",
        "laptop": "Laptop",
        "phone": "Smartphone",
        "smartphone": "Smartphone",
        "tablet": "Tablet",
        "keyboard": "Keyboard",
        "mouse": "Mouse",
        "book": "Book",
        "glasses": "Glasses",
        "sunglasses": "Sunglasses"
    }

    for keyword, standard_category in categories.items():
        if keyword in value_lower:
            return standard_category

    # If it is an unknown product, keep the VLM's answer
    return value

def normalize_color(value):
    value = normalize_text(value)

    value_lower = value.lower()

    colors = {
        "black": "Black",
        "white": "White",
        "red": "Red",
        "blue": "Blue",
        "green": "Green",
        "yellow": "Yellow",
        "gray": "Gray",
        "grey": "Gray",
        "brown": "Brown",
        "orange": "Orange",
        "purple": "Purple",
        "pink": "Pink"
    }

    for color, standard_color in colors.items():

        if color in value_lower:
            return standard_color

    return value


def normalize_pattern(value):
    value = normalize_text(value)

    value_lower = value.lower()

    if (
        "no pattern" in value_lower
        or "plain" in value_lower
        or value_lower == "none"
        or value_lower == "no"
    ):
        return "Plain"

    return value


# --------------------------------------------------
# Test
# --------------------------------------------------

category = "Headphones."
color = "Black."
material = "Rubber."
pattern = "No pattern."

print("Before normalization:")
print(category)
print(color)
print(material)
print(pattern)


category = normalize_category(category)
color = normalize_color(color)
material = normalize_text(material)
pattern = normalize_pattern(pattern)


print("\nAfter normalization:")
print(category)
print(color)
print(material)
print(pattern)