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
        intent_list = self._identify_intent(user_message)

        all_results = []
        total_count = 0
        all_data = []

        for intent_pair in intent_list:
            self.intent = list(intent_pair.keys())[0]
            self.parameter = intent_pair[self.intent]

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

            all_results.append(query_results)
            if query_results.get("count"):
                total_count += query_results["count"]
            if query_results.get("data"):
                all_data.extend(query_results["data"])

        combined_query_results = {
            "status": "success",
            "data": all_data,
            "count": total_count,
            "all_results": all_results,
        }

        response = self._generate_response(user_message, combined_query_results)

        return {
            "status": "success",
            "user_message": user_message,
            "formatted_response": response,
            "data": all_data,
            "count": total_count,
        }

    def _identify_intent(self, message: str):
        extracted_data = self.openai_extractor.extract_intent(message)
        self.logger.info(extracted_data)
        return extracted_data

    def _generate_response(self, query, query_results: dict) -> str:

        try:
            if query_results["status"] == "error":
                return f"Sorry, I encountered an error: {query_results['message']}"
            if query_results["status"] == "unsupported":
                return query_results["message"]

            openai_intents = [
                "patient_lookup",
                "diagnosis_search",
                "physician_search",
            ]

            if len(query_results["all_results"]) > 1 or self.intent in openai_intents:
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
