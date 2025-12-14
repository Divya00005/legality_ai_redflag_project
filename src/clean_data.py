import os
import json
import pandas as pd
import re

# 1. SETUP FILES
# We read your existing file, clean it, and save it back.
INPUT_FILE = 'data/processed/risky_clauses_final.json' 
OUTPUT_FILE = 'data/processed/risky_clauses_clean.json' # Save as a new clean file

def clean_text(text):
    """Fixes common formatting issues in legal text."""
    if not isinstance(text, str):
        return ""
    
    # 1. Fix smart quotes and weird encoding
    text = text.replace("â€™", "'").replace("â€œ", '"').replace("â€", '"')
    text = text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    
    # 2. Normalize whitespace (turn multiple spaces into one)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 3. Remove numbering at the start (e.g., "1. The Clause..." -> "The Clause...")
    text = re.sub(r'^[\d\.\-\)\*]+\s*', '', text)
    
    return text

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found.")
        print("   Make sure your data is in the data/processed folder.")
        return

    print(f"🧹 Loading data from {INPUT_FILE}...")
    df = pd.read_json(INPUT_FILE)
    
    original_count = len(df)
    print(f"   Found {original_count} rows.")

    # 1. Clean the Text
    print("🧼 Scrubbing text...")
    df['risky_clause'] = df['risky_clause'].apply(clean_text)
    
    # 2. Remove Duplicates (Critical Step)
    df = df.drop_duplicates(subset=['risky_clause'])
    
    # 3. Remove Empty or Too Short rows (Garbage data)
    df = df[df['risky_clause'].str.len() > 15] 

    # Stats
    final_count = len(df)
    print(f"✨ Cleaning Done! Removed {original_count - final_count} garbage rows.")
    
    # Save
    df.to_json(OUTPUT_FILE, orient='records', indent=4)
    print(f"📁 Saved CLEAN data to: {OUTPUT_FILE}")
    print("   (Use this file for the next step!)")

if __name__ == "__main__":
    main()