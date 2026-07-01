# Extraction Rules

## Source

- Sample file: `SupplierTCAgent/Samples/Supplier TC format.pdf`
- File type: text-extractable PDF
- Pages in sample: 2
- Supported v2 input types: text PDFs, scanned/image PDFs, PNG, JPG/JPEG, TIF/TIFF, BMP, and WEBP

## Header Fields

- Test certificate number
- Date
- Product
- SO number
- SO date
- Customer name and address
- Specification
- Grade
- Billing document number
- Invoice number
- Vehicle number

## Line Item Fields

- Batch/heat number
- Coil/packet number
- Nominal size
- Pieces
- Net weight MT
- Thickness, width, length parsed from nominal size
- Chemical values: C, S, P, Si, Al, N
- Nb+V+Ti calculated from supplier TC values
- Mechanical values: tensile direction, YS, UTS, GL, elongation, YS/UTS ratio, bend direction, bend radius, bend result

## Validation Rules

- Extracted line count should match grand total of coils/packets.
- Extracted net weight total should match total weight in metric tonnes.
- Fail the run when more than 9 line items are extracted because the current output template has rows 15-23 available.
- Warn when no line items are extracted.

## OCR Rules

- Use normal PDF text/table extraction first for PDFs.
- If a PDF has no useful text layer, render pages and run OCR.
- If the input is an image file, run OCR directly.
- OCR requires Python packages from `requirements.txt` plus the separate Tesseract OCR application.
- If Tesseract is not on PATH, set `TESSERACT_CMD` in the environment to the installed `tesseract.exe` path.
- OCR text is parsed using line patterns, so low-quality scans may need manual review or a stronger supplier-specific rule.

## LLM Extraction Rules

- If `LLM_API_BASE_URL` and `LLM_API_KEY` are configured, use the LLM playground `/api/invoke` endpoint first.
- Send the uploaded TC file as a base64 attachment.
- Ask for strict JSON matching the agent schema.
- Include selected `tc_format` from Power Automate in the prompt.
- If the LLM extraction fails or returns no line items, fall back to local PDF/OCR parsing.

## Current Assumptions

- `Batch No.` in the output template maps to supplier `Cast / Heat No.`
- `RM TC Reference No.` maps to supplier `Test Certificate No.`
- `Nb+V+Ti` maps to the calculated sum of supplier Nb, V, and Ti fields.
- Output columns `Long TEN` and `DIR` both receive the supplier tensile direction until the final business meaning is confirmed.
