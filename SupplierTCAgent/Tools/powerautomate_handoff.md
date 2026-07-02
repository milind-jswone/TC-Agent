# Power Automate Handoff

Power Automate will watch the Teams channel, send the supplier TC PDF to the agent, save the generated TC output back to the channel or SharePoint folder, and append extracted rows to the production master Excel file.

## Teams Source

- Team: Test Certificate Agent
- Channel: Supplier TC Agent
- Trigger: new message or uploaded PDF attachment in the channel
- Supported input in v2: text PDFs, scanned/image PDFs, PNG, JPG/JPEG, TIF/TIFF, BMP, and WEBP

## Local Agent Endpoints

Start locally from `SupplierTCAgent/Tools`:

```powershell
uvicorn webhook_listener:app --host 0.0.0.0 --port 8000
```

Health check:

```text
GET http://localhost:8000/health
```

Power Automate can call either endpoint:

- `POST /tc/process` with multipart field `file`
- `POST /tc/process-base64` with JSON body containing `file_name`, `file_content_base64`, and optional `tc_format`

To let the agent update the production master workbook, also send the current SharePoint master file:

```json
{
  "file_name": "Supplier TC.pdf",
  "file_content_base64": "<uploaded TC file base64>",
  "tc_format": "format_1",
  "master_file_name": "Master TC.xlsx",
  "master_file_base64": "<current master workbook base64>"
}
```

For a cloud flow, the endpoint must be reachable by Power Automate. That means the agent needs to run on a hosted service, an internal gateway, or a tunnel during testing.

OCR requirements for scanned PDFs and image files:

- Python packages from `requirements.txt`
- Tesseract OCR application installed on the machine running the agent
- Optional `TESSERACT_CMD` environment variable when `tesseract.exe` is not on PATH

## Agent Response Shape

```json
{
  "status": "success",
  "source_file": "Supplier TC format.pdf",
  "output_file_name": "TC_Output_7109367113.xlsx",
  "output_file": "",
  "output_file_base64": "",
  "master_file": "",
  "master_file_name": "Master TC.xlsx",
  "master_file_base64": "",
  "json_file": "",
  "line_items": 5,
  "tc_format": "auto",
  "extracted_data": {},
  "warnings": []
}
```

## Master Excel Contract

Local test master:

```text
SupplierTCAgent/Master/supplier_tc_master.xlsx
```

Production master should use an Excel table with the same columns as the local workbook. The unique row key is:

```text
test_certificate_no + "|" + coil_no
```

Recommended behavior:

- If the key does not exist, append a new row.
- If the key exists, skip the row or update it based on the final business rule.
- If the master write fails, post a warning in Teams and keep the generated output file.

## Power Automate Flow Draft

1. Trigger when a new channel message is created in `Supplier TC Agent`.
2. Check whether the message has a supported PDF or image attachment.
3. Get attachment content.
4. Call the agent endpoint `/tc/process-base64`.
5. Save `output_file_base64` as `output_file_name` to the target Teams/SharePoint location.
6. Save `master_file_base64` back over the production master workbook.
7. Reply in the Teams thread with success/failure and output file link.

## LLM Playground Integration

The agent can optionally use the JSW One LLM Console invoke API before falling back to the local PDF/OCR parser.

Configure these Cloud Run environment variables:

```text
LLM_API_BASE_URL=<LLM console base URL>
LLM_API_KEY=<API key>
LLM_MODEL=gemini-2.5-flash
LLM_USER_ID=<optional user id>
LLM_MAX_TOKENS=32768
```

When configured, the agent sends the uploaded TC as a base64 attachment to:

```text
POST /api/invoke
```

If the LLM call fails or returns no line items, the agent falls back to the deterministic parser/OCR path and returns a warning.

## Items Needed From User

- Production master Excel file location.
- Output folder location for generated TC files.
- Whether duplicate keys should be skipped or updated.
- Where the HTTP agent will run so Power Automate can reach it.
