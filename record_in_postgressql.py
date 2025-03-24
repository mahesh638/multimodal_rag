import os
import psycopg2
from dotenv import load_dotenv
from uuid import uuid4

# Load environment variables from .env file
load_dotenv()
POSTGRESQL_HOST = os.getenv("POSTGRESQL_HOST")
POSTGRESQL_DBNAME = os.getenv("POSTGRESQL_DBNAME")
POSTGRESQL_USER = os.getenv("POSTGRESQL_USER")
POSTGRESQL_PASSWORD = os.getenv("POSTGRESQL_PASSWORD")
POSTGRESQL_PORT = os.getenv("POSTGRESQL_PORT")

def get_or_create_index_uuid(pdf_name, owner):
    """
    Checks if a (pdf_name, owner) entry exists in PostgreSQL.
    If not, generates a new UUID and inserts it.

    Parameters:
    - pdf_name (str): The name of the PDF.
    - owner (str): The owner of the document.

    Returns:
    - str: The index UUID (which serves as the Pinecone index name).
    """

    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname=POSTGRESQL_DBNAME,
        user=POSTGRESQL_USER,
        password=POSTGRESQL_PASSWORD,
        host=POSTGRESQL_HOST,
        port=POSTGRESQL_PORT
    )
    cursor = conn.cursor()

    # Ensure the table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pdf_index_mapping (
            name_of_pdf TEXT NOT NULL,
            owner TEXT NOT NULL,
            index_uuid TEXT UNIQUE NOT NULL,
            PRIMARY KEY (name_of_pdf, owner)
        );
    """)
    conn.commit()

    # Check if the entry already exists
    cursor.execute(
        "SELECT index_uuid FROM pdf_index_mapping WHERE name_of_pdf = %s AND owner = %s;",
        (pdf_name, owner)
    )
    result = cursor.fetchone()

    if result:
        index_uuid = result[0]  # Retrieve existing UUID
    else:
        index_uuid = str(uuid4())  # Generate a new UUID
        cursor.execute(
            "INSERT INTO pdf_index_mapping (name_of_pdf, owner, index_uuid) VALUES (%s, %s, %s);",
            (pdf_name, owner, index_uuid)
        )
        conn.commit()

    # Close connection
    cursor.close()
    conn.close()

    return index_uuid  # This is the name to be used for the Pinecone index

# Example usage
if __name__ == "__main__":
    pdf_name = "doc.pdf"
    owner = "maheshvar"
    index_name = get_or_create_index_uuid(pdf_name, owner)
    print(f"Pinecone Index Name (UUID): {index_name}")
