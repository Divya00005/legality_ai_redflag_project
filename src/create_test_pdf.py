from fpdf import FPDF
import os

def create_dummy_contract():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="SERVICE AGREEMENT (DRAFT)", ln=1, align="C")
    pdf.ln(10)
    pdf.multi_cell(0, 10, "1. This agreement is made between Party A and Party B.")
    pdf.set_text_color(255, 0, 0)
    pdf.multi_cell(0, 10, "3. LIABILITY: The Service Provider shall be liable for all damages, losses, and costs without any limitation or cap, regardless of the cause.")
    pdf.output("data/test_files/risky_contract.pdf")
    print("✅ Created dummy contract.")

if __name__ == "__main__":
    create_dummy_contract()
