# Excel Mapping

## Template

- Template file: `SupplierTCAgent/Templates/tc_output__template.xlsx`
- Sheet: `Sheet1`
- Output file pattern: `TC_Output_<test_certificate_no>.xlsx`
- Local output folder: `SupplierTCAgent/Output/`

## Header Mapping

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

## Line Item Mapping

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

- The current template supports 9 line items.
- Some target cells are merged. The generator writes to the top-left cell of merged ranges automatically.
