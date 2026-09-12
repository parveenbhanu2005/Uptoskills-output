import fitz  # PyMuPDF
import os

# File paths
PDF_PATH = "data/manual.pdf"
IMAGE_DIR = "data/extracted_images"

def extract_content(pdf_path):
    # Create the directory for images if it doesn't exist
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    # Open the PDF
    doc = fitz.open(pdf_path)
    print(f"Successfully opened: {pdf_path} (Total Pages: {len(doc)})\n")

    # Let's just process the first 90 pages for our initial test
    for page_num in range(min(90, len(doc))):
        page = doc[page_num]
        
        # 1. Extract Text
        text = page.get_text()
        if text.strip():
            print(f"--- Page {page_num + 1} Text Snippet ---")
            print(text[:150].strip() + "...\n") # Print just the first 150 characters

        # 2. Extract Images (Diagrams, exploded views)
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0] # The internal reference number for the image
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            # Save the image to our folder
            image_filename = f"{IMAGE_DIR}/page_{page_num + 1}_diagram_{img_index}.{image_ext}"
            with open(image_filename, "wb") as image_file:
                image_file.write(image_bytes)
            print(f"[+] Saved diagram: {image_filename}")

if __name__ == "__main__":
    extract_content(PDF_PATH)