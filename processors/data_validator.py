import logging
from typing import Any, Dict, Tuple


class DataValidator:

    def __init__(self):
        self.required_fields = ["patient_name", "mrn", "primary_diagnosis"]
        self.logger = logging.getLogger(__name__)

    def validate_data(self, extracted_data: Dict[str, Any]) -> Tuple[float, bool]:
        found_fields = sum(
            1
            for field in self.required_fields
            if extracted_data.get(field) and extracted_data[field] != "null"
        )

        # Calculate accuracy (same as original)
        accuracy = (found_fields / len(self.required_fields)) * 100

        # Log results (same format as original)
        self.logger.info(
            f"📊 Extraction accuracy: {accuracy:.1f}% ({found_fields}/{len(self.required_fields)} required fields)"
        )

        # Determine success (same threshold as original)
        is_success = accuracy >= 90

        if is_success:
            self.logger.info("✅ EXTRACTION SUCCESSFUL - Ready for database storage")
        else:
            self.logger.warning("⚠️ LOW ACCURACY - Would be stored in ExceptionTable")

        return accuracy, is_success
