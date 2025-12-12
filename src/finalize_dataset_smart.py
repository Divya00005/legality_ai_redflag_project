import pandas as pd
import os

# CONFIGURATION
INPUT_FILE = 'data/processed/risky_clauses.json'       # Reading the JSON you just created
OUTPUT_FILE = 'data/processed/risky_clauses_final.json' # Saving the Final Golden Dataset

# Keywords for Smart Scoring
QUALITY_KEYWORDS = {
    "Unilateral Termination": ["without cause", "convenience", "immediately", "at any time", "sole discretion"],
    # CRITICAL: We look for "uncapped" here to prioritize those specific risks
    "Unlimited Liability": ["indemnify", "consequential", "unlimited", "uncapped", "no cap", "negligence", "willful misconduct", "limit"],
    "Non-Compete": ["compete", "solicit", "competitor", "business", "territory", "12 months", "years"]
}

def calculate_quality_score(text, category):
    score = 0
    text_lower = str(text).lower()
    
    # 1. Length Score (We prefer clauses 200-1000 chars long)
    length = len(text_lower)
    if length < 100: score -= 50
    elif 200 <= length <= 1000: score += 20
    else: score += 5
        
    # 2. Keyword Score (Bonus points if it contains specific risk words)
    if category in QUALITY_KEYWORDS:
        for word in QUALITY_KEYWORDS[category]:
            if word in text_lower:
                score += 10 
                
    return score

def finalize_dataset_smart():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found.")
        return

    print(f"⏳ Reading combined data from {INPUT_FILE}...")
    # Read JSON instead of CSV
    df = pd.read_json(INPUT_FILE)
    
    # Deduplicate (Remove exact matches)
    df = df.drop_duplicates(subset=['risky_clause'])
    
    # Score every clause
    print("🧠 Calculating quality scores...")
    df['quality_score'] = df.apply(lambda row: calculate_quality_score(row['risky_clause'], row['risk_category']), axis=1)

    final_rows = []

    # --- SELECTION: Top 50 for each target ---
    
    # 1. Unilateral Termination (CUAD)
    term = df[(df['risk_category'] == 'Unilateral Termination') & (df['source'] == 'CUAD')]
    final_rows.append(term.sort_values(by='quality_score', ascending=False).head(50))

    # 2. Unlimited Liability (CUAD)
    # This filters the "Unlimited Liability" category for high-scoring clauses (containing "uncapped", etc.)
    liab = df[(df['risk_category'] == 'Unlimited Liability') & (df['source'] == 'CUAD')]
    final_rows.append(liab.sort_values(by='quality_score', ascending=False).head(50))

    # 3. Non-Compete (CUAD)
    nc_cuad = df[(df['risk_category'] == 'Non-Compete') & (df['source'] == 'CUAD')]
    final_rows.append(nc_cuad.sort_values(by='quality_score', ascending=False).head(50))

    # 4. Non-Compete (ContractNLI)
    nc_nli = df[(df['risk_category'] == 'Non-Compete') & (df['source'] == 'ContractNLI')]
    final_rows.append(nc_nli.sort_values(by='quality_score', ascending=False).head(50))

    # --- SAVE ---
    if not final_rows:
        print("❌ No rows selected!")
        return

    final_df = pd.concat(final_rows)
    final_df = final_df.drop(columns=['quality_score']) # Clean up score column
    
    # Shuffle the data so it's not in order
    final_df = final_df.sample(frac=1, random_state=42).reset_index(drop=True)

    # Save as JSON
    final_df.to_json(OUTPUT_FILE, orient='records', indent=4)
    
    print(f"\n🚀 SUCCESS! Final dataset saved to: {OUTPUT_FILE}")
    print(f"📊 Total Rows: {len(final_df)} ")
    print(f"   • Unilateral Termination: {len(term.head(50))}")
    print(f"   • Unlimited Liability:    {len(liab.head(50))}")
    print(f"   • Non-Compete (CUAD):     {len(nc_cuad.head(50))}")
    print(f"   • Non-Compete (NLI):      {len(nc_nli.head(50))}")

if __name__ == "__main__":
    finalize_dataset_smart()