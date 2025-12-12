import os
import json
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

# FILES
INPUT_FILE = 'data/processed/risky_clauses_final.json'
# We overwrite the previous file with high-quality Maverick data
OUTPUT_FILE = 'data/processed/safe_clauses_expanded.json'

def generate_safe_version_maverick(risky_text, category):
    """Asks Llama 4 Maverick to act as a lawyer."""
    
    prompt = f"""
    You are an expert lawyer. Rewrite the following "{category}" clause to be fair and safe for the employee/contractor.
    
    RULES:
    1. Remove the unfair risk (e.g., add notice periods, caps on liability, or specific scopes).
    2. Keep the legal tone professional.
    3. Output ONLY the rewritten clause. No explanations or intro.
    
    RISKY CLAUSE: "{risky_text}"
    
    SAFE REWRITE:
    """
    
    try:
        completion = client.chat.completions.create(
            # 🔴 EXACT MODEL ID YOU REQUESTED
            model="meta-llama/Llama-4-Maverick-17B-128E-Instruct", 
            messages=[{"role": "user", "content": prompt}],
            extra_headers={
                "HTTP-Referer": "https://github.com/legality-ai",
                "X-Title": "Legality AI"
            },
            temperature=0.3, # Low temp for precision
            max_tokens=450,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Model Error: {e}")
        return None

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found.")
        return

    print(f"⏳ Loading risky clauses from {INPUT_FILE}...")
    df = pd.read_json(INPUT_FILE)
    
    results = []
    
    print(f"🚀 Starting Llama 4 Maverick Generation...")
    print(f"   (Model: meta-llama/Llama-4-Maverick-17B-128E-Instruct)")

    for index, row in df.iterrows():
        risky_text = row['risky_clause']
        category = row['risk_category']
        
        safe_text = generate_safe_version_maverick(risky_text, category)
        
        if safe_text:
            results.append({
                "category": category,
                "source": row['source'],
                "risky_clause": risky_text,
                "safe_clause": safe_text
            })
            print(f"   ✅ [{index+1}/{len(df)}] Fixed: {category}")
        else:
            print(f"   ⚠️ [{index+1}/{len(df)}] Failed (Model might be busy/invalid)")
        
        # Tiny sleep to avoid aggressive rate limits
        time.sleep(0.5)

    # Save
    final_df = pd.DataFrame(results)
    final_df.to_json(OUTPUT_FILE, orient='records', indent=4)
    print(f"\n🎉 SUCCESS! Regenerated Knowledge Base saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()