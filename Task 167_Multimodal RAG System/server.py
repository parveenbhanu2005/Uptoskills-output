from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from chromadb.utils import embedding_functions
from google import genai
import csv
from datetime import datetime
import os

# Initialize the API server
app = FastAPI()

# Allow the Next.js frontend (running on port 3000) to communicate with this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Configuration & Client Setup
API_KEY = "YOUR_API_KEY_HERE"
genai_client = genai.Client(api_key=API_KEY)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
sentence_transformer_ef = embedding_functions.DefaultEmbeddingFunction()
collection = chroma_client.get_collection(
    name="technical_manual_data",
    embedding_function=sentence_transformer_ef
)

LOG_FILE = "query_logs.csv"

# Define the format of incoming requests
class QueryRequest(BaseModel):
    query: str

@app.post("/api/chat")
def chat_endpoint(req: QueryRequest):
    user_query = req.query
    
    # 2. Query ChromaDB
    results = collection.query(query_texts=[user_query], n_results=1)
    
    retrieved_doc = results["documents"][0][0]
    metadata = results["metadatas"][0][0]
    distance = results["distances"][0][0]
    doc_id = results["ids"][0][0]
    source_ref = metadata.get("source", "Unknown")
    
    # Format the image path so Next.js can find it in the /public folder
    image_filename = "/" + os.path.basename(source_ref)
    
    # 3. Generate LLM Response
    prompt = f"""
    You are an expert technical support AI assistant. 
    A technician needs help with the following issue: "{user_query}"

    Use ONLY the retrieved technical context below to provide clear, step-by-step guidance.
    
    Technical Context:
    - Manual Source: {source_ref}
    - Details: {retrieved_doc}

    Provide concise, actionable repair instructions grounded in the context provided.
    """
    
    response = genai_client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt
    )
    
    # 4. Log the interaction
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_query, doc_id, f"{distance:.4f}", source_ref, retrieved_doc])
        
    # 5. Send the dynamic data back to the React UI
    return {
        "text": response.text,
        "image": image_filename,
        "source": source_ref,
        "distance": f"{distance:.4f}"
    }