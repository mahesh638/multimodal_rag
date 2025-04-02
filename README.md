# 📄 Multimodal PDF Question Answering (Prototype)

This project is a prototype of a **multimodal Retrieval-Augmented Generation (RAG)** system that answers user queries based on the contents of an uploaded PDF document.

## 🚀 How It Works

1. **PDF Ingestion**  
   The uploaded PDF's text is extracted and stored in a **DynamoDB** table.

2. **Text Chunking & Indexing**  
   Extracted text is chunked, each chunk is tagged with its **page number** as metadata, and stored in a **Pinecone** vector index.

3. **Image Storage**  
   Page-wise images of the PDF are generated and stored in an **S3 bucket**.

4. **Streamlit Interface**  
   A user-friendly **Streamlit** web app allows users to upload PDFs and ask questions.

5. **Query Handling**  
   - The system retrieves the most relevant chunks using **cosine similarity**.
   - It identifies associated **page numbers** via metadata.
   - It fetches the corresponding **page images** from S3.
   - Both the **text chunks** and **images** are passed to **Gemini 2.0**, a multimodal LLM, to generate an accurate response.

This hybrid approach of combining visual and textual data enables deeper contextual understanding and produces highly relevant answers.

---

## 🛠️ Running the App

1. Install dependencies:
   ```bash
   pip install -r requirements.txt

2. Fill in the required environment variables in the env.txt file.

3. Launch the Streamlit app:
    ```bash
   streamlit run webapp.py


