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

        self.intent_detection_template = """
        You are a query intent detection specialist. Extract the intent from the following query and return it as a JSON object.

        Instructions To Detect Intent:
        1. Extract the most likely intent
        2. Intent will be of the following categories, return only the category name:
           a) "patient_lookup" : If the query is related to finding details about a specific patient by giving their name
              Examples: "Show me John Doe", "Find patient Jane Smith", "Look up Mary Johnson"
           
           b) "diagnosis_search" : If the query is related to finding patients with a specific diagnosis or condition
              Examples: "Show diabetes patients", "Find all pneumonia cases", "List heart disease patients"
           
           c) "mrn_lookup" : If the query provides an MRN (Medical Record Number) to look up a patient
              Examples: "Look up MRN 12345", "Find patient with record number 67890", "Show MRN A1B2C3"
           
           d) "facility_search" : If the query is about finding patients or information from a specific healthcare facility
              Examples: "Show patients from General Hospital", "Find admissions at City Medical Center", "List patients at Mayo Clinic"
           
           e) "physician_search" : If the query is about finding patients treated by a specific doctor or physician
              Examples: "Show patients treated by Dr. Smith", "Find Dr. Johnson's patients", "List all patients under Dr. Brown"
           
           f) "date_range_search" : If the query involves finding patients based on admission dates, discharge dates, or date ranges
              Examples: "Show admissions from January 2024", "Find patients discharged yesterday", "List admissions between Jan 1 and Jan 15"
           
           g) "insurance_search" : If the query is about finding patients with specific insurance companies or plans
              Examples: "Show Aetna patients", "Find patients with Blue Cross", "List Humana insurance patients"
           
           h) "document_search" : If the query is about finding information about processed documents or document types
              Examples: "Show processed documents", "Find admission forms", "List document types processed"
           
           i) "stats_summary" : If the query is asking for statistics, counts, or summary information
              Examples: "How many patients total?", "Show patient statistics", "What's the count of processed documents?"
           
           j) "recent_activity" : If the query is about recent admissions, discharges, or recently processed information
              Examples: "Show recent admissions", "What was processed today?", "Recent patient activity"

        3. Use "null" if you could not detect any of the above intents

        Using the intent that you just identified, I also want you to recognize the related parameters:
        Instructions to Detect Parameters:
        1. If intent is "patient_lookup" then the parameter will be the patient name provided
        2. If the intent is "diagnosis_search" then the parameter will be the diagnosis name
        3. If the intent is "mrn_lookup" then the parameter will be the MRN provided
        4. If the intent is "facility_search" then the parameter will be the facility name
        5. If the intent is "physician_search" then the parameter will be the physician/doctor name
        6. If the intent is "date_range_search" then the parameter will be the date or date range mentioned
        7. If the intent is "insurance_search" then the parameter will be the insurance company name
        8. If the intent is "document_search" then the parameter will be the document type or "all" for general document queries
        9. If the intent is "stats_summary" then the parameter will be what type of statistics requested or "general"
        10. If the intent is "recent_activity" then the parameter will be the time period or "recent"
        11. If no intent is detected, parameter will also be "null"

        Required JSON structure:
        {{
          "intent": "intent you detected in the provided format",
          "parameter": "parameter you detected in the provided format"
        }}

        Query to analyze:
        {query}
        """

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

        Query text to analyze:
        {document_text}
        """

    def extract_intent(self, query: str) -> Dict[str, Any]:

        try:
            self.logger.info("Starting INTENT & PARAMETER Extraction")
            prompt = self.intent_detection_template.format(query=query)

            response = self.client.chat.completions.create(
                model="healthcare-extractor",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a intent & parameter extraction expert. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.1,
            )

            openai_response = response.choices[0].message.content

            self.logger.info(f"Raw OpenAI response: {openai_response}")
            self.logger.info(
                f"✅ OpenAI response received: {len(openai_response)} characters"
            )

            try:
                extracted_data = json.loads(openai_response)
                self.logger.info(f"Parsed JSON keys: {list(extracted_data.keys())}")
                self.logger.info("🎯 EXTRACTED INTENT DATA:")
                for key, value in extracted_data.items():
                    self.logger.info(f"  {key}: {value}")

                return extracted_data

            except json.JSONDecodeError as json_error:
                self.logger.error(f"❌ JSON parsing failed: {str(json_error)}")
                self.logger.error(f"OpenAI response was: {openai_response}")
                raise json_error

        except Exception as e:
            self.logger.error(f"❌ Intent extraction failed for query: {query}")
            raise e

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
