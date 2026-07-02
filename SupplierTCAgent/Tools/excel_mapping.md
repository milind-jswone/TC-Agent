# Excel Mapping

## Templates

- Legacy template file: `SupplierTCAgent/Templates/tc_output__template.xlsx`
- Multi-format template file: `SupplierTCAgent/Templates/tc_formats.xlsx`
- Local output folder: `SupplierTCAgent/Output/`
- Output file pattern: `<input_file_name>_output_<YYYYMMDD_HHMMSS_IST>.xlsx`

The active generator uses `tc_formats.xlsx`. Each real TC output format is a sheet in that workbook. To add a new format later:

1. Add a new sheet to `tc_formats.xlsx`.
2. Add the sheet display name to `TC_FORMAT_SHEETS` in `Tools/generate_tc_output.py`.
3. Add the same choice to the Teams adaptive card dropdown.

Supported format values:

| Display name | Power Automate value |
| --- | --- |
| P&T IS 3601 | `p_t_is_3601` |
| P&T IS 1161 | `p_t_is_1161` |
| P&T IS 4923 | `p_t_is_4923` |
| One Helix Coil | `one_helix_coil` |
| One Helix Sheet bundle | `one_helix_sheet_bundle` |
| One Helix Sheet | `one_helix_sheet` |
| Fe 550 | `fe_550` |
| Fe 550D | `fe_550d` |

## Legacy Header Mapping

- `E6`: test certificate number
- `Y6`: date
- `C7`: customer name and address
- `Y7`: SO number
- `Y8`: product
- `L10`: supplier/OEM TC reference number
- `E11`: specification
- `H24`: total quantity in MT
- `P24`: grand total of coils/bundles/sheets
- `C28`: vehicle number
- `C29`: invoice number

## Legacy Line Item Mapping

Rows 15-23 are used for coil/item data.

- `C`: batch/heat number
- `D`: grade
- `E`: RM TC reference number
- `F`: coil number
- `G`: nominal size
- `H`: net weight MT
- `I`: width
- `J`: thickness
- `K`: C
- `L`: S
- `M`: P
- `N`: Si
- `O`: Al
- `P`: N
- `Q`: Nb+V+Ti
- `R`: tensile direction
- `S`: tensile direction
- `T`: YS
- `U`: UTS
- `V`: GL
- `W`: elongation
- `X`: bend direction
- `Y`: bend radius
- `Z`: bend result

## Notes

- The current multi-format templates support 9 line items.
- Some target cells are merged. The generator writes to the top-left cell of merged ranges automatically.
- The generator selects one sheet from `tc_formats.xlsx`, deletes the other sheets from the output workbook, and fills only the selected format.
- Master file update is independent of the selected output format.
- Extraction is also independent of the selected output format. The selected value controls workbook layout only and must not filter TC line items.
