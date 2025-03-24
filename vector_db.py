import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from uuid import uuid4
from pdf_preprocessing import extract_text_from_pdf

# Load API Key from .env file
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

def chunk_text(text, chunk_size=3000, overlap=50):
    """
    Splits text into overlapping chunks.
    
    Parameters:
    - text (str): Input text.
    - chunk_size (int): Maximum length of each chunk.
    - overlap (int): Number of overlapping characters between chunks.
    
    Returns:
    - List of text chunks.
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap  # Move forward with overlap

    print("Chunks processed")
    return chunks

def store_embeddings_in_pinecone(text_dict, index_name="pdf-text-index"):
    """
    Chunks text from each page, generates BERT embeddings, and stores them in a Pinecone index.

    Parameters:
    - text_dict (dict): A dictionary where keys are page numbers and values are text from those pages.
    - index_name (str): Pinecone index name.
    """
    # Load MiniLM embedding model
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # Check if the index exists
    existing_indexes = pc.list_indexes().names()
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=384,  # MiniLM embeddings are 384-dimensional
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")  # Adjust region if needed
        )

    index = pc.Index(index_name)

    # Store embeddings in Pinecone with page metadata
    vectors = []
    
    for page_no, text in text_dict.items():
        chunks = chunk_text(text)  # Chunk the text from the page
        embeddings = model.encode(chunks).tolist()  # Generate embeddings

        # Create vectors with metadata
        for emb, chunk in zip(embeddings, chunks):
            vectors.append((str(uuid4()), emb, {"text": chunk, "page": page_no}))

    # Upsert all vectors into Pinecone
    index.upsert(vectors)

    print(f"Stored {len(vectors)} chunks in Pinecone index '{index_name}' with page metadata.")


def retrieve_top_k_text(query, index_name="pdf-text-index", k=1):
    """
    Retrieves the top K most relevant text chunks from the Pinecone index for a given query,
    along with their corresponding page numbers.

    Parameters:
    - query (str): The input query text.
    - index_name (str): Pinecone index name.
    - k (int): Number of top matches to return.

    Returns:
    - list of tuples: [(chunk_text, page_number)] or an empty list if no results are found.
    """
    # Load the same MiniLM model used for storage
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # Get the Pinecone index
    index = pc.Index(index_name)

    # Encode query text
    query_embedding = model.encode(query).tolist()

    # Search in Pinecone index
    results = index.query(vector=query_embedding, top_k=k, include_metadata=True)

    # Extract matches with text and page number (if available)
    if results and results.get("matches"):
        print("Returning top k")
        return [
            (match["metadata"].get("text", "No text available"), match["metadata"].get("page", "Unknown Page"))
            for match in results["matches"]
        ]
    else:
        return []  # Ensure the function always returns a list

# # Example usage
# pdf_text = extract_text_from_pdf("doc.pdf") # Replace with actual extracted text
# store_embeddings_in_pinecone(pdf_text)

# text = "Why does VisualBERT not work?"
# print(retrieve_top_k_text(text))

# Step 1: Extract text from PDF
# pdf_path = "doc.pdf"  # Replace with your actual PDF file path
# text_dict = extract_text_from_pdf(pdf_path)  # Extract text as {page_no: text}

# # Step 2: Store embeddings into Pinecone
# store_embeddings_in_pinecone(text_dict)  # Store in Pinecone with metadata

# # Step 3: Run a query and retrieve the most relevant chunk
# query_text = "Why does LXMERT and VisualBERT not perform well?"
# retrieved_text = retrieve_top_k_text(query_text, k=3)  # Fetch top 3 matches

# # Step 4: Print results
# print("\nRetrieved Text Chunks:\n")
# for text, page in retrieved_text:
#     print(f"Page {page}:\n{text}\n{'-'*50}")
