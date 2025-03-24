import pdfplumber
from pdf2image import convert_from_path
import os
import fitz  # PyMuPDF
from pathlib import Path

# If using Windows, set the path to Tesseract-OCR (uncomment and update if needed)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pdf_path = "doc.pdf"  # Your PDF file

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF using pdfplumber and returns a dictionary where:
    - Keys = Page numbers (starting from 1)
    - Values = Extracted text from the respective page

    Parameters:
    - pdf_path (str): Path to the PDF file.

    Returns:
    - dict: {page_number: "text_from_page"}
    """
    text_dict = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):  # Start page numbering from 1
            text_dict[i] = page.extract_text() or ""  # Store text with page number as key

    print("Text processed")
    return text_dict  # Dictionary with page-wise text

def extract_tables_from_pdf(pdf_path):
    """Extracts tables from a PDF using pdfplumber."""
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            table = page.extract_table()
            if table:
                tables.append({"page": i+1, "table": table})
    return tables

def extract_images_from_pdf(pdf_path):
    """
    Extracts:
    1. Each page as an image -> saved in 'images/<pdf_name>/pages_as_images'.
    2. Embedded images inside the PDF -> saved in 'images/<pdf_name>/images_in_pdf'.
    """
    # Extract the PDF name without extension
    pdf_name = Path(pdf_path).stem
    
    # Define output folders
    base_folder = f"images/{pdf_name}"
    pages_folder = f"{base_folder}/pages_as_images"
    embedded_images_folder = f"{base_folder}/images_in_pdf"

    # Create necessary directories
    os.makedirs(pages_folder, exist_ok=True)
    os.makedirs(embedded_images_folder, exist_ok=True)

    # Convert each page to an image and save
    page_images = convert_from_path(pdf_path, dpi=300)
    page_image_paths = []
    
    for i, img in enumerate(page_images):
        page_filename = f"{pages_folder}/page_{i+1}.png"
        img.save(page_filename, "PNG")
        page_image_paths.append(page_filename)

    # Extract embedded images using PyMuPDF (fitz)
    doc = fitz.open(pdf_path)
    embedded_image_paths = []
    
    for i, page in enumerate(doc):
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"{embedded_images_folder}/embedded_page{i+1}_img{img_index}.{image_ext}"
            
            with open(image_filename, "wb") as f:
                f.write(image_bytes)
                
            embedded_image_paths.append(image_filename)

    return {"base_folder": base_folder, "page_images": page_image_paths, "embedded_images": embedded_image_paths}


# # Running the extraction
# text = extract_text_from_pdf(pdf_path)
# tables = extract_tables_from_pdf(pdf_path)
# images = extract_images_from_pdf(pdf_path)

# # Printing the results
# print("Extracted Text:\n", text[:500])  # First 500 characters of text
# print("\nExtracted Tables:\n", tables)
# print("\nExtracted Images Saved at:\n", images)
