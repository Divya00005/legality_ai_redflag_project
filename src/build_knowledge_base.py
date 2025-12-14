import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os

# 1. SETUP PATHS
RISKY_FILE = 'data/processed/risky_clauses_clean.json'
SAFE_FILE = 'data/processed/step2_final_variations.json'
DB_PATH = "data/chroma_db"  # Where the database will be saved on disk

def main():
    print("🚀 Building Knowledge Base (Vector Database)...")

    # 2. LOAD DATA
    if not os.path.exists(RISKY_FILE) or not os.path.exists(SAFE_FILE):
        print("❌ Error: Input files not found. Check data/processed/")
        return

    df_risky = pd.read_json(RISKY_FILE)
    df_safe = pd.read_json(SAFE_FILE)

    print(f"   📄 Loaded {len(df_risky)} risky clauses.")
    print(f"   📄 Loaded {len(df_safe)} safe solutions.")

    # 3. INITIALIZE DATABASE
    # We use a persistent client so data is saved to disk
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # We use a standard, free embedding model (Sentence Transformers)
    # This converts text -> numbers
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # Delete collection if it exists (so we start fresh)
    try:
        client.delete_collection(name="legal_risks")
    except:
        pass

    collection = client.create_collection(
        name="legal_risks",
        embedding_function=sentence_transformer_ef
    )

    # 4. MERGE & INDEX
    # We map Safe Clauses to Risky Clauses using the 'id' (or index)
    
    # Create a dictionary for fast lookup of safe answers: {id: safe_text}
    safe_lookup = {}
    for _, row in df_safe.iterrows():
        # Prefer the generated variations, fallback to base
        best_safe = row.get('safe_option_1', row.get('safe_clause_base', ''))
        safe_lookup[row['id']] = best_safe

    documents = [] # The Risky Text (What we search for)
    metadatas = [] # The Info we want back (The Safe Rewrite + Category)
    ids = []       # Unique IDs

    print("   ...Indexing data...")
    
    count = 0
    for index, row in df_risky.iterrows():
        # If we have a safe answer for this risky clause
        row_id = row.get('id', index) # Use ID column if exists, else index
        
        if row_id in safe_lookup:
            risky_text = row['risky_clause']
            category = row.get('risk_category', 'General')
            safe_text = safe_lookup[row_id]

            documents.append(risky_text)
            metadatas.append({
                "category": category,
                "safe_rewrite": safe_text,
                "risk_id": str(row_id)
            })
            ids.append(str(row_id))
            count += 1

    # 5. SAVE TO DB
    # Add in batches to be safe
    batch_size = 50
    for i in range(0, len(documents), batch_size):
        collection.add(
            documents=documents[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
        print(f"   ✅ Indexed batch {i} - {i+batch_size}")

    print(f"\n🎉 SUCCESS! Knowledge Base built with {count} entries.")
    print(f"📁 Database saved to: {DB_PATH}")

if __name__ == "__main__":
    main()