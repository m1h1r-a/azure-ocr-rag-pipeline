import json
import logging

from database import DatabaseConnection, DatabaseOperations, RetreiveData

from .openai_extractor import OpenAIExtractor


class ChatProcessor:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_message(self, user_message: str) -> dict:

        self.logger.info(f"💬 User message: {user_message}")
        self.openai_extractor = OpenAIExtractor()
        self.retreive_data = RetreiveData()
        self.intent = ""
        self.parameter = ""

        intent = self._identify_intent(user_message)

        if self.intent == "patient_lookup":
            query_results = self.retreive_data._get_patient_by_name(self.parameter)
        elif self.intent == "mrn_lookup":
            query_results = self.retreive_data._get_patient_by_mrn(self.parameter)
        elif self.intent == "diagnosis_search":
            query_results = self.retreive_data._get_patients_by_diagnosis(
                self.parameter
            )
        elif self.intent == "physician_search":
            query_results = self.retreive_data._get_patients_by_physician(
                self.parameter
            )
        elif self.intent == "insurance_search":
            query_results = self.retreive_data._get_patients_by_insurance(
                self.parameter
            )
        elif self.intent == "document_search":
            query_results = self.retreive_data._get_documents_search(self.parameter)
        elif self.intent == "stats_summary":
            query_results = self.retreive_data._get_stats_summary(self.parameter)
        else:
            query_results = {
                "status": "unsupported",
                "message": f"Intent '{self.intent}' not recognized or supported yet",
            }

        response = self._generate_response(user_message, query_results)

        return {
            "status": "success",
            "user_message": user_message,
            "intent": self.intent,
            "parameter": self.parameter,
            "formatted_response": response,
            "data": query_results.get("data", []),
            "count": query_results.get("count", 0),
        }

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

            # Intents that need OpenAI formatting (complex, narrative responses)
            openai_intents = [
                "patient_lookup",
                "diagnosis_search",
                "physician_search",
            ]

            if self.intent in openai_intents:
                response = self.openai_extractor.format_response(query, query_results)
                return response
            else:
                return self._format_simple_response(query_results)

        except Exception as e:
            self.logger.error(f"Unable to generate response: {e}")
            return "Unable to generate response, try again later"

    def _format_simple_response(self, query_results: dict) -> str:
        """Template-based formatting for simple responses"""

        if query_results["count"] == 0:
            # TODO: Make AI generate the query?
            return "No results found for your query."

        if self.intent == "mrn_lookup":
            if query_results["count"] > 0:
                patient = query_results["data"][0]
                name = patient.get("PatientName", "Unknown")
                mrn = patient.get("MedicalRecordNumber", "Unknown")
                diagnosis = patient.get("PrimaryDiagnosis", "No diagnosis listed")
                admission = patient.get("AdmissionDate", "Unknown date")
                return (
                    f"Patient {name} (MRN: {mrn}) - {diagnosis}. Admitted: {admission}"
                )

        elif self.intent == "insurance_search":
            count = query_results["count"]
            return f"Found {count} patients with the specified insurance company."

        elif self.intent == "document_search":
            count = query_results["count"]
            if count > 0:
                doc_types = list(
                    set(
                        [
                            doc.get("DocumentType", "Unknown")
                            for doc in query_results["data"]
                            if doc.get("DocumentType")
                        ]
                    )
                )
                types_str = ", ".join(doc_types[:3])  # Show first 3 types
                return f"Found {count} documents. Document types include: {types_str}"
            return f"Found {count} documents matching your search."

        elif self.intent == "stats_summary":
            data = query_results["data"]
            total_patients = data.get("total_patients", 0)
            total_docs = data.get("total_documents", 0)
            top_diagnosis = data.get("top_diagnosis", "No data")
            return f"Database contains {total_patients} patients and {total_docs} processed documents. Top diagnosis: {top_diagnosis}"

        # Default fallback
        return f"Found {query_results['count']} results for your query."
