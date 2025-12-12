import json
import pandas as pd
import os

# CONFIGURATION
INPUT_FILE = 'data/raw/CUAD_v1.json'
OUTPUT_FILE = 'data/processed/risky_clauses.json'

# MAPPING: Mentor's Risk Category -> The specific phrase to find inside the long question
TARGET_MAPPING = {
    "Unilateral Termination": "Termination For Convenience",
    "Non-Compete": "Non-Compete",
    # ✅ CORRECT: We search for this phrase inside the long sentence
    "Unlimited Liability": "Uncapped Liability" 
}

def extract_cuad_data():
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

    extracted_rows = []
    print("🔍 Scanning CUAD contracts...")

    for contract in data.get('data', []):
        title = contract.get('title', 'Unknown')
        
        for paragraph in contract.get('paragraphs', []):
            for qa in paragraph.get('qas', []):
                question_text = qa['question'] # Keep original case for now
                
                # Check against our 3 target categories
                for mentor_category, target_phrase in TARGET_MAPPING.items():
                    # ✅ THE FIX: substring search using 'in' (Case Insensitive)
                    if target_phrase.lower() in question_text.lower():
                        for answer in qa['answers']:
                            clause_text = answer['text']
                            
                            # Only keep valid clauses > 30 chars
                            if len(clause_text) > 30:
                                extracted_rows.append({
                                    "source": "CUAD",
                                    "contract_name": title,
                                    "risk_category": mentor_category, # Saves as "Unlimited Liability"
                                    "risky_clause": clause_text
                                })

    if not extracted_rows:
        print("❌ No rows extracted. Check the phrase again.")
        return

    # Save as JSON
    df = pd.DataFrame(extracted_rows)
    os.makedirs('data/processed', exist_ok=True)
    df.to_json(OUTPUT_FILE, orient='records', indent=4)
    
    print(f"✅ Step 1 Done: Saved {len(df)} clauses to '{OUTPUT_FILE}'")
    print("   • Clause Counts:", df['risk_category'].value_counts().to_dict())

if __name__ == "__main__":
    extract_cuad_data()