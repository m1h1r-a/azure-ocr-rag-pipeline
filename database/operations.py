import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional


class DatabaseOperations:
    """Handles database insert operations"""

    def __init__(self, connection, cursor):
        """Initialize with database connection and cursor"""
        self.conn = connection
        self.cursor = cursor
        self.logger = logging.getLogger(__name__)

    def truncate_string(self, value: Any, max_length: int) -> Optional[str]:
        """Truncate string to fit database column size - same as original"""
        if value is None:
            return None
        str_value = str(value)
        if len(str_value) > max_length:
            self.logger.warning(
                f"⚠️ Truncating '{str_value}' to {max_length} characters"
            )
            return str_value[:max_length]
        return str_value

    def format_date_field(self, date_str: Any) -> Optional[str]:
        """Convert date string to SQL Server format or return None - same as original"""
        if not date_str or date_str == "null":
            return None
        try:
            # Try to parse common date formats and convert to YYYY-MM-DD
            # Try MM/DD/YYYY format first
            if "/" in str(date_str):
                parsed_date = datetime.strptime(str(date_str), "%m/%d/%Y")
                return parsed_date.strftime("%Y-%m-%d")
            # Try YYYY-MM-DD format
            elif "-" in str(date_str):
                parsed_date = datetime.strptime(str(date_str), "%Y-%m-%d")
                return parsed_date.strftime("%Y-%m-%d")
            else:
                return None
        except ValueError:
            self.logger.warning(f"Could not parse date: {date_str}")
            return None

    def insert_all_data(
        self,
        extracted_data: Dict[str, Any],
        extracted_text: str,
        filename: str,
        accuracy: float,
    ) -> None:
        """
        Insert all data into database tables - exact same logic as original

        Args:
            extracted_data: Extracted healthcare data
            extracted_text: Raw extracted text
            filename: Name of the file
            accuracy: Calculated accuracy percentage
        """
        try:
            self.logger.info("💾 Starting database insertion...")

            # Get current timestamp - same formatting as original
            current_time = datetime.now()
            formatted_datetime = current_time.strftime("%Y-%m-%d %H:%M:%S")
            formatted_date = current_time.strftime("%Y-%m-%d")
            formatted_time = current_time.strftime("%H:%M:%S")

            # 1. Insert into Documents table - same as original
            self.cursor.execute(
                """
                INSERT INTO Documents (Filename, DocumentType, ProcessingStatus, RawText, CreatedDate)
                VALUES (%s, %s, %s, %s, %s)
            """,
                (
                    self.truncate_string(filename, 255),
                    self.truncate_string(
                        extracted_data.get("document_type", "Unknown"), 50
                    ),
                    "Processed" if accuracy >= 50 else "Exception",
                    extracted_text[:4000],  # Limit text length
                    formatted_datetime,
                ),
            )

            # Get the inserted DocumentID - same as original
            self.cursor.execute("SELECT @@IDENTITY as DocumentID")
            document_row = self.cursor.fetchone()
            document_id = int(document_row["DocumentID"])
            self.logger.info(f"✅ Document inserted with ID: {document_id}")

            # 2. Insert into Patients table (if we have patient data) - same as original
            if (
                extracted_data.get("patient_name")
                and extracted_data.get("patient_name") != "null"
            ):

                # Format dates - same as original
                formatted_dob = self.format_date_field(extracted_data.get("dob"))
                formatted_admission = self.format_date_field(
                    extracted_data.get("admission_date")
                )
                formatted_discharge = self.format_date_field(
                    extracted_data.get("discharge_date")
                )

                self.cursor.execute(
                    """
                    INSERT INTO Patients (PatientName, MedicalRecordNumber, DateOfBirth, 
                                        PrimaryDiagnosis, AdmissionDate, DischargeDate, 
                                        AttendingPhysician, FacilityName, DocumentID)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        self.truncate_string(extracted_data.get("patient_name"), 100),
                        self.truncate_string(extracted_data.get("mrn"), 50),
                        formatted_dob,
                        self.truncate_string(
                            extracted_data.get("primary_diagnosis"), 200
                        ),
                        formatted_admission,
                        formatted_discharge,
                        self.truncate_string(extracted_data.get("physician"), 100),
                        self.truncate_string(extracted_data.get("facility"), 100),
                        document_id,
                    ),
                )

                # Get PatientID - same as original
                self.cursor.execute("SELECT @@IDENTITY as PatientID")
                patient_row = self.cursor.fetchone()
                patient_id = int(patient_row["PatientID"])
                self.logger.info(f"✅ Patient inserted with ID: {patient_id}")

                # 3. Insert into Insurance table (if we have insurance data) - same as original
                if (
                    extracted_data.get("insurance_company")
                    and extracted_data.get("insurance_company") != "null"
                ):

                    self.cursor.execute(
                        """
                        INSERT INTO Insurance (PatientID, InsuranceCompany, DocumentID)
                        VALUES (%s, %s, %s)
                    """,
                        (
                            patient_id,
                            self.truncate_string(
                                extracted_data.get("insurance_company"), 100
                            ),
                            document_id,
                        ),
                    )
                    self.logger.info("✅ Insurance data inserted")

            # 4. Insert into ProcessTable or ExceptionTable - same as original
            document_type = extracted_data.get("document_type", "Unknown")

            if accuracy >= 50:
                self.cursor.execute(
                    """
                    INSERT INTO ProcessTable (FileName, Accuracy, Status, Type, 
                                            IngestedDate, IngestedTime, DocumentID)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        self.truncate_string(filename, 255),
                        accuracy,
                        "Success",
                        self.truncate_string(document_type, 50),
                        formatted_date,
                        formatted_time,
                        document_id,
                    ),
                )
                self.logger.info("✅ Record added to ProcessTable")
            else:
                self.cursor.execute(
                    """
                    INSERT INTO ExceptionTable (FileName, Accuracy, Status, Type, 
                                            IngestedDate, IngestedTime, ErrorDetails, 
                                            RawExtractedData, DocumentID)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        self.truncate_string(filename, 255),
                        accuracy,
                        "Low_Accuracy",
                        self.truncate_string(document_type, 15),
                        formatted_date,
                        formatted_time,
                        f"Low accuracy: {accuracy}% - Missing required fields",
                        json.dumps(extracted_data)[:1000],  # Truncate JSON if too long
                        document_id,
                    ),
                )
                self.logger.info("✅ Record added to ExceptionTable")

            # Commit all changes - same as original
            self.conn.commit()
            self.logger.info("🎉 DATABASE INSERTION COMPLETED SUCCESSFULLY!")

        except Exception as db_insert_error:
            self.logger.error(f"❌ Database insertion failed: {str(db_insert_error)}")
            self.conn.rollback()  # Rollback on error
            raise db_insert_error

    def close_connection(self):
        """Close database connection - same as original"""
        if self.conn:
            self.conn.close()
            self.logger.info("🔐 Database connection closed")
