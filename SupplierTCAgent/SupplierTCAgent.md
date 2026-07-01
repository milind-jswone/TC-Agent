# Supplier TC Agent

## Purpose

This agent processes supplier TC files uploaded in a Microsoft Teams channel, extracts the required TC data, writes the output into a fixed Excel template, and preserves all extracted data in a master Excel file through Power Automate.

The structure follows the same maintainable pattern as the Contract & SO agent projects: a living markdown notebook, local logs, local memory, and a dedicated tools folder. Every rule, error, fix, and format decision should be recorded here so the agent can improve over time.

## Current Scope

- Accept supplier TC files from a Teams channel upload.
- Use the supplier TC format that will be provided next as the source format.
- Generate the final TC output in the specific Excel template that will be provided next.
- Save extracted data into a master Excel file using Power Automate.
- Maintain local logs, error records, and memory for future improvements.

## Folder Structure

```text
SupplierTCAgent/
  SupplierTCAgent.md
  Logs/
    activity.log
    error.log
  Memory/
    memory.json
  Tools/
    .env.example
    requirements.txt
    teams_intake_notes.md
    extraction_rules.md
    excel_mapping.md
    powerautomate_handoff.md
  Templates/
    README.md
  Samples/
    README.md
  Output/
    README.md
```

## Planned Workflow

1. A supplier TC file is uploaded to the configured Teams channel.
2. Power Automate detects the upload and passes file metadata/content to the TC Agent workflow.
3. The agent extracts required fields from the supplier TC.
4. The extracted values are mapped into the required output Excel template.
5. The output TC Excel file is generated and saved.
6. The complete extracted dataset is appended or updated in the master Excel file through Power Automate.
7. The run result, warnings, and errors are recorded in `Logs/`.
8. New extraction corrections and lessons learned are recorded in `Memory/memory.json` and this markdown file.

## Inputs Needed Next

- Sample supplier TC file.
- Exact output Excel template.
- Required Teams upload naming or message format.
- Master Excel file columns and storage location.
- Power Automate trigger details, if already created.

## Extraction Notes

Pending sample supplier TC.

When the sample is provided, document:

- Source file type.
- Required fields.
- Optional fields.
- Repeated table sections.
- Validation rules.
- Known supplier-specific variations.
- Fields that need manual review when confidence is low.

## Excel Output Mapping

Pending output template.

When the template is provided, document:

- Template file name.
- Sheet names.
- Cell/range mapping.
- Required formatting rules.
- Formula cells that must not be overwritten.
- Output file naming convention.

## Master Excel Handoff

Power Automate will be responsible for saving extracted data into the master Excel file.

Recommended contract between the agent and Power Automate:

- Agent returns one normalized JSON record per TC.
- Power Automate appends or updates the master Excel table.
- A unique TC key should be defined to avoid duplicate rows.
- Failed writes should be logged and retried.

Pending decisions:

- Master Excel file path.
- Table name.
- Unique key field.
- Whether reruns update existing rows or append new versions.

## Logging Rules

- `Logs/activity.log` records successful runs and important run milestones.
- `Logs/error.log` records failures, exception text, affected file name, and next action.
- `Memory/memory.json` stores structured lessons, recurring corrections, supplier-specific quirks, and mapping updates.
- This markdown file stores human-readable workflow decisions and implementation notes.

## Change Log

### 2026-07-01

- Created initial Supplier TC Agent structure.
- Added placeholder folders for logs, memory, tools, templates, samples, and output files.
- Documented the planned Teams upload to Excel template workflow.
- Documented the Power Automate master Excel handoff requirement.
- Copied the sample supplier TC PDF into `Samples/`.
- Copied the output Excel template into `Templates/`.
- Added PDF parser, Excel output generator, local sample runner, and HTTP webhook listener.
- Generated a local test output file for TC `7109367113`.
- Created a local master Excel workbook with one row per extracted coil.
- Added OCR-ready support for scanned PDFs and image uploads.

## Local Test Result

- Source: `Samples/Supplier TC format.pdf`
- Output: `Output/TC_Output_7109367113.xlsx`
- Extracted line items: 5
- Total MT: 25.050
- Master file: `Master/supplier_tc_master.xlsx`
- Warnings: none

## Open Questions

- Confirm whether duplicate master keys should be skipped or updated.
- Confirm where the production master Excel file will be stored.
- Confirm where generated TC output files should be saved in Teams/SharePoint.
- Confirm whether output columns `Long TEN` and `DIR` should both receive tensile direction, or whether one of them should carry a different value.
- Confirm where the HTTP agent will run so Power Automate can reach it.
- Confirm/install Tesseract OCR on the machine/server where the agent will run.
