import logging
import os

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential


class DocumentIntelligenceProcessor:

    def __init__(self):
        self.endpoint = os.environ.get("DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.key = os.environ.get("DOCUMENT_INTELLIGENCE_KEY")

        if not self.endpoint or not self.key:
            raise ValueError(
                "Document Intelligence credentials not found in environment variables"
            )

        self.client = DocumentAnalysisClient(
            endpoint=self.endpoint, credential=AzureKeyCredential(self.key)
        )

        self.logger = logging.getLogger(__name__)

    def extract_text(self, blob_data: bytes, filename: str = "unknown") -> str:
        """
        Extract text from PDF blob data

        Args:
            blob_data: PDF file as bytes
            filename: Name of the file (for logging)

        Returns:
            Extracted text as string

        Raises:
            Exception: If text extraction fails
        """
        try:
            self.logger.info(f"🔍 Starting text extraction for: {filename}")

            # Analyze document using prebuilt-read model
            poller = self.client.begin_analyze_document(
                "prebuilt-read", document=blob_data
            )
            result = poller.result()

            # Extract text from all pages
            extracted_text = ""
            for page in result.pages:
                for line in page.lines:
                    extracted_text += line.content + "\n"

            self.logger.info(
                f"✅ Text extraction completed: {len(result.pages)} pages, {len(extracted_text)} characters"
            )
            return extracted_text

        except Exception as e:
            self.logger.error(f"❌ Text extraction failed for {filename}: {str(e)}")
            raise e
