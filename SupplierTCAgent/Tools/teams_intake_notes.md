# Teams Intake Notes

## Channel

- Team: Test Certificate Agent
- Channel: Supplier TC Agent

## Upload Format

Current v1 expectation:

- User uploads one supplier TC PDF or image in the Teams channel.
- Supported extensions: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`, `.webp`
- No special command text is required yet.

Recommended optional message format for future control:

```text
@suppliertc
```

## Power Automate Payload Fields

For `/tc/process-base64`:

```json
{
  "file_name": "Supplier TC format.pdf",
  "file_content_base64": "<file content>"
}
```

## Output Back To Teams

Power Automate should reply in the same thread with:

- Success/failure status
- Generated TC Excel file link
- Number of extracted line items
- Any warnings
