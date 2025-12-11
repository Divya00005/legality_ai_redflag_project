import json
import os
import pandas as pd  # Still useful for grouping/filtering, even if output is JSON

# --- CONFIGURATION ---
INPUT_FILE = 'data/raw/CUAD_v1.json'
OUTPUT_FILE = 'data/processed/risky_clauses.json'

# Mentor's Target Risks mapped to CUAD Questions
TARGET_MAPPING = {
    "Unilateral Termination": "Termination For Convenience",
    "Non-Compete": "Non-Compete",
    "Unlimited Liability": "Uncapped Liability" 
}

def extract_cuad_data():
    # 1. Check if input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: File not found at {INPUT_FILE}")
        return

    print(f"⏳ Reading {INPUT_FILE}... (This takes a few seconds)")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")
        return

    extracted_rows = []
    
    print("🔍 Scanning for clauses inside 'question' field...")
    
    # 2. Iterate through contracts
    for contract in data.get('data', []):
        title = contract.get('title', 'Unknown')
        
        # 3. Iterate through paragraphs and Q&A pairs
        for paragraph in contract.get('paragraphs', []):
            for qa in paragraph.get('qas', []):
                
                # Look at the 'question' text to identify the category
                question_text = qa['question']
                
                # Check if this question matches one of our target categories
                for mentor_category, cuad_label in TARGET_MAPPING.items():
                    if cuad_label in question_text:
                        
                        # Get the answers (the actual clause text)
                        for answer in qa['answers']:
                            clause_text = answer['text']
                            
                            # Filter out very short fragments (noise)
                            if len(clause_text) > 50:
                                extracted_rows.append({
                                    "source": "CUAD",
                                    "contract_name": title,
                                    "risk_category": mentor_category,
                                    "risky_clause": clause_text
                                })

    # 4. Validation
    if len(extracted_rows) == 0:
        print("\n❌ NO MATCHES FOUND. Please check the TARGET_MAPPING or input file.")
        return

    # 5. Process and Filter (Keep top 50 of each category)
    df = pd.DataFrame(extracted_rows)
    final_list = []
    
    print("\n--- Extraction Report ---")
    for category in TARGET_MAPPING.keys():
        subset = df[df['risk_category'] == category]
        count = len(subset)
        print(f"• {category}: Found {count} clauses")
        
        # Take the top 50 (or less if not enough found)
        top_50 = subset.head(50).to_dict(orient='records')
        final_list.extend(top_50)

    # 6. Save as JSON
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_list, f, indent=4, ensure_ascii=False)
        print(f"\n✅ Success! Saved {len(final_list)} clauses to '{OUTPUT_FILE}'")
    except Exception as e:
        print(f"❌ Error saving file: {e}")

if __name__ == "__main__":
    extract_cuad_data()

