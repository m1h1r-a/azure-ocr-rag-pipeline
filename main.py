import json
import logging
import os
import sys

from azure.storage.blob import BlobServiceClient
from flask import Flask, jsonify, request

from database import DatabaseConnection, DatabaseOperations
from processors import DataValidator, DocumentIntelligenceProcessor, OpenAIExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def load_local_settings():
    """Load environment variables from local.settings.json"""
    try:
        with open("local.settings.json", "r") as f:
            settings = json.load(f)
            for key, value in settings["Values"].items():
                os.environ[key] = value
        logger.info("✅ Loaded environment variables from local.settings.json")
    except Exception as e:
        logger.error(f"❌ Failed to load local.settings.json: {str(e)}")
        raise


# Load settings at startup
load_local_settings()


# Simple health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


@app.route("/process-pdf", methods=["POST"])
def process_pdf():
    """Main processing endpoint - almost identical to your ProcessPdfBlob function"""

    data = request.get_json()
    blob_url = data.get("blob_url")

    if not blob_url:
        return jsonify({"error": "Missing blob_url"}), 400

    logger.info(f"Processing blob: {blob_url}")

    try:
        connection_string = os.environ.get("pdfstorage0001_STORAGE")
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )

        parts = blob_url.split("/")
        container_name = parts[-2]  # 'pdfs'
        filename = parts[-1]  # 'filename.pdf'

        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=filename
        )
        blob_data = blob_client.download_blob().readall()

        logger.info(f"Downloaded {len(blob_data)} bytes for {filename}")

        # STEP 1: Document Intelligence - Extract Text
        doc_processor = DocumentIntelligenceProcessor()
        extracted_text = doc_processor.extract_text(blob_data, filename)

        # STEP 2: OpenAI - Structure the Data
        openai_extractor = OpenAIExtractor()
        extracted_data = openai_extractor.extract_data(extracted_text, filename)

        # STEP 3: Validate Data
        validator = DataValidator()
        accuracy, is_success = validator.validate_data(extracted_data)

        # STEP 4: Database Operations
        try:
            db_connection = DatabaseConnection()
            conn, cursor = db_connection.connect_with_retry()

            if conn and cursor:
                try:
                    db_operations = DatabaseOperations(conn, cursor)
                    db_operations.insert_all_data(
                        extracted_data, extracted_text, filename, accuracy
                    )
                    logger.info("✅ Processing completed successfully!")
                    return jsonify(
                        {
                            "status": "success",
                            "filename": filename,
                            "accuracy": accuracy,
                        }
                    )
                finally:
                    db_operations.close_connection()
        except Exception as db_error:
            logger.error(f"❌ Database operation failed: {str(db_error)}")
            return jsonify({"error": f"Database error: {str(db_error)}"}), 500

    except Exception as e:
        logger.error(f"❌ Error in PDF processing pipeline: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Check environment variables (same ones from your local.settings.json)
    required_vars = [
        "DOCUMENT_INTELLIGENCE_ENDPOINT",
        "AZURE_OPENAI_ENDPOINT",
        "SQL_CONNECTION_STRING",
        "pdfstorage0001_STORAGE",  # Same as your Azure Functions
    ]

    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        sys.exit(1)

    logger.info("✅ All required environment variables present")

    # Start Flask app
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
