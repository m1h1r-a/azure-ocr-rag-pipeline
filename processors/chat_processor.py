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

        if self.intent == "patient_lookup":
            query_results = self._get_patient_by_name(self.parameter)
        else:
            query_results = {
                "status": "unsupported",
                "message": f"Intent '{self.intent}' not implemented yet",
            }

        return query_results

    def _identify_intent(self, message: str):

        openai_extractor = OpenAIExtractor()
        extracted_data = openai_extractor.extract_intent(message)
        self.intent = extracted_data["intent"]
        self.parameter = extracted_data["parameter"]

        self.logger.info(f"Intent: {self.intent}")
        self.logger.info(f"Parameter: {self.parameter}")
        return extracted_data

    def _get_patient_by_name(self, name: str) -> dict:
        """Query database for patient by name"""
        try:
            self.logger.info(f"🔍 Searching for patient: {name}")

            # Connect to database
            db_connection = DatabaseConnection()
            conn, cursor = db_connection.connect_with_retry()

            if not conn or not cursor:
                return {"status": "error", "message": "Database connection failed"}

            # Query patients table with LIKE for partial matches
            query = """
            SELECT p.PatientName, p.MedicalRecordNumber, p.DateOfBirth, 
                   p.PrimaryDiagnosis, p.AdmissionDate, p.DischargeDate,
                   p.AttendingPhysician, p.FacilityName,
                   i.InsuranceCompany
            FROM Patients p
            LEFT JOIN Insurance i ON p.PatientID = i.PatientID
            WHERE p.PatientName LIKE %s
            """

            cursor.execute(query, (f"%{name}%",))
            results = cursor.fetchall()

            # Close connection
            conn.close()

            self.logger.info(f"✅ Found {len(results)} patients matching '{name}'")

            return {
                "status": "success",
                "data": results,
                "count": len(results),
                "query_type": "patient_lookup",
            }

        except Exception as e:
            self.logger.error(f"❌ Patient lookup failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _generate_response(self, query_results: dict) -> str:
        pass

    def _get_patient_by_mrn(self, mrn: str) -> dict:
        # Query database for patient by MRN
        pass

    def _get_patients_by_diagnosis(self, diagnosis: str) -> list:
        # Query database for patients with specific diagnosis
        pass
