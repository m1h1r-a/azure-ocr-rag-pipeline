import logging

from . import DatabaseConnection


class RetreiveData:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.db_connection = DatabaseConnection()
        self.con, self.cursor = self.db_connection.connect_with_retry()

    def _get_patient_by_name(self, name: str) -> dict:
        """Query database for patient by name"""
        try:
            self.logger.info(f"🔍 Searching for patient: {name}")

            if not self.con or not self.cursor:
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

            self.cursor.execute(query, (f"%{name}%",))
            results = self.cursor.fetchall()

            # Close connection
            self.con.close()

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

    def _get_patient_by_mrn(self, mrn: str) -> dict:
        # Query database for patient by MRN
        pass

    def _get_patients_by_diagnosis(self, diagnosis: str) -> list:
        # Query database for patients with specific diagnosis
        pass
