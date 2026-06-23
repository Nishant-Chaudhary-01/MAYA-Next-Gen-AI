import google.generativeai as genai
import os
import chromadb
# ChromaDB ka local embedding engine use karne ke liye import
from chromadb.utils import embedding_functions

# 1. Gemini API Key Configuration (Abhi is file me embedding ke liye zaroorat nahi hai, par Maya ke baaki kamo ke liye configured rahega)
GOOGLE_API_KEY = "AQ.Ab8RN6Kh9PMPFD0LimYzBSZZnib7poFPU_yR1Gs7p0ddS1zfbA"
genai.configure(api_key=GOOGLE_API_KEY)

# Yeh line current file (maya_rag.py) ki location se absolute root path nikalegi
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Data", "maya_vector_db")

# Ab client ko exact system location ka path milega
chroma_client = chromadb.PersistentClient(path=DATA_DIR)

# Default local embedding (All-MiniLM-L6-v2 = 73 mb) function initialize karein (No Gemini API hits for embedding)
default_ef = embedding_functions.DefaultEmbeddingFunction()

# Ek collection (table jaisa) banate hain search results cache karne ke liye
# `embedding_function=default_ef` dene se Chroma khud text ko vector me convert karega
collection = chroma_client.get_or_create_collection(
    name="web_search_cache", 
    metadata={"hnsw:space": "cosine"},
    embedding_function=default_ef
)

# 2. Function: Web Search ka result database me save karna
def save_search_to_cache(query: str, search_result: str):
    # Id ke liye hum query ko hi use kar rahe hain taaki easily check ho sake aur duplicate na ho
    collection.add(
        documents=[search_result],          # Actual text info jo future me use hogi
        metadatas=[{"original_query": query}], # Extra tracking info
        ids=[query]                         # Unique ID ki jagah query string khud kaam karegi
    )
    print(f"✅ Cache Saved for query: '{query}'")

# 3. Function: Pehle se save data ko query karna (Similarity Search)
def search_cache(user_query: str):
    # query_texts dene par ChromaDB local embedding use karke search karega
    results = collection.query(
        query_texts=[user_query],
        n_results=1 # Sabse top ka best 1 result chahiye
    )
    
    # Agar koi match mila aur uski distance kam hai (matlab match strong hai)
    if results['documents'] and len(results['documents'][0]) > 0:
        distance = results['distances'][0][0]
        if distance < 0.5: # 0.3 se kam matlab bohot similar query hai
            return results['documents'][0][0]
            
    return None

# ---- CHALU KARKE DEKHTE HAIN (TESTING) ----
if __name__ == "__main__":
    # Simulate: User ne pehli baar poocha aur humne web search ka result cache kiya
    print("--- Scenario 1: First time query (Saving to DB) ---")
    web_data = "Trending update: Python 3.12 has introduced new syntaxes for generic types and isolated subinterpreters."
    save_search_to_cache(
        query="What are the new features in Python 3.12?", 
        search_result=web_data
    )
    
    print("\n--- Scenario 2: Similar query asked later (Retrieving from DB) ---")
    # User ne thoda ghuma ke poocha: "Tell me about python 3.12 updates"
    test_query = "Tell me about python 3.12 updates"
    cached_response = search_cache(test_query)
    
    if cached_response:
        print(f"🚀 Found in Local ChromaDB! Bypassing API Hit.\nResult: {cached_response}")
    else:
        print("❌ Not found in cache. Need to hit APIs.")