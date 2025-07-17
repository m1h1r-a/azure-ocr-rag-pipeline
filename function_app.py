import json
import logging
import os

import azure.functions as func

from database import DatabaseConnection, DatabaseOperations
from processors import (
    ChatProcessor,
    DataValidator,
    DocumentIntelligenceProcessor,
    OpenAIExtractor,
)

# Configure logging properly for Azure Functions
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = func.FunctionApp()


@app.blob_trigger(
    arg_name="myblob", path="pdfs/{name}", connection="pdfstorageci0001_STORAGE"
)
def ProcessPdfBlob(myblob: func.InputStream):
    logger.info(f"Python blob trigger function processed blob")
    logger.info(f"Name: {myblob.name}")
    logger.info(f"Blob Size: {myblob.length} bytes")

    try:
        # extract file name
        filename = myblob.name.split("/")[-1]  # Gets filename from 'pdfs/filename.pdf'

        # extract text with doc intelligence
        doc_processor = DocumentIntelligenceProcessor()
        blob_data = myblob.read()
        extracted_text = doc_processor.extract_text(blob_data, filename)

        # structure data with ai
        openai_extractor = OpenAIExtractor()
        extracted_data = openai_extractor.extract_data(extracted_text, filename)

        # validate results
        validator = DataValidator()
        accuracy, is_success = validator.validate_data(extracted_data)

        # db
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
                    db_operations.close_connection()

        except Exception as db_error:
            logger.error(f"❌ Database operation failed: {str(db_error)}")
            logger.error(f"Error type: {type(db_error).__name__}")

    except Exception as e:
        logger.error(f"❌ Error in PDF processing pipeline: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise e


@app.route(route="chat", methods=["POST"])
def chat_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    logger.info("🤖 Chat endpoint triggered")

    try:
        req_body = req.get_json()

        if not req_body or "message" not in req_body:
            return func.HttpResponse(
                json.dumps(
                    {
                        "error": "Missing 'message' field in request body",
                        "status": "error",
                    }
                ),
                status_code=400,
                mimetype="application/json",
            )

        user_message = req_body["message"]

        chat_processor = ChatProcessor()
        response_data = chat_processor.process_message(user_message)

        return func.HttpResponse(
            json.dumps(response_data, default=str),
            status_code=200,
            mimetype="application/json",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    except Exception as e:
        logger.error(f"❌ Chat endpoint error: {str(e)}")

        error_response = {
            "status": "error",
            "error": str(e),
            "formatted_response": "Sorry, I encountered an error. Please try again.",
        }

        return func.HttpResponse(
            json.dumps(error_response, default=str),
            status_code=500,
            mimetype="application/json",
        )
