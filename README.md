# Centralized AI OCR Solution for Healthcare using Azure

A serverless, end-to-end pipeline for extracting, structuring, and querying data from healthcare PDFs using Azure services and AI.

## Features

* **Automated Ingestion**: Upload PDFs to Azure Blob Storage to kick off processing.
* **Text Extraction**: Use Azure Document Intelligence for accurate OCR of complex layouts.
* **Data Structuring**: Leverage Azure OpenAI (GPT-4o mini) to transform raw text into a structured JSON schema.
* **Validation & Exception Handling**: Verify critical fields and route low-confidence results for review.
* **Secure Storage**: Store processed records in Azure SQL Database with normalized tables.
* **Chatbot Interface**: Query patient records via a natural-language HTTP API (Azure Functions).

## Architecture

```text
PDF Upload → Azure Blob Storage → Azure Functions → AI Processing → SQL Database
                                        ↓
                          HTTP Chat API + Intent Recognition

```

## Technology Stack

* **Cloud**: Azure Functions, Blob Storage, Azure SQL Database
* **AI**: Azure Document Intelligence, Azure OpenAI (GPT-4o mini)
* **Language**: Python
* **Libraries**: `azure-functions`, `azure-storage-blob`, `azure-ai-formrecognizer`, `openai`, `pymssql`

## Workflow & Usage

### High-Level Workflow

1. **PDF Ingestion**: User uploads a healthcare PDF to Azure Blob Storage.
2. **Automated Processing**: A Blob-triggered Azure Function invokes Document Intelligence for OCR, then OpenAI Extractor to structure data.
3. **Validation & Storage**: Extracted records are validated; high-confidence entries are saved in Azure SQL, while exceptions are queued for review.
4. **Interactive Chat API**: Users interact via an HTTP endpoint—intent recognition routes queries to the database and returns results.

### Usage Scenarios

* **Patient Lookup**: "Show me all records for patient John Doe."
* **Diagnosis Search**: "Find patients diagnosed with Pneumonia in March 2025."
* **Recent Activity**: "List documents processed in the last 24 hours."
* **Stats Summary**: "How many admissions by facility in Q2 2025?"


## Code Structure

The project follows a clean, modular structure to separate concerns and improve maintainability.

```
azure-functions-env/
├── function_app.py             # Main blob trigger + HTTP chat endpoint
├── host.json                   # Function timeout configuration
├── requirements.txt            # Python dependencies
├── database/
│   ├── connection.py           # Database connection with retry logic
│   └── operations.py           # SQL insert and query operations
└── processors/
    ├── document_intelligence.py   # Text extraction logic
    ├── openai_extractor.py        # Data structuring & Intent Recognition
    ├── data_validator.py          # Accuracy validation logic
    └── chat_processor.py          # Chat logic orchestration
```
---

*Built with Azure Functions and Azure AI services.*
