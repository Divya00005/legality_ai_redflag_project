import json
import pandas as pd
import os

# CONFIGURATION
INPUT_FILE = 'data/raw/train.json' 
OUTPUT_FILE = 'data/processed/risky_clauses.json'

# ALL POSSIBLE KEYS to find the most data
TARGET_KEYS = {
    "nda-11": "Non-Compete", # Non-Compete
    "nda-12": "Non-Compete", # Non-Solicit (Employees) - Treated as Risky
    "nda-13": "Non-Compete", # Non-Solicit (Clients) - Treated as Risky
    "nda-15": "Non-Compete"  # The key that gave you data before!
}

def extract_nli_data():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found.")
        return

    print(f"⏳ Reading {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")
        return

    new_rows = []
    print("🔍 Scanning ContractNLI (All Keys)...")

    for doc in data['documents']:
        doc_text = doc['text']
        if not doc.get('annotation_sets'): continue
        annotations = doc['annotation_sets'][0]['annotations']
        
        for key, info in annotations.items():
            # Check if this is one of our target keys AND it exists (Entailment)
            if key in TARGET_KEYS and info['choice'] == "Entailment":
                raw_spans = info['spans']
                if not raw_spans: continue
                
                # Handle list variations (Fix for the crash you saw earlier)
                if isinstance(raw_spans[0], int):
                    final_spans = [raw_spans]
                else:
                    final_spans = raw_spans
                
                for span in final_spans:
                    if len(span) >= 2:
                        start, end = span[0], span[1]
                        clause_text = doc_text[start:end]
                        
                        # Only keep clauses with meaningful length
                        if len(clause_text) > 20:
                            new_rows.append({
                                "source": "ContractNLI",
                                "contract_name": f"NDA_{doc['id']}",
                                "risk_category": TARGET_KEYS[key], 
                                "risky_clause": clause_text
                            })

    # Append to existing file (which currently holds your CUAD data)
    if os.path.exists(OUTPUT_FILE):
        try:
            existing_df = pd.read_json(OUTPUT_FILE)
            final_df = pd.concat([existing_df, pd.DataFrame(new_rows)])
        except:
            final_df = pd.DataFrame(new_rows)
    else:
        final_df = pd.DataFrame(new_rows)

    # Save
    final_df.to_json(OUTPUT_FILE, orient='records', indent=4)
    print(f"✅ Step 2 Done: Added {len(new_rows)} NLI clauses. Total Database: {len(final_df)}")

if __name__ == "__main__":
    extract_nli_data()