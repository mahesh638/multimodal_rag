import streamlit as st
import uuid
import os
from pdf_preprocessing import process_pdf
from vector_db import store_embeddings_in_pinecone  # Ensure Pinecone is populated
from multimodal_llm_api_call import call_gemini_multimodal  # Handles queries

# Define session state variables
if "pdf_uuid" not in st.session_state:
    st.session_state.pdf_uuid = None
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False
if "pinecone_index_created" not in st.session_state:
    st.session_state.pinecone_index_created = False  # Track Pinecone index creation

# Define the Streamlit app
st.title("📄 AI-Powered PDF Processing & Querying")

# Step 1: Upload PDF
if not st.session_state.pdf_processed:
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

    if uploaded_file is not None:
        # Generate a unique UUID for the PDF
        pdf_uuid = str(uuid.uuid4())
        st.session_state.pdf_uuid = pdf_uuid

        # Save the uploaded PDF temporarily
        pdf_path = os.path.join("temp_uploads", uploaded_file.name)
        os.makedirs("temp_uploads", exist_ok=True)  # Ensure directory exists

        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.read())

        # Show progress message
        st.write(f"✅ File uploaded successfully! Processing with UUID: `{pdf_uuid}`")

        # Run the PDF processing function
        with st.spinner("🔄 Processing PDF... This may take a few seconds."):
            process_pdf(pdf_path, pdf_uuid)

        # Ensure Pinecone index is created
        with st.spinner("🔄 Storing text embeddings in Pinecone..."):
            store_embeddings_in_pinecone(pdf_uuid)  # 🔥 Now Pinecone is populated

        # Remove temp file after processing
        os.remove(pdf_path)

        # Update session state
        st.session_state.pdf_processed = True
        st.session_state.pinecone_index_created = True

        st.success(f"🎉 PDF `{uploaded_file.name}` processed successfully!")
        st.write(f"✅ All data stored with UUID: `{pdf_uuid}`")
        st.write("✅ Pinecone index created successfully! You can now ask questions.")

# Step 2: Query Interface (Appears After Processing & Indexing)
if st.session_state.pdf_processed and st.session_state.pinecone_index_created:
    st.subheader("🔍 Ask Questions About Your PDF")
    question = st.text_input("Enter your question:")

    if st.button("Get Answer"):
        if question.strip() == "":
            st.warning("⚠ Please enter a valid question.")
        else:
            with st.spinner("🔄 Fetching relevant information..."):
                response = call_gemini_multimodal(question, st.session_state.pdf_uuid)
            
            st.subheader("🤖 AI Response:")
            st.write(response)
