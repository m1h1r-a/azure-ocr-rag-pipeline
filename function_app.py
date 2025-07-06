import azure.functions as func
import logging
import os
import json
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

log_directory = "logs"
os.makedirs(log_directory, exist_ok=True)
log_file_path = os.path.join(log_directory, "pdf_processor.log")

file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Get the root logger and add the file handler
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

app = func.FunctionApp()

@app.blob_trigger(arg_name="myblob", path="pdfs/{name}",
                  connection="pdfstorage0001_STORAGE") 
def ProcessPdfBlob(myblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob")
    logging.info(f"Name: {myblob.name}")
    logging.info(f"Blob Size: {myblob.length} bytes")







    
    try:
        # === STEP 1: Document Intelligence - Extract Text ===
        logging.info("🔍 Starting Document Intelligence text extraction...")
        
        # Get Document Intelligence credentials
        doc_endpoint = os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"]
        doc_key = os.environ["DOCUMENT_INTELLIGENCE_KEY"]
        
        # Initialize Document Intelligence client
        document_analysis_client = DocumentAnalysisClient(
            endpoint=doc_endpoint, 
            credential=AzureKeyCredential(doc_key)
        )
        
        # Read and analyze PDF
        blob_data = myblob.read()
        poller = document_analysis_client.begin_analyze_document(
            "prebuilt-read", 
            document=blob_data
        )
        result = poller.result()
        
        # Extract text from all pages
        extracted_text = ""
        for page in result.pages:
            for line in page.lines:
                extracted_text += line.content + "\n"
        
        logging.info(f"✅ Document Intelligence completed: {len(result.pages)} pages, {len(extracted_text)} characters")
        
        # === STEP 2: OpenAI - Structure the Data ===
        logging.info("🤖 Starting OpenAI data structuring...")
        
        # Get OpenAI credentials
        openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
        openai_key = os.environ["AZURE_OPENAI_KEY"]
        
        # Initialize OpenAI client
        openai_client = AzureOpenAI(
            azure_endpoint=openai_endpoint,
            api_key=openai_key,
            api_version="2024-02-01"
        )
        
        # Healthcare data extraction prompt
        healthcare_prompt = f"""
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
{extracted_text}
"""
        
        # Call OpenAI
        response = openai_client.chat.completions.create(
            model="healthcare-extractor",  # Your deployment name
            messages=[
                {"role": "system", "content": "You are a healthcare data extraction expert. Return only valid JSON."},
                {"role": "user", "content": healthcare_prompt}
            ],
            max_tokens=1000,
            temperature=0.1  # Low temperature for consistent extraction
        )
        
        # Get the response content
        openai_response = response.choices[0].message.content
        logging.info(f"✅ OpenAI response received: {len(openai_response)} characters")
        
        # === STEP 3: Parse and Validate JSON ===
        logging.info("📝 Parsing and validating extracted data...")
        
        try:
            # Parse JSON response
            extracted_data = json.loads(openai_response)

            # Log structured data
            logging.info(f"Data:\n{extracted_data}")  
            logging.info("🎯 EXTRACTED HEALTHCARE DATA:")
            for key, value in extracted_data.items():
                logging.info(f"  {key}: {value}")
            
            # Simple validation - check if we got any meaningful data
            required_fields = ["patient_name", "mrn", "primary_diagnosis"]
            found_fields = sum(1 for field in required_fields if extracted_data.get(field) and extracted_data[field] != "null")
            accuracy = (found_fields / len(required_fields)) * 100
            
            logging.info(f"📊 Extraction accuracy: {accuracy:.1f}% ({found_fields}/{len(required_fields)} required fields)")
            
            if accuracy >= 50:
                logging.info("✅ EXTRACTION SUCCESSFUL - Ready for database storage")
            else:
                logging.warning("⚠️ LOW ACCURACY - Would be stored in ExceptionTable")

        except json.JSONDecodeError as json_error:
                    logging.error(f"❌ JSON parsing failed: {str(json_error)}")
                    logging.error(f"OpenAI response was: {openai_response}")
                    raise json_error

        # === STEP 4: Test Database Connection ===
        logging.info("🔗 Testing SQL database connection...")

        try:
            import pymssql
            
            # Parse connection details from your existing connection string
            server = "pdf-sql-server-0001.database.windows.net"
            database = "pdf-data-db"
            username = "CloudSAdccf3bad"
            password = "Azure@3627"
            
            # Test connection using pymssql
            with pymssql.connect(
                server=server,
                user=username,
                password=password,
                database=database,
                port=1433,
                timeout=60,
                as_dict=True  # Return results as dictionaries
            ) as conn:
                cursor = conn.cursor()
                
                # Simple test query
                cursor.execute("SELECT 1 as test_value")
                result = cursor.fetchone()
                
                if result and result['test_value'] == 1:
                    logging.info("✅ SQL Database connection successful!")

                else:
                    logging.error("❌ SQL connection test failed - unexpected result")



                    
        except Exception as db_error:
            logging.error(f"❌ SQL Database connection failed: {str(db_error)}")
            logging.error(f"Error type: {type(db_error).__name__}")
            
 
    except Exception as e:
        logging.error(f"❌ Error in PDF processing pipeline: {str(e)}")
        logging.error(f"Error type: {type(e).__name__}")
        raise e