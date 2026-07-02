# Templates

`tc_formats.xlsx` is the active multi-format output template workbook. Each supported output format is maintained as a separate sheet.

Current selectable formats:

- P&T IS 3601
- P&T IS 1161
- P&T IS 4923
- One Helix Coil
- One Helix Sheet bundle
- One Helix Sheet
- Fe 550
- Fe 550D

To add a new output format later:

1. Add a new sheet to `tc_formats.xlsx`.
2. Register the sheet name in `Tools/generate_tc_output.py`.
3. Add the same option to the Teams adaptive card dropdown.
