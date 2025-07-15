import json
import logging
import os
from typing import Any, Dict

from openai import AzureOpenAI


class OpenAIExtractor:
    """Extracts structured healthcare data using Azure OpenAI"""

    def __init__(self):
        """Initialize the OpenAI client"""
        self.endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.key = os.environ.get("AZURE_OPENAI_KEY")

        if not self.endpoint or not self.key:
            raise ValueError(
                "Azure OpenAI credentials not found in environment variables"
            )

        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.key,
            api_version="2025-01-01-preview",
        )

        self.logger = logging.getLogger(__name__)

        # Healthcare extraction prompt template
        self.healthcare_prompt_template = """
        You are a healthcare data extraction specialist. Extract patient information from the following medical document text and return it as a JSON object.

        Instructions:
        1. Extract ALL available information, even if some fields are missing, but do not make up any data.
        2. Use "null" for missing information
        3. Keep original formatting for names and text
        4. For dates, use MM/DD/YYYY format when possible
        5. Return only valid JSON, no additional text

        Required JSON structure:
        {{
          "patient_name": "string or null",
          "mrn": "string or null", 
          "dob": "string or null",
          "admission_date": "string or null",
          "discharge_date": "string or null",
          "primary_diagnosis": "string or null",
          "physician": "string or null",
          "insurance_company": "string or null",
          "facility": "string or null",
          "document_type": "string or null"
        }}

        Document text to analyze:
        {document_text}
        """

    def extract_data(
        self, document_text: str, filename: str = "unknown"
    ) -> Dict[str, Any]:
        try:
            self.logger.info(f"🤖 Starting data extraction for: {filename}")

            # Create the prompt
            prompt = self.healthcare_prompt_template.format(document_text=document_text)

            # Call OpenAI
            response = self.client.chat.completions.create(
                model="healthcare-extractor",  # Your deployment name
                messages=[
                    {
                        "role": "system",
                        "content": "You are a healthcare data extraction expert. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.1,  # Low temperature for consistent extraction
            )

            # Get response content
            openai_response = response.choices[0].message.content
            self.logger.info(
                f"✅ OpenAI response received: {len(openai_response)} characters"
            )

            # Parse JSON
            try:
                extracted_data = json.loads(openai_response)

                # Log extracted data
                self.logger.info("🎯 EXTRACTED HEALTHCARE DATA:")
                for key, value in extracted_data.items():
                    self.logger.info(f"  {key}: {value}")

                return extracted_data

            except json.JSONDecodeError as json_error:
                self.logger.error(f"❌ JSON parsing failed: {str(json_error)}")
                self.logger.error(f"OpenAI response was: {openai_response}")
                raise json_error

        except Exception as e:
            self.logger.error(f"❌ Data extraction failed for {filename}: {str(e)}")
            raise e
