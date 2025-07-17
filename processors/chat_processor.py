import json
import logging

from database import DatabaseConnection, DatabaseOperations, RetreiveData

from .openai_extractor import OpenAIExtractor


class ChatProcessor:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_message(self, user_message: str) -> str:

        self.logger.info(f"💬 User message: {user_message}")
        self.openai_extractor = OpenAIExtractor()
        self.retreive_data = RetreiveData()
        self.intent = ""
        self.parameter = ""

        intent = self._identify_intent(user_message)

        if self.intent == "patient_lookup":
            query_results = self.retreive_data._get_patient_by_name(self.parameter)
        else:
            query_results = {
                "status": "unsupported",
                "message": f"Intent '{self.intent}' not implemented yet",
            }

        response = self._generate_response(user_message, query_results)
        return response

    def _identify_intent(self, message: str):

        extracted_data = self.openai_extractor.extract_intent(message)
        self.intent = extracted_data["intent"]
        self.parameter = extracted_data["parameter"]

        self.logger.info(f"Intent: {self.intent}")
        self.logger.info(f"Parameter: {self.parameter}")
        return extracted_data

    def _generate_response(self, query, query_results: dict) -> str:

        try:

            if query_results["status"] == "error":
                return f"Sorry, I encountered an error: {query_results['message']}"
            if query_results["status"] == "unsupported":
                return query_results["message"]

            response = self.openai_extractor.format_response(query, query_results)
            return response

        except Exception as e:
            self.logger.error(f"Unable to generate response: {e}")
            return "Unable to generate response, try again later"
