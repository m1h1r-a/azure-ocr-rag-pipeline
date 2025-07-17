import logging
from datetime import datetime, timedelta

from . import DatabaseConnection


class RetreiveData:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _get_patient_by_name(self, name: str) -> dict:
        """Query database for patient by name"""
        conn = None
        try:
            self.logger.info(f"🔍 Searching for patient: {name}")

            db_connection = DatabaseConnection()
            conn, cursor = db_connection.connect_with_retry()

            if not conn or not cursor:
                return {"status": "error", "message": "Database connection failed"}

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

        finally:
            if conn:
                conn.close()
                self.logger.info("🔐 Database connection closed")

    def _get_patient_by_mrn(self, mrn: str) -> dict:
        """Query database for patient by MRN"""
        conn = None
        try:
            self.logger.info(f"🔍 Searching for patient with MRN: {mrn}")

            db_connection = DatabaseConnection()
            conn, cursor = db_connection.connect_with_retry()

            if not conn or not cursor:
                return {"status": "error", "message": "Database connection failed"}

            query = """
            SELECT p.PatientName, p.MedicalRecordNumber, p.DateOfBirth, 
                   p.PrimaryDiagnosis, p.AdmissionDate, p.DischargeDate,
                   p.AttendingPhysician, p.FacilityName,
                   i.InsuranceCompany
            FROM Patients p
            LEFT JOIN Insurance i ON p.PatientID = i.PatientID
            WHERE p.MedicalRecordNumber = %s
            """

            cursor.execute(query, (mrn,))
            results = cursor.fetchall()

            self.logger.info(f"✅ Found {len(results)} patients with MRN '{mrn}'")

            return {
                "status": "success",
                "data": results,
                "count": len(results),
                "query_type": "mrn_lookup",
            }

        except Exception as e:
            self.logger.error(f"❌ MRN lookup failed: {str(e)}")
            return {"status": "error", "message": str(e)}

        finally:
            if conn:
                conn.close()
                self.logger.info("🔐 Database connection closed")

    def _get_patients_by_diagnosis(self, diagnosis: str) -> dict:
        """Query database for patients with specific diagnosis"""
        conn = None
        try:
            self.logger.info(f"🔍 Searching for patients with diagnosis: {diagnosis}")

            db_connection = DatabaseConnection()
            conn, cursor = db_connection.connect_with_retry()

            if not conn or not cursor:
                return {"status": "error", "message": "Database connection failed"}

            query = """
            SELECT p.PatientName, p.MedicalRecordNumber, p.DateOfBirth, 
                   p.PrimaryDiagnosis, p.AdmissionDate, p.DischargeDate,
                   p.AttendingPhysician, p.FacilityName,
                   i.InsuranceCompany
            FROM Patients p
            LEFT JOIN Insurance i ON p.PatientID = i.PatientID
            WHERE p.PrimaryDiagnosis LIKE %s
            """

            cursor.execute(query, (f"%{diagnosis}%",))
            results = cursor.fetchall()

            self.logger.info(
                f"✅ Found {len(results)} patients with diagnosis '{diagnosis}'"
            )

            return {
                "status": "success",
                "data": results,
                "count": len(results),
                "query_type": "diagnosis_search",
            }

        except Exception as e:
            self.logger.error(f"❌ Diagnosis search failed: {str(e)}")
            return {"status": "error", "message": str(e)}

        finally:
            if conn:
                conn.close()
                self.logger.info("🔐 Database connection closed")

    def _get_patients_by_physician(self, physician: str) -> dict:
        """Query database for patients treated by specific physician"""
        conn = None
        try:
            self.logger.info(f"🔍 Searching for patients treated by: {physician}")

            db_connection = DatabaseConnection()
            conn, cursor = db_connection.connect_with_retry()

            if not conn or not cursor:
                return {"status": "error", "message": "Database connection failed"}

            query = """
            SELECT p.PatientName, p.MedicalRecordNumber, p.DateOfBirth, 
                   p.PrimaryDiagnosis, p.AdmissionDate, p.DischargeDate,
                   p.AttendingPhysician, p.FacilityName,
                   i.InsuranceCompany
            FROM Patients p
            LEFT JOIN Insurance i ON p.PatientID = i.PatientID
            WHERE p.AttendingPhysician LIKE %s
            """

            cursor.execute(query, (f"%{physician}%",))
            results = cursor.fetchall()

            self.logger.info(
                f"✅ Found {len(results)} patients treated by '{physician}'"
            )

            return {
                "status": "success",
                "data": results,
                "count": len(results),
                "query_type": "physician_search",
            }

        except Exception as e:
            self.logger.error(f"❌ Physician search failed: {str(e)}")
            return {"status": "error", "message": str(e)}

        finally:
            if conn:
                conn.close()
                self.logger.info("🔐 Database connection closed")

    def _get_patients_by_insurance(self, insurance: str) -> dict:
        """Query database for patients with specific insurance"""
        conn = None
        try:
            self.logger.info(f"🔍 Searching for patients with insurance: {insurance}")

            db_connection = DatabaseConnection()
            conn, cursor = db_connection.connect_with_retry()

            if not conn or not cursor:
                return {"status": "error", "message": "Database connection failed"}

            query = """
            SELECT p.PatientName, p.MedicalRecordNumber, p.DateOfBirth, 
                   p.PrimaryDiagnosis, p.AdmissionDate, p.DischargeDate,
                   p.AttendingPhysician, p.FacilityName,
                   i.InsuranceCompany
            FROM Patients p
            INNER JOIN Insurance i ON p.PatientID = i.PatientID
            WHERE i.InsuranceCompany LIKE %s
            """

            cursor.execute(query, (f"%{insurance}%",))
            results = cursor.fetchall()

            self.logger.info(
                f"✅ Found {len(results)} patients with insurance '{insurance}'"
            )

            return {
                "status": "success",
                "data": results,
                "count": len(results),
                "query_type": "insurance_search",
            }

        except Exception as e:
            self.logger.error(f"❌ Insurance search failed: {str(e)}")
            return {"status": "error", "message": str(e)}

        finally:
            if conn:
                conn.close()
                self.logger.info("🔐 Database connection closed")

    def _get_documents_search(self, search_param: str) -> dict:
        """Query database for documents by type or filename"""
        conn = None
        try:
            self.logger.info(f"🔍 Searching for documents: {search_param}")

            db_connection = DatabaseConnection()
            conn, cursor = db_connection.connect_with_retry()

            if not conn or not cursor:
                return {"status": "error", "message": "Database connection failed"}

            query = """
            SELECT d.Filename, d.DocumentType, d.ProcessingStatus, d.CreatedDate,
                   pt.Accuracy, pt.Status
            FROM Documents d
            LEFT JOIN ProcessTable pt ON d.DocumentID = pt.DocumentID
            WHERE d.DocumentType LIKE %s OR d.Filename LIKE %s
            """

            search_pattern = f"%{search_param}%"
            cursor.execute(query, (search_pattern, search_pattern))
            results = cursor.fetchall()

            self.logger.info(
                f"✅ Found {len(results)} documents matching '{search_param}'"
            )

            return {
                "status": "success",
                "data": results,
                "count": len(results),
                "query_type": "document_search",
            }

        except Exception as e:
            self.logger.error(f"❌ Document search failed: {str(e)}")
            return {"status": "error", "message": str(e)}

        finally:
            if conn:
                conn.close()
                self.logger.info("🔐 Database connection closed")

    def _get_stats_summary(self, param: str) -> dict:
        """Query database for basic statistics"""
        conn = None
        try:
            self.logger.info(f"🔍 Getting statistics summary")

            db_connection = DatabaseConnection()
            conn, cursor = db_connection.connect_with_retry()

            if not conn or not cursor:
                return {"status": "error", "message": "Database connection failed"}

            # Get basic counts
            stats = {}

            # Total patients
            cursor.execute("SELECT COUNT(*) as total_patients FROM Patients")
            result = cursor.fetchone()
            stats["total_patients"] = result["total_patients"]

            # Total documents
            cursor.execute("SELECT COUNT(*) as total_documents FROM Documents")
            result = cursor.fetchone()
            stats["total_documents"] = result["total_documents"]

            # Top diagnosis
            cursor.execute(
                """
                SELECT TOP 1 PrimaryDiagnosis, COUNT(*) as count 
                FROM Patients 
                WHERE PrimaryDiagnosis IS NOT NULL 
                GROUP BY PrimaryDiagnosis 
                ORDER BY count DESC
            """
            )
            result = cursor.fetchone()
            if result:
                stats["top_diagnosis"] = (
                    f"{result['PrimaryDiagnosis']} ({result['count']} cases)"
                )
            else:
                stats["top_diagnosis"] = "No diagnosis data"

            self.logger.info(f"✅ Retrieved statistics summary")

            return {
                "status": "success",
                "data": stats,
                "count": 1,
                "query_type": "stats_summary",
            }

        except Exception as e:
            self.logger.error(f"❌ Stats summary failed: {str(e)}")
            return {"status": "error", "message": str(e)}

        finally:
            if conn:
                conn.close()
                self.logger.info("🔐 Database connection closed")
