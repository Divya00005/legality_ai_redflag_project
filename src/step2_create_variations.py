import os
import time
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# 1. Setup
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    print("❌ Error: OPENROUTER_API_KEY is missing.")
    exit()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# 🔴 UPDATED FILE NAMES
INPUT_FILE = 'data/processed/step1_safe_clauses.json'
OUTPUT_FILE = 'data/processed/step2_final_variations.json'

# 🔴 CONFIGURATION: Use Llama 4 Maverick
MODEL_NAME = "meta-llama/Llama-4-Maverick-17B-128E-Instruct"

def generate_variations(safe_text):
    prompt = f"""
    Read this safe legal clause: "{safe_text}"
    
    Task: Write 4 DIFFERENT variations of this clause using different words but keeping the same legal meaning.
    
    Output Format:
    1. [First variation]
    2. [Second variation]
    3. [Third variation]
    4. [Fourth variation]
    
    Output ONLY the numbered list. No extra text.
    """
    
    for attempt in range(3):
        try:
            print(f"   ...Expanding via {MODEL_NAME}...", end="\r")
            completion = client.chat.completions.create(
                model=MODEL_NAME, 
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7 
            )
            content = completion.choices[0].message.content.strip()
            
            # Parse the numbered list
            variations = []
            for line in content.split('\n'):
                # Look for lines starting with "1.", "2.", etc.
                if line.strip() and line.strip()[0].isdigit() and "." in line[:3]:
                    variations.append(line.split('.', 1)[-1].strip())
            
            return variations[:4] # Ensure we get exactly up to 4
            
        except Exception as e:
            if "402" in str(e): # Credits run out -> Switch to free
                 print("   ⚠️ No credits. Switching to Free Model...")
                 return generate_variations_fallback(prompt)
            if "429" in str(e):
                time.sleep(10)
            else:
                return []
    return []

def generate_variations_fallback(prompt):
    """Fallback to free Llama 3 if Maverick fails"""
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-3.1-8b-instruct:free", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = completion.choices[0].message.content.strip()
        variations = []
        for line in content.split('\n'):
            if line.strip() and line.strip()[0].isdigit() and "." in line[:3]:
                variations.append(line.split('.', 1)[-1].strip())
        return variations[:4]
    except:
        return []

def main():
    if not os.path.exists(INPUT_FILE):
        print("❌ Error: Run Step 1 first!")
        return

    # Check resume
    existing_data = []
    if os.path.exists(OUTPUT_FILE):
        try:
            existing_data = pd.read_json(OUTPUT_FILE).to_dict('records')
            print(f"🔄 Resuming... Found {len(existing_data)} done.")
        except: pass
            
    processed_ids = {row['id'] for row in existing_data if 'id' in row}

    df = pd.read_json(INPUT_FILE)
    results = existing_data
    
    print(f"🚀 Step 2: Generating Variations (Target: Maverick)...")

    for index, row in df.iterrows():
        row_id = row['id']
        
        if row_id in processed_ids:
            continue

        base_safe = row['safe_clause_base']
        
        # Generate 4 variations
        vars = generate_variations(base_safe)
        
        # If we got variations (or at least have the base one)
        if vars or base_safe:
            entry = {
                "id": row_id,
                "category": row['category'],
                "safe_option_1": base_safe,               # Original
                "safe_option_2": vars[0] if len(vars) > 0 else "",
                "safe_option_3": vars[1] if len(vars) > 1 else "",
                "safe_option_4": vars[2] if len(vars) > 2 else "",
                "safe_option_5": vars[3] if len(vars) > 3 else ""
            }
            results.append(entry)
            print(f"   ✅ [{index+1}/{len(df)}] Expanded to 5 Options")
            
            if len(results) % 5 == 0:
                pd.DataFrame(results).to_json(OUTPUT_FILE, orient='records', indent=4)
        
        time.sleep(1)

    # Final Save
    pd.DataFrame(results).to_json(OUTPUT_FILE, orient='records', indent=4)
    print(f"\n🎉 SUCCESS! Final dataset saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()