import os
import boto3
import pdfplumber
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from pathlib import Path

# Initialize AWS Clients
dynamodb = boto3.resource("dynamodb", region_name="us-west-1")  # Ensure correct region
s3 = boto3.client("s3", region_name="us-west-1")

# Define AWS Resources
DYNAMODB_TABLE = "pdf_by_pages"
S3_BUCKET = "my-rag-images"

# Create temp_images directory if it doesn't exist
TEMP_DIR = "temp_images"
os.makedirs(TEMP_DIR, exist_ok=True)  # ✅ Fix: Ensures temp_images/ exists

def process_pdf(pdf_path, pdf_uuid):
    """
    Processes a PDF by extracting text, tables, and images.
    - Stores text and tables in DynamoDB under `pdf_uuid`
    - Uploads extracted images to S3 under `my-rag-images/{pdf_uuid}/`
    
    Parameters:
    - pdf_path (str): Path to the PDF file.
    - pdf_uuid (str): Unique identifier for the PDF.
    """
    # Get DynamoDB table reference (explicitly fetching it)
    table = boto3.resource("dynamodb", region_name="us-west-1").Table(DYNAMODB_TABLE)

    # Debugging print
    print(f"DEBUG: Type of table object -> {type(table)}")

    # Extract PDF name (without extension)
    pdf_name = Path(pdf_path).stem

    # Define output folders in S3
    s3_folder = f"{pdf_uuid}/"
    pages_folder = f"{s3_folder}pages_as_images/"
    embedded_images_folder = f"{s3_folder}images_in_pdf/"

    # Initialize storage for text & tables
    pdf_data = {"pdf_uuid": pdf_uuid, "pages": {}}

    # Extract Text & Tables
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_data = {"text": page.extract_text() or "", "tables": {}}

            # Extract tables (if any)
            tables = page.extract_table()
            if tables:
                for idx, table_data in enumerate(tables, start=1):  # ✅ FIXED variable reuse
                    page_data["tables"][str(idx)] = table_data  # Store as string-indexed dict

            # Store in data structure
            pdf_data["pages"][str(i)] = page_data

    # Store in DynamoDB
    table.put_item(Item=pdf_data)  # ✅ This should now work without errors
    print(f"✅ Stored text & tables in DynamoDB for PDF UUID: {pdf_uuid}")

    # Convert PDF pages to images
    page_images = convert_from_path(pdf_path, dpi=300)

    # Upload Full Page Images to S3
    for i, img in enumerate(page_images, start=1):
        page_filename = f"page_{i}.png"  # ✅ Corrected filename format
        local_path = os.path.join(TEMP_DIR, page_filename)  # Save temporarily

        # ✅ Ensure directory exists before saving
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        img.save(local_path, "PNG")  # ✅ Now this won't fail

        s3.upload_file(local_path, S3_BUCKET, pages_folder + page_filename)
        os.remove(local_path)  # Clean up after upload

    print(f"✅ Uploaded page images to S3: s3://{S3_BUCKET}/{pages_folder}")

    # Extract Embedded Images
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc):
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_filename = f"embedded_page{i+1}_img{img_index}.{image_ext}"

            local_path = os.path.join(TEMP_DIR, image_filename)

            with open(local_path, "wb") as f:
                f.write(image_bytes)

            s3.upload_file(local_path, S3_BUCKET, embedded_images_folder + image_filename)
            os.remove(local_path)  # Clean up after upload

    print(f"✅ Uploaded embedded images to S3: s3://{S3_BUCKET}/{embedded_images_folder}")

    return {"status": "Processing complete", "pdf_uuid": pdf_uuid}

# # Example usage
# if __name__ == "__main__":
#     pdf_uuid = "123e4567-e89b-12d3-a456-426614174000"  # Replace with actual UUID
#     pdf_path = "doc.pdf"  # Replace with actual PDF file path

#     result = process_pdf(pdf_path, pdf_uuid)
#     print(result)
