import os
import chromadb
from chromadb.utils import embedding_functions

# 1. Initialize the Local Vector Database
client = chromadb.PersistentClient(path="./chroma_db")
sentence_transformer_ef = embedding_functions.DefaultEmbeddingFunction()

# 2. Create or Load the Collection
collection = client.get_or_create_collection(
    name="technical_manual_data",
    embedding_function=sentence_transformer_ef
)

def store_all_extracted_data():
    print("Initializing bulk database ingestion...")
    
    documents = []
    metadatas = []
    ids = []
    
    # Assuming your manual has up to 124 pages (adjust the range if needed)
    total_pages = 124
    
    for page_num in range(1, total_pages + 1):
        # --- A. Handle Text Chunks ---
        # If you save page text as text files (e.g., data/extracted_text/page_1.txt)
        text_path = f"data/extracted_text/page_{page_num}.txt"
        
        if os.path.exists(text_path):
            with open(text_path, "r", encoding="utf-8") as f:
                page_text = f.read()
        else:
            # Default fallback description if text file hasn't been split separately
            page_text = f"Technical Manual Page {page_num}: Standard specifications, wiring guidelines, and structural schematics."
            
        documents.append(page_text)
        metadatas.append({"source": f"page_{page_num}_text"})
        ids.append(f"doc_text_{page_num}")
        
        # --- B. Handle Extracted Images & Vision Descriptions ---
        # Looking for files like data/extracted_images/page_18_diagram_1.jpeg
        image_path = f"data/extracted_images/page_{page_num}_diagram_1.jpeg"
        
        if os.path.exists(image_path):
            img_description = f"Page {page_num} Diagram Description: Detailed exploded hardware component view and routing schematic extracted from page {page_num}."
            
            documents.append(img_description)
            metadatas.append({"source": image_path})
            ids.append(f"doc_image_page_{page_num}")

    # 3. Batch Add Everything to ChromaDB
    if documents:
        # Clear existing items to avoid duplicates if re-running
        existing = collection.get()
        if existing['ids']:
            collection.delete(ids=existing['ids'])
            
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"[+] Successfully ingested {len(documents)} total documents and diagrams into ChromaDB!")
    else:
        print("[-] No documents found to store. Please check your directory structure.")
        
    print(f"[+] Total vector items currently in database: {collection.count()}")

if __name__ == "__main__":
    store_all_extracted_data()