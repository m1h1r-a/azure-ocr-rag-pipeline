
---

# Centralized AI OCR Solution for Healthcare using Azure

A serverless, end-to-end pipeline for extracting, structuring, and querying data from healthcare PDFs using Azure services and AI with an intelligent multi-intent chatbot interface.

## Features

* **Automated Ingestion**: Upload PDFs to Azure Blob Storage to kick off processing.
* **Text Extraction**: Use Azure Document Intelligence for accurate OCR of complex layouts.
* **Data Structuring**: Leverage Azure OpenAI (GPT-4o mini) to transform raw text into a structured JSON schema.
* **Validation & Exception Handling**: Verify critical fields and route low-confidence results for review.
* **Secure Storage**: Store processed records in Azure SQL Database with normalized tables.
* **Multi-Intent Chatbot**: Advanced conversational interface supporting 10+ query types with natural language processing.
* **Streamlit Web Interface**: User-friendly web application for PDF upload and chat interactions.

## Architecture

```text
PDF Upload → Azure Blob Storage → Azure Functions → AI Processing → SQL Database
                                        ↓
                    Streamlit UI ← HTTP Chat API + Multi-Intent Recognition
```

## Technology Stack

* **Cloud**: Azure Functions, Blob Storage, Azure SQL Database
* **AI**: Azure Document Intelligence, Azure OpenAI (GPT-4o mini)
* **Frontend**: Streamlit (Python web framework)
* **Language**: Python
* **Libraries**: `azure-functions`, `azure-storage-blob`, `azure-ai-formrecognizer`, `openai`, `pymssql`, `streamlit`

## Workflow & Usage

### High-Level Workflow

1. **PDF Ingestion**: User uploads a healthcare PDF via Streamlit interface to Azure Blob Storage.
2. **Automated Processing**: A Blob-triggered Azure Function invokes Document Intelligence for OCR, then OpenAI Extractor to structure data.
3. **Validation & Storage**: Extracted records are validated; high-confidence entries are saved in Azure SQL, while exceptions are queued for review.
4. **Interactive Chat Interface**: Users interact via Streamlit chat interface—multi-intent recognition routes queries to the database and returns natural language responses.

### Enhanced Chat Capabilities

The system now supports sophisticated multi-intent detection and processing:

#### **Supported Intent Categories**

* **Patient Lookup**: Find patients by name
* **MRN Lookup**: Search by Medical Record Number
* **Diagnosis Search**: Find patients by medical condition
* **Physician Search**: Locate patients by attending doctor
* **Insurance Search**: Query by insurance company
* **Facility Search**: Find patients by healthcare facility
* **Document Search**: Locate processed documents
* **Stats Summary**: Get database statistics and counts
* **Date Range Search**: Find records within specific timeframes
* **Recent Activity**: View recent admissions or processing

#### **Multi-Intent Processing**

The system can handle complex queries with multiple intents:

* "Show Dr. Smith's diabetes patients" → Combines physician search + diagnosis search
* "Find John Doe's insurance and diagnosis" → Patient lookup + insurance info + diagnosis
* "How many patients admitted last month at General Hospital?" → Stats + date range + facility

### Usage Scenarios

* **Basic Patient Lookup**:
  → *"Who is John Doe?"*

* **MRN Retrieval**:
  → *"What is John Doe's MRN?"*

* **Diagnosis Inquiry**:
  → *"What is John Doe's diagnosis?"*

* **Multi-Criteria Search**:
  → *"Patients in general hospital who are newborn?"*

* **Physician Information**:
  → *"What is Zaghari Etaf Mohammed physician's name?"*

* **Insurance Details**:
  → *"What is Jane Cortez Doe's insurance details?"*

## Code Structure

The project follows a clean, modular structure to separate concerns and improve maintainability.

```
digest/
├── app.py                      # Streamlit web interface
├── function_app.py             # Main blob trigger + HTTP chat endpoint
├── host.json                   # Function timeout configuration
├── local.settings.json         # Environment variables and API keys
├── requirements.txt            # Python dependencies
├── database/
│   ├── __init__.py
│   ├── connection.py           # Database connection with retry logic
│   ├── operations.py           # SQL insert operations
│   └── retreive_data.py        # Database query operations for chat
└── processors/
    ├── __init__.py
    ├── document_intelligence.py   # Text extraction logic
    ├── openai_extractor.py        # Data structuring & Multi-Intent Recognition
    ├── data_validator.py          # Accuracy validation logic
    └── chat_processor.py          # Chat orchestration & response generation
```

## Key Improvements

### **Enhanced Chat System**

* **Multi-Intent Detection**: Advanced AI-powered intent recognition supporting complex, multi-faceted queries
* **Natural Language Responses**: Context-aware response generation that directly answers user questions
* **Improved Accuracy**: Evolved from "highly inaccurate" single-intent to comprehensive multi-intent system
* **Query Flexibility**: Supports 10+ intent categories with intelligent parameter extraction

### **User Interface**

* **Streamlit Web App**: Professional web interface replacing basic API interactions
* **Real-time Chat**: Conversational interface with message history
* **PDF Upload Integration**: Seamless file upload with processing status feedback
* **Responsive Design**: Clean, healthcare-focused UI design

### **Database Architecture**

* **Comprehensive Schema**: Normalized tables for Documents, Patients, Insurance, ProcessTable, and ExceptionTable
* **Advanced Querying**: Support for complex JOIN operations across multiple tables
* **Data Relationships**: Proper foreign key relationships enabling sophisticated queries
* **Audit Trail**: Complete processing history with accuracy tracking

### **Response Generation**

* **Direct Answers**: Responses lead with the specific information requested
* **Context-Aware**: Tailored responses based on query type and complexity
* **Professional Tone**: Healthcare-appropriate language and formatting
* **Multi-Result Handling**: Intelligent aggregation of results from multiple database queries

---

*Built with Azure Functions, Azure AI services, and Streamlit for modern healthcare document processing.*
