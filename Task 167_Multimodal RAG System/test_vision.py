from google import genai
import PIL.Image
import os

# 1. Setup your API Key using the new Client
API_KEY = "YOUR_API_KEY_HERE"
client = genai.Client(api_key=API_KEY)

def test_diagram_analysis():
    # Target one of the images you just extracted
    # IMPORTANT: Check your 'data/extracted_images' folder and update this filename if needed!
    # Update this to a real diagram from your folder!
    image_path = "data/extracted_images/page_18_diagram_1.jpeg" 
    
    if not os.path.exists(image_path):
        print(f"Error: Could not find {image_path}. Please check the filename.")
        return

    print("Loading image and connecting to Gemini via new SDK...")
    img = PIL.Image.open(image_path)
    
    # 2. Prompt the AI to act as a technical extraction tool
    prompt = """
    You are an expert hardware technician. Analyze this image from a technical manual.
    If it is a circuit diagram, exploded view, or hardware schematic, describe every visible component, 
    label, and connection in extreme detail so that it can be searched in a database.
    If it is just a company logo or irrelevant icon, reply with 'IRRELEVANT_IMAGE'.
    """
    
    # 3. Use the updated syntax to generate content
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=[img, prompt]
    )
    
    print("\n--- AI Image Analysis ---")
    print(response.text)

if __name__ == "__main__":
    test_diagram_analysis()