import json
import logging
import os

import azure.functions as func

from database import DatabaseConnection, DatabaseOperations
from processors import DataValidator, DocumentIntelligenceProcessor, OpenAIExtractor

# Configure logging properly for Azure Functions
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = func.FunctionApp()


@app.blob_trigger(
    arg_name="myblob",
    path="pdfs/{name}",
    connection="pdfstorageci0001_STORAGE",
)
def ProcessPdfBlob(myblob: func.InputStream):
    logger.info(f"Python blob trigger function processed blob")
    logger.info(f"Name: {myblob.name}")
    logger.info(f"Blob Size: {myblob.length} bytes")

    try:
        # Extract filename from blob path
        filename = myblob.name.split("/")[-1]  # Gets filename from 'pdfs/filename.pdf'

        # === STEP 1: Document Intelligence - Extract Text ===
        doc_processor = DocumentIntelligenceProcessor()
        blob_data = myblob.read()
        extracted_text = doc_processor.extract_text(blob_data, filename)

        # === STEP 2: OpenAI - Structure the Data ===
        openai_extractor = OpenAIExtractor()
        extracted_data = openai_extractor.extract_data(extracted_text, filename)

        # === STEP 3: Validate Data ===
        validator = DataValidator()
        accuracy, is_success = validator.validate_data(extracted_data)

        # === STEP 4: Database Operations ===
        try:
            db_connection = DatabaseConnection()
            conn, cursor = db_connection.connect_with_retry()

            if conn and cursor:
                try:
                    db_operations = DatabaseOperations(conn, cursor)
                    db_operations.insert_all_data(
                        extracted_data, extracted_text, filename, accuracy
                    )
                finally:
                    # Always close connection
                    db_operations.close_connection()
        except Exception as db_error:
            logger.error(f"❌ Database operation failed: {str(db_error)}")
            logger.error(f"Error type: {type(db_error).__name__}")

    except Exception as e:
        logger.error(f"❌ Error in PDF processing pipeline: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise e
