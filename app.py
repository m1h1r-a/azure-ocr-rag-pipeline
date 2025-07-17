import json
import os

import requests
import streamlit as st
from azure.storage.blob import BlobServiceClient

# Configuration
API_BASE_URL = "https://pdf-processor-functions-v2.azurewebsites.net/api"
API_KEY = os.environ.get("API_KEY")
STORAGE_CONNECTION_STRING = os.environ.get("STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "pdfs"

# Page config (ONLY ONCE, at the very top)
st.set_page_config(page_title="Healthcare AI", page_icon="🏥")
st.title("Centralized AI OCR Solution")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []


def query_backend(question: str):
    """Send question to your Azure Function chat endpoint"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            headers={"Content-Type": "application/json"},
            params={"code": API_KEY},
            json={"message": question},
        )
        if response.status_code == 200:
            return response.json()["formatted_response"]
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"


def upload_pdf_to_blob(uploaded_file):
    """Upload PDF to Azure Blob Storage"""
    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            STORAGE_CONNECTION_STRING
        )
        blob_client = blob_service_client.get_blob_client(
            container=CONTAINER_NAME, blob=uploaded_file.name
        )
        blob_client.upload_blob(uploaded_file.getvalue(), overwrite=True)
        return True, "Upload successful"
    except Exception as e:
        return False, f"Upload failed: {str(e)}"


# SIDEBAR - PDF Upload
with st.sidebar:
    st.header("📄 Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        if st.button("Process PDF"):
            with st.spinner("Uploading and processing..."):
                success, message = upload_pdf_to_blob(uploaded_file)
                if success:
                    st.success(f"✅ {uploaded_file.name} uploaded successfully!")
                    st.info("Processing will complete in the background.")
                else:
                    st.error(f"❌ {message}")

# MAIN CHAT INTERFACE
# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
prompt = st.chat_input("What's your Question?")

if prompt:
    # Add user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get and display assistant response
    answer = query_backend(prompt)
    st.chat_message("assistant").markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
