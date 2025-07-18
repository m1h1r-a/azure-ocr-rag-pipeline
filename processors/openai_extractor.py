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
        You are a query intent detection specialist. Extract ALL applicable intents from the query and return as JSON array.

        Instructions:
        1. Extract ALL intents that apply (can be one or many)
        2. Return array of key-value pairs: intent category → parameter
        3. Order by relevance (most important first)
        4. Read the entire query and determine what the subject is reffering to based on the context
            example query: "Who is John Doe's physician name?" 
            Here, John Doe is clearly the patient and we are looking up the physician

        Intent Categories:
        a) "patient_lookup" - Finding patient by name ("Show John Doe")
        b) "diagnosis_search" - Finding patients by diagnosis ("diabetes patients")
        c) "mrn_lookup" - Finding by MRN ("MRN 12345")
        d) "facility_search" - Finding by facility ("patients at Mayo Clinic")
        e) "physician_search" - Finding by doctor ("Dr. Smith's patients")
        f) "date_range_search" - Finding by dates ("admitted last month")
        g) "insurance_search" - Finding by insurance ("Aetna patients")
        h) "document_search" - Finding documents ("processed documents")
        i) "stats_summary" - Statistics/counts ("How many patients?")
        j) "recent_activity" - Recent info ("recent admissions")

        Parameters:
        - patient_lookup → patient name
        - diagnosis_search → diagnosis name
        - mrn_lookup → MRN number
        - facility_search → facility name
        - physician_search → doctor name
        - date_range_search → date/range
        - insurance_search → insurance name
        - document_search → doc type or "all"
        - stats_summary → stat type or "general"
        - recent_activity → time period or "recent"

        Required format:
        [{{"intent_name": "parameter_value"}}]

        Examples:
        "Show Dr. Smith's diabetes patients"
        [{{"physician_search": "Dr. Smith"}}, {{"diagnosis_search": "diabetes"}}]

        "What are newborn baby names born in General Hospital?"
        [{{"facility_search": "General Hospital"}}, {{"diagnosis_search": "newborn"}}]

        "How many patients admitted last month at General Hospital?"
        [{{"stats_summary": "patient count"}}, {{"date_range_search": "last month"}}, {{"facility_search": "General Hospital"}}]

        "Find John Doe's insurance and diagnosis"
        [{{"patient_lookup": "John Doe"}}, {{"insurance_search": "all"}}, {{"diagnosis_search": "all"}}]

        Return empty array [] if no intents detected.

        Query to analyze:
        {query}
        """

        self.healthcare_prompt_template = """
        You are a healthcare data extraction specialist. Extract patient information from the following medical document text and return it as a JSON object.

        Instructions:
        1. Extract ALL available information, even if some fields are missing, but do not make up any data.
        2. For "patient_name", remove any periods and collapse multiple spaces into a single space (e.g. “MARY.   JANE” → “MARY JANE”).
        3. Use "null" for missing information
        4. Keep original formatting for names and text (aside from the cleaning rule for patient_name)
        5. For dates, use MM/DD/YYYY format when possible
        6. Return only valid JSON, no additional text

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

        self.response_prompt_template = """
        You are a healthcare data assistant. Your job is to directly answer the user's specific question using the provided query results.

        CRITICAL INSTRUCTIONS:
        1. **Answer the question directly FIRST** - Start with the exact information the user asked for
        2. **Be specific to the query type** - Focus on what they actually want to know
        3. **Use the most relevant data** - Prioritize results that directly answer their question
        4. **Provide context secondarily** - Add related helpful information after the main answer
        5. **Handle multiple results intelligently** - If multiple patients found, clarify which one or list them

        RESPONSE STRUCTURE:
        - **Direct Answer**: Start with the specific information requested
        - **Context**: Add relevant supporting details (patient info, dates, etc.)
        - **Closing**: Simple offer to help with more information

        QUERY TYPE EXAMPLES:
        - Insurance questions → Lead with insurance company name
        - Diagnosis questions → Lead with diagnosis information  
        - Patient lookup → Lead with patient identification details
        - Doctor questions → Lead with physician information
        - Date questions → Lead with relevant dates

        FORMATTING RULES:
        - **Tone**: Professional but conversational
        - **Length**: 2-3 sentences maximum
        - **Format**: Single paragraph, no bullet points
        - **Names**: Use proper names and titles (Dr., Patient, etc.)
        - **Null handling**: Skip any null/empty fields entirely
        - **Multiple results**: Be clear about which patient/result you're referencing

        If multiple patients match, either:
        - Focus on the most relevant one if context makes it clear
        - Briefly mention all matches if ambiguous

        User Query: {query}
        Query Results: {query_results}

        Provide a direct, helpful response that answers their specific question:
        """

    def format_response(self, query, query_results) -> str:
        try:
            self.logger.info("Starting Response Formatting")
            prompt = self.response_prompt_template.format(
                query=query, query_results=query_results
            )

            response = self.client.chat.completions.create(
                model="healthcare-extractor",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a chatbot given query and query_results, give appropriate natural language response",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.1,
            )

            openai_response = response.choices[0].message.content
            self.logger.info(f"✅ OpenAI response received: {openai_response}")
            return openai_response

        except Exception as e:
            self.logger.info(f"Unable to Format Response in OpenAI: {e}")
            return "Error Formatting Response in OpenAIExtractor"

    def extract_intent(self, query: str) -> list[Dict[str, Any]]:
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
                temperature=0.3,
            )
            openai_response = response.choices[0].message.content
            self.logger.info(f"Raw OpenAI response: {openai_response}")

            try:
                extracted_intents = json.loads(openai_response)
                self.logger.info(f"🎯 Extracted {len(extracted_intents)} intents")

                # Log each intent
                for intent_dict in extracted_intents:
                    for intent, parameter in intent_dict.items():
                        self.logger.info(f"  {intent}: {parameter}")

                return extracted_intents

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
