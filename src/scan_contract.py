import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
import os

# CONFIGURATION
DB_PATH = "data/chroma_db"
INPUT_PDF = "data/test_files/risky_contract.pdf"
DISTANCE_THRESHOLD = 0.35

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def split_into_clauses(text):
    clauses = [line.strip() for line in text.split('\n') if len(line.strip()) > 30]
    return clauses

def main():
    print(f"🚀 Scanning Contract: {INPUT_PDF}...\n")
    
    # 1. CONNECT TO DATABASE
    client = chromadb.PersistentClient(path=DB_PATH)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = client.get_collection(name="legal_risks", embedding_function=sentence_transformer_ef)

    if not os.path.exists(INPUT_PDF):
        print("❌ PDF not found.")
        return
    
    full_text = extract_text_from_pdf(INPUT_PDF)
    clauses = split_into_clauses(full_text)
    
    print(f"📄 Analyzing {len(clauses)} clauses for Golden Standard deviations...")
    print("-" * 60)

    risks_found = 0
    
    for i, clause in enumerate(clauses):
        results = collection.query(
            query_texts=[clause],
            n_results=1,
            include=["metadatas", "distances"]
        )
        
        distance = results['distances'][0][0]
        metadata = results['metadatas'][0][0]
        
        # MATHEMATICAL LOGIC:
        # If the clause is very close to a "Risky Clause", it has a High Deviation from the Standard.
        # Deviation % = Similarity to Risk %
        deviation_score = (1 - distance) * 100
        
        if distance < DISTANCE_THRESHOLD:
            risks_found += 1
            print(f"🚩 [RISK DETECTED]")
            # 🔴 EXACT OUTPUT FORMAT REQUESTED
            print(f"   📈 DEVIATION FROM GOLDEN STANDARD: {deviation_score:.2f}%")
            print(f"   🔻 RISKY CLAUSE: \"{clause}\"")
            print(f"   ⚠️ CATEGORY:     {metadata['category']}")
            print(f"   🛡️ GOLDEN STD:   \"{metadata['safe_rewrite'][:100]}...\"")
            print("-" * 60)

    if risks_found == 0:
        print("✅ Contract aligns with Golden Standard. No deviations detected.")
    else:
        print(f"🚨 Scan Complete. Found {risks_found} deviations from the Golden Standard.")

if __name__ == "__main__":
    main()