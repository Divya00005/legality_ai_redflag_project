import os
import time
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# 1. Setup
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    print("❌ Error: OPENROUTER_API_KEY is missing in .env file.")
    exit()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

INPUT_FILE = 'data/processed/risky_clauses_clean.json'
OUTPUT_FILE = 'data/processed/step1_safe_clauses.json'

# 🔴 CONFIGURATION: Use Llama 4 Maverick
MODEL_NAME = "meta-llama/Llama-4-Maverick-17B-128E-Instruct"

def generate_safe_clause(risky_text, category):
    prompt = f"""
    You are an expert lawyer. Rewrite this "{category}" clause to be fair and safe.
    
    RULES:
    1. Remove the unfair risk completely.
    2. Output ONLY the rewritten clause text.
    3. Do NOT include the original risky clause.
    4. Do NOT include any introductory text like "Here is the rewrite".
    
    RISKY CLAUSE: "{risky_text}"
    
    SAFE REWRITE:
    """
    
    # Retry logic (3 attempts)
    for attempt in range(3):
        try:
            print(f"   ...Sending to {MODEL_NAME}...", end="\r")
            
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
            if "402" in str(e): # Insufficient credits
                print("   ❌ CRITICAL: Account has no credits. Switching to Free Model.")
                # Fallback to free model if Maverick fails
                return generate_fallback(prompt)
            if "429" in str(e): # Rate limit
                time.sleep(10)
            else:
                return None
    return None

def generate_fallback(prompt):
    """Fallback to free Llama 3 if Maverick fails"""
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-3.1-8b-instruct:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return completion.choices[0].message.content.strip()
    except:
        return None

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found.")
        return

    # Load input
    df = pd.read_json(INPUT_FILE)
    print(f"📄 Loaded {len(df)} risky clauses.")
    
    # Check for existing work to resume
    existing_data = []
    if os.path.exists(OUTPUT_FILE):
        try:
            existing_data = pd.read_json(OUTPUT_FILE).to_dict('records')
            print(f"🔄 Resuming... Found {len(existing_data)} safe clauses.")
        except: pass
    
    # Get list of IDs we already finished
    processed_ids = {row['id'] for row in existing_data if 'id' in row}

    results = existing_data
    
    print(f"🚀 Step 1: Generating Safe Clauses (Model: Llama 4 Maverick)...")
    print(f"⚠️ NOTE: Saving ONLY Safe Clauses (No Pairs).")

    for index, row in df.iterrows():
        # Resume logic: Skip if we already have this ID
        if index in processed_ids:
            continue

        risky_text = row['risky_clause']
        category = row.get('risk_category', 'General')
        
        # 1. Generate the Safe Version
        safe_text = generate_safe_clause(risky_text, category)
        
        if safe_text:
            # 2. SAVE ONLY THE SAFE DATA
            # We explicitly do NOT add 'risky_text' to this dictionary.
            entry = {
                "id": index,
                "category": category,
                "safe_clause_base": safe_text
            }
            results.append(entry)
            print(f"   ✅ [{index+1}/{len(df)}] Saved Safe Clause")
            
            # Save every 5 rows to be safe
            if len(results) % 5 == 0:
                pd.DataFrame(results).to_json(OUTPUT_FILE, orient='records', indent=4)
        else:
            print(f"   ⚠️ [{index+1}/{len(df)}] Failed")
        
        # Short pause
        time.sleep(1)

    # Final Save
    pd.DataFrame(results).to_json(OUTPUT_FILE, orient='records', indent=4)
    print(f"\n🎉 SUCCESS! Saved {len(results)} rows to: {OUTPUT_FILE}")
    print("   (This file contains NO risky clauses, only Safe ones.)")

if __name__ == "__main__":
    main()