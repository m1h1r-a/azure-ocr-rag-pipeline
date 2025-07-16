import json
import logging

from database import DatabaseConnection, DatabaseOperations

from .openai_extractor import OpenAIExtractor


class ChatProcessor:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_message(self, user_message: str) -> dict:

        self.logger.info(f"💬 User message: {user_message}")
        self.intent = ""
        self.parameter = ""

        intent = self._identify_intent(user_message)

        # test_response_data = {
        #     "status": "success",
        #     "user_message": user_message,
        #     "formatted_response": f"You asked: {user_message}. Chat functionality will be implemented next!",
        #     "data": None,
        #     "timestamp": "2025-07-15T12:00:00Z",
        # }

        self.logger.info("✅ Chat response generated successfully")

        return intent

    def _identify_intent(self, message: str):

        openai_extractor = OpenAIExtractor()
        extracted_data = openai_extractor.extract_intent(message)
        self.logger.info(f"Type of Returned JSON: {type(extracted_data)}")
        self.logger.info(extracted_data)
        return extracted_data

    def _extract_parameters(self, message: str, intent: str) -> dict:
        # Extract specific values from the message
        # Example: "Show me John Doe" → {"name": "John Doe"}
        pass

    def _get_patient_by_name(self, name: str) -> dict:
        # Query database for patient by name
        pass

    def _get_patient_by_mrn(self, mrn: str) -> dict:
        # Query database for patient by MRN
        pass

    def _get_patients_by_diagnosis(self, diagnosis: str) -> list:
        # Query database for patients with specific diagnosis
        pass
