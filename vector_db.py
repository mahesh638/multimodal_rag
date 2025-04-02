import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from uuid import uuid4
import boto3

# Load API Key from .env file
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
DYNAMO_DB_TABLE = os.getenv("DYNAMO_DB_TABLE")
AWS_REGION = os.getenv("AWS_REGION")
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

def store_embeddings_in_pinecone(pdf_uuid, index_name=None):
    """
    Reads text from DynamoDB using the given UUID, chunks it, generates embeddings,
    and stores them in Pinecone.

    Parameters:
    - pdf_uuid (str): The UUID of the PDF stored in DynamoDB.
    - index_name (str, optional): The Pinecone index name (default is the pdf_uuid itself).
    """
    if index_name is None:
        index_name = pdf_uuid  # Use pdf_uuid as the Pinecone index name

    # Load MiniLM embedding model
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # Fetch data from DynamoDB
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMO_DB_TABLE)
    response = table.get_item(Key={"pdf_uuid": pdf_uuid})

    if "Item" not in response:
        print(f"❌ No data found in DynamoDB for pdf_uuid: {pdf_uuid}")
        return

    pdf_data = response["Item"]
    if "pages" not in pdf_data:
        print(f"❌ No pages found in the record for pdf_uuid: {pdf_uuid}")
        return

    print(f"✅ Retrieved text data from DynamoDB for pdf_uuid: {pdf_uuid}")

    # Check if the Pinecone index exists
    existing_indexes = pc.list_indexes().names()
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=384,  # MiniLM embeddings are 384-dimensional
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")  # Adjust if needed
        )

    index = pc.Index(index_name)

    # Store embeddings in Pinecone with page metadata
    vectors = []

    # Iterate through pages and process text
    for page_no, page_data in pdf_data["pages"].items():
        text = page_data.get("text", "").strip()
        if not text:
            continue  # Skip empty pages

        # Chunk text
        chunks = chunk_text(text)
        embeddings = model.encode(chunks).tolist()  # Generate embeddings

        # Create vectors with metadata
        for emb, chunk in zip(embeddings, chunks):
            vectors.append((str(uuid4()), emb, {"text": chunk, "page": page_no}))

    # Upsert all vectors into Pinecone
    if vectors:
        index.upsert(vectors)
        print(f"✅ Stored {len(vectors)} chunks in Pinecone index '{index_name}' with page metadata.")
    else:
        print(f"⚠ No valid text chunks found for pdf_uuid: {pdf_uuid}")


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
