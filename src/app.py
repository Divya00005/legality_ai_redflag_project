import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
import os

# 1. CONFIGURATION
DB_PATH = "data/chroma_db"
# We keep the stricter threshold we found worked best (0.35)
DISTANCE_THRESHOLD = 0.35

# Set page layout to wide for better comparison view
st.set_page_config(page_title="Legality AI Scanner", layout="wide")

# 2. HELPER FUNCTIONS
def extract_text_from_pdf(uploaded_file):
    """Reads text from the uploaded PDF object"""
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def split_into_clauses(text):
    """Splits text into analyzable chunks"""
    # Simple split by newline, filtering out empty/short lines
    return [line.strip() for line in text.split('\n') if len(line.strip()) > 30]

# 3. MAIN APP
def main():
    # --- HEADER ---
    st.title("⚖️ Legality AI: Golden Standard Scanner")
    st.markdown("""
    **Upload a legal contract (PDF) to mathematically identify deviations from standard safety clauses.**
    This tool compares your document against a vector database of 500+ known risks.
    """)
    st.divider()

    # --- SIDEBAR (Debug Info) ---
    with st.sidebar:
        st.header("⚙️ Scanner Settings")
        st.write(f"**Sensitivity:** {DISTANCE_THRESHOLD}")
        st.write(f"**Database:** {DB_PATH}")
        st.info("System Ready")

    # --- FILE UPLOADER ---
    uploaded_file = st.file_uploader("📂 Drag and drop your contract here", type="pdf")

    if uploaded_file is not None:
        # --- PROCESSING ---
        with st.spinner("🔍 Reading document and vectorizing text..."):
            # 1. Connect to Brain
            client = chromadb.PersistentClient(path=DB_PATH)
            sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            collection = client.get_collection(name="legal_risks", embedding_function=sentence_transformer_ef)

            # 2. Analyze Text
            text = extract_text_from_pdf(uploaded_file)
            clauses = split_into_clauses(text)
            
            risks_found = []
            
            # Progress Bar
            progress_bar = st.progress(0)
            
            for i, clause in enumerate(clauses):
                # Update progress
                progress_bar.progress((i + 1) / len(clauses))
                
                # Query DB
                results = collection.query(
                    query_texts=[clause],
                    n_results=1,
                    include=["metadatas", "distances"]
                )
                
                distance = results['distances'][0][0]
                
                # Check threshold
                if distance < DISTANCE_THRESHOLD:
                    metadata = results['metadatas'][0][0]
                    deviation_score = (1 - distance) * 100
                    
                    risks_found.append({
                        "clause": clause,
                        "category": metadata['category'],
                        "safe_rewrite": metadata['safe_rewrite'],
                        "deviation": deviation_score
                    })

            # --- DISPLAY RESULTS ---
            progress_bar.empty() # Remove bar when done
            
            if len(risks_found) == 0:
                st.balloons()
                st.success("✅ **Clean Contract!** No significant deviations from the Golden Standard detected.")
            else:
                st.error(f"🚨 **Scan Complete:** Found {len(risks_found)} Critical Deviations")
                
                for i, risk in enumerate(risks_found):
                    st.divider()
                    
                    # Create columns for Side-by-Side comparison
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader(f"🚩 Risk #{i+1}: {risk['category']}")
                        st.markdown(f"**Deviates by:** `{risk['deviation']:.2f}%`")
                        # Visual red bar for risk
                        st.markdown(f"""
                        <div style="padding:10px; background-color:#ffe6e6; border-left:5px solid #ff4b4b; color: black;">
                            "{risk['clause']}"
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.subheader("🛡️ Golden Standard Suggestion")
                        st.markdown("**Proposed Rewrite:**")
                        # Visual green bar for safe option
                        st.markdown(f"""
                        <div style="padding:10px; background-color:#e6fffa; border-left:5px solid #00cc96; color: black;">
                            {risk['safe_rewrite']}
                        </div>
                        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()