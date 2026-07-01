# TC Agent

Supplier TC Agent extracts supplier test certificate data from PDF or image uploads, fills the JSW One TC Excel output template, and prepares extracted rows for master Excel storage through Power Automate.

## Current Capabilities

- Accepts text PDFs, scanned PDFs, and common image files.
- Extracts header, chemical, and mechanical properties.
- Generates TC output Excel files from the provided template.
- Maintains local logs, memory, and mapping documentation.
- Provides FastAPI endpoints for Power Automate or Cloud Run.

## Local Run

```powershell
cd SupplierTCAgent\Tools
python -m pip install -r requirements.txt
uvicorn webhook_listener:app --host 0.0.0.0 --port 8000
```

Health check:

```text
GET http://localhost:8000/health
```

Main endpoints:

- `POST /tc/process` with multipart file upload.
- `POST /tc/process-base64` with `file_name` and `file_content_base64`.

Webhook responses include `output_file_name`, `output_file_base64`, and `extracted_data` so Power Automate can save the generated Excel file and append rows to a master Excel table.

Optional request field:

```json
{
  "tc_format": "auto"
}
```

## LLM Playground Integration

Set these Cloud Run environment variables to enable LLM-first document extraction:

```text
LLM_API_BASE_URL=<LLM console base URL>
LLM_API_KEY=<API key>
LLM_MODEL=gemini-2.5-flash
LLM_USER_ID=<optional user id>
```

If the LLM call fails, the service falls back to local PDF/OCR extraction.

## Cloud Run

This repo includes a `Dockerfile` for a new independent Cloud Run service. Recommended service name:

```text
supplier-tc-agent
```

Recommended region:

```text
asia-south1
```

The Docker image installs Tesseract OCR, so scanned PDFs and images can be processed in Cloud Run.

## Notes

Generated outputs, sample supplier files, local master Excel workbooks, and environment files are ignored by git.
