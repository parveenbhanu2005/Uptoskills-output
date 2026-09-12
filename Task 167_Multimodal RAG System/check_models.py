from google import genai

# Paste your API key here
client = genai.Client(api_key="YOUR_API_KEY_HERE")

print("Available Models for your API Key:")
for model_info in client.models.list():
    # We only want models that support generating content
    if "generateContent" in model_info.supported_actions:
        print(model_info.name)