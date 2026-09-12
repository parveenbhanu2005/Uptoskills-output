import os
import csv
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions
from google import genai

# 1. Configuration & Client Setup
API_KEY = "YOUR_API_KEY_HERE"  # Ensure your valid Gemini API key is here
genai_client = genai.Client(api_key=API_KEY)

# Connect to local ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
sentence_transformer_ef = embedding_functions.DefaultEmbeddingFunction()
collection = chroma_client.get_collection(
    name="technical_manual_data",
    embedding_function=sentence_transformer_ef
)

LOG_FILE = "query_logs.csv"

def init_logger():
    """Ensure CSV log file exists with proper headers."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Timestamp", 
                "User_Query", 
                "Retrieved_Doc_ID", 
                "Similarity_Distance", 
                "Source_Reference", 
                "Retrieved_Context"
            ])

def log_interaction(query, doc_id, distance, source, context):
    """Save query details, similarity scores, and sources to a CSV log."""
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            query,
            doc_id,
            f"{distance:.4f}",
            source,
            context
        ])

def run_multimodal_rag(user_query):
    print(f"\n[?] User Query: '{user_query}'")
    
    # 2. Query ChromaDB for relevant text & image descriptions
    results = collection.query(
        query_texts=[user_query],
        n_results=1
    )
    
    # Extract retrieved data
    retrieved_doc = results["documents"][0][0]
    metadata = results["metadatas"][0][0]
    distance = results["distances"][0][0]
    doc_id = results["ids"][0][0]
    source_ref = metadata.get("source", "Unknown")

    print("\n--- ChromaDB Search Results ---")
    print(f"[+] Matched Doc ID : {doc_id}")
    print(f"[+] Distance Score : {distance:.4f}")
    print(f"[+] Source Manual   : {source_ref}")
    print(f"[+] Extracted Text  : {retrieved_doc}")

    # 3. Log the retrieval metrics
    init_logger()
    log_interaction(user_query, doc_id, distance, source_ref, retrieved_doc)
    print(f"[+] Query metrics logged to '{LOG_FILE}'")

    # 4. Generate grounded troubleshooting response via LLM
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

    print("\n--- Generated Technician Guidance ---")
    print(response.text)

if __name__ == "__main__":
    # Test query specifically targetting the hinge & display cable data stored from page 18
    test_query = "How do I align or troubleshoot the display cable and hinge assembly?"
    run_multimodal_rag(test_query)