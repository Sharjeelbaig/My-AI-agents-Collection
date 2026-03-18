from PyPDF2 import PdfReader, PdfWriter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import io

def edit_pdf(input_path, output_path, new_text):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    # Copy existing pages
    for page in reader.pages:
        writer.add_page(page)

    # Create new page with text
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    doc.build([Paragraph(new_text, styles["Normal"])])

    buffer.seek(0)
    new_pdf = PdfReader(buffer)

    # Add new page
    writer.add_page(new_pdf.pages[0])

    # Save result
    with open(output_path, "wb") as f:
        writer.write(f)