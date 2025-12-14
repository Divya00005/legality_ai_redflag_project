from fpdf import FPDF
import os

def create_dummy_contract():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="SERVICE AGREEMENT (DRAFT)", ln=1, align='C')
    pdf.ln(10)
    
    # Normal safe text
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, "1. This agreement is made between Party A and Party B.")
    pdf.multi_cell(0, 10, "2. The services will be performed in a timely manner.")
    
    # 🔴 THE TRAP (A Risky Clause)
    # This is similar to "Unlimited Liability" but worded differently to test the AI
    pdf.set_text_color(255, 0, 0) # Red color just for us to see
    pdf.multi_cell(0, 10, "3. LIABILITY: The Service Provider shall be liable for all damages, losses, and costs without any limitation or cap, regardless of the cause.")
    
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 10, "4. This agreement shall be governed by the laws of India.")

    if not os.path.exists("data/test_files"):
        os.makedirs("data/test_files")
        
    pdf.output("data/test_files/risky_contract.pdf")
    print("✅ Created dummy contract: data/test_files/risky_contract.pdf")

if __name__ == "__main__":
    create_dummy_contract()