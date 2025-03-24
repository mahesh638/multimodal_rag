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

def encode_image_to_base64(image_path):
    """Encodes an image as Base64 format."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def call_gemini_multimodal(question, chunks, image_paths):
    """
    Makes a multimodal API call to Gemini 2.0, sending both a text prompt and multiple images.

    Parameters:
    - question (str): The user question.
    - chunks (list): A list of text chunks that provide context.
    - image_paths (list): A list of image file paths.

    Returns:
    - str: The Gemini model's response.
    """
    # Prepare the prompt
    prompt = """You are given some context from which you will answer questions. 
    Additionally, images relevant to the question are provided. The context is as follows: """

    context = "\n".join(chunks)  # Merge text chunks efficiently
    prompt = prompt + context + "\n" + question  # Combine everything

    # Encode all images into Base64
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

if __name__ == "__main__":
    question = "Why does LXMERT and VisualBERT not perform well?"

    # Retrieve top relevant text chunks and their corresponding pages
    retrieved_text = retrieve_top_k_text(question, index_name="pdf-text-index", k=3)

    if not retrieved_text:
        print("No relevant text found in the index.")
    else:
        # Extract text chunks and collect corresponding page numbers
        chunks = [text for text, page in retrieved_text]
        page_numbers = [page for _, page in retrieved_text]

        # Define the image directory
        IMAGE_DIR = r"D:\Pet projects\rag\code\images\doc\pages_as_images"

        # Collect image paths for the retrieved pages
        image_paths = []
        for page_no in page_numbers:
            image_path = os.path.join(IMAGE_DIR, f"page_{page_no}.png")
            if os.path.exists(image_path):  # Only add existing images
                image_paths.append(image_path)

        # Call Gemini multimodal function with retrieved text and images
        result = call_gemini_multimodal(question, chunks, image_paths)

        # Print the response
        print("Gemini Response:\n", result)
