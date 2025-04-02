import boto3
import os
import base64
import google.generativeai as genai
from dotenv import load_dotenv
from vector_db import retrieve_top_k_text

# Load API Key from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# AWS S3 Configuration
S3_BUCKET = "my-rag-images"
AWS_REGION = "us-west-1"  # Update this to your AWS region

# Initialize AWS S3 client
s3 = boto3.client("s3", region_name=AWS_REGION)

def encode_image_to_base64(image_path):
    """Encodes an image as Base64 format."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def get_relevant_images_from_s3(pdf_uuid, pages):
    """
    Downloads relevant images from S3 based on the pages retrieved from Pinecone.
    
    Parameters:
    - pdf_uuid (str): The UUID of the PDF.
    - pages (list): List of page numbers from retrieved text chunks.

    Returns:
    - List of local file paths to downloaded images.
    """
    image_paths = []
    local_image_dir = "temp_images"
    os.makedirs(local_image_dir, exist_ok=True)  # Ensure temp directory exists

    for page in pages:
        s3_key = f"{pdf_uuid}/pages_as_images/page_{page}.png"
        local_image_path = os.path.join(local_image_dir, f"page_{page}.png")

        try:
            s3.download_file(S3_BUCKET, s3_key, local_image_path)  # Download from S3
            image_paths.append(local_image_path)
        except Exception as e:
            print(f"⚠ Warning: Could not retrieve image for page {page}: {e}")

    return image_paths

def call_gemini_multimodal(question, pdf_uuid):
    """
    Fetches top K relevant text chunks, retrieves relevant images from S3,
    and sends a multimodal query to Gemini 2.0.

    Parameters:
    - question (str): The user query.
    - pdf_uuid (str): The UUID of the PDF.

    Returns:
    - str: The Gemini model's response.
    """
    # Retrieve top K relevant text chunks
    k = 3
    retrieved_text_chunks = retrieve_top_k_text(question, index_name=pdf_uuid, k=k)

    if not retrieved_text_chunks:
        return "❌ No relevant information found."

    # Extract text and associated page numbers
    chunks = [text for text, page in retrieved_text_chunks]
    pages = [page for _, page in retrieved_text_chunks]  # Extract relevant page numbers

    print(f"✅ Retrieved relevant text from pages: {pages}")

    # Get relevant images from S3
    image_paths = get_relevant_images_from_s3(pdf_uuid, pages)

    if not image_paths:
        print("⚠ No relevant images found in S3.")

    # Prepare the prompt
    prompt = """You are given some context from which you will answer questions. 
    Additionally, images relevant to the question are provided. The context is as follows: """

    context = "\n".join(chunks)  # Merge text chunks efficiently
    prompt = prompt + context + "\n" + question  # Combine everything

    # Encode images into Base64
    encoded_images = []
    for image_path in image_paths:
        encoded_images.append({
            "mime_type": "image/png",  # Adjust MIME type if needed (e.g., "image/jpeg")
            "data": encode_image_to_base64(image_path)
        })

    # Create a model instance for Gemini multimodal
    model = genai.GenerativeModel("gemini-2.0-flash-exp")

    # Construct request with multiple images
    request_content = [prompt] + encoded_images  # Text first, followed by images

    # Send request to Gemini API
    response = model.generate_content(request_content)

    return response.text  # Get response text

# Example usage
# if __name__ == "__main__":
#     pdf_uuid = "123e4567-e89b-12d3-a456-426614174000"  # Replace with actual UUID
#     question = "What is LXMERT?"

#     result = call_gemini_multimodal(question, pdf_uuid)
#     print("\n🔍 Gemini Response:\n", result)
