from __future__ import annotations

import json
import shutil
import base64
from datetime import datetime
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.worksheet.table import Table, TableStyleInfo

from tc_parser import TCRecord, parse_supplier_tc


AGENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = AGENT_ROOT / "Templates" / "tc_output__template.xlsx"
DEFAULT_OUTPUT_DIR = AGENT_ROOT / "Output"
DEFAULT_MASTER = AGENT_ROOT / "Master" / "supplier_tc_master.xlsx"

MAX_TEMPLATE_ROWS = 9
FIRST_ITEM_ROW = 15


def _safe_name(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in value.strip())
    return safe.strip("_") or "supplier_tc"


def _load_record(input_path: str | Path, tc_format: str = "auto") -> TCRecord:
    return parse_supplier_tc(input_path, tc_format=tc_format)


def _set(ws: Any, cell: str, value: Any) -> None:
    target = ws[cell]
    for merged_range in ws.merged_cells.ranges:
        if cell in merged_range:
            target = ws.cell(merged_range.min_row, merged_range.min_col)
            break
    target.value = "" if value is None else value


def _fill_output_template(record: TCRecord, template_path: Path, output_path: Path) -> None:
    if len(record.line_items) > MAX_TEMPLATE_ROWS:
        raise ValueError(
            f"Template has {MAX_TEMPLATE_ROWS} item rows, but {len(record.line_items)} line items were extracted."
        )

    shutil.copy2(template_path, output_path)
    wb = openpyxl.load_workbook(output_path)
    ws = wb.active

    _set(ws, "E6", record.test_certificate_no)
    _set(ws, "Y6", record.date)
    _set(ws, "C7", f"To M/S {record.customer_name_address}" if record.customer_name_address else "To M/S")
    _set(ws, "Y7", record.so_no)
    _set(ws, "Y8", record.product)
    _set(ws, "Y9", "")
    _set(ws, "L10", record.test_certificate_no)
    _set(ws, "E11", record.specification)

    for index, item in enumerate(record.line_items):
        row = FIRST_ITEM_ROW + index
        _set(ws, f"C{row}", item.batch_no)
        _set(ws, f"D{row}", record.grade)
        _set(ws, f"E{row}", record.test_certificate_no)
        _set(ws, f"F{row}", item.coil_no)
        _set(ws, f"G{row}", item.nominal_size)
        _set(ws, f"H{row}", item.net_weight_mt)
        _set(ws, f"I{row}", item.width_mm)
        _set(ws, f"J{row}", item.thickness_mm)
        _set(ws, f"K{row}", item.c)
        _set(ws, f"L{row}", item.s)
        _set(ws, f"M{row}", item.p)
        _set(ws, f"N{row}", item.si)
        _set(ws, f"O{row}", item.al)
        _set(ws, f"P{row}", item.n)
        _set(ws, f"Q{row}", item.nb_v_ti)
        _set(ws, f"R{row}", item.tensile_direction)
        _set(ws, f"S{row}", item.tensile_direction)
        _set(ws, f"T{row}", item.ys)
        _set(ws, f"U{row}", item.uts)
        _set(ws, f"V{row}", item.gl)
        _set(ws, f"W{row}", item.elongation)
        _set(ws, f"X{row}", item.bend_direction)
        _set(ws, f"Y{row}", item.bend_radius)
        _set(ws, f"Z{row}", item.bend_result)

    _set(ws, "H24", record.total_weight_mt or sum(item.net_weight_mt for item in record.line_items))
    _set(ws, "P24", record.total_coils_packets or len(record.line_items))
    _set(ws, "E28", record.vehicle_no)
    _set(ws, "E29", record.invoice_no)

    wb.save(output_path)


def _master_headers() -> list[str]:
    return [
        "processed_at",
        "source_file",
        "test_certificate_no",
        "date",
        "customer_name_address",
        "so_no",
        "so_date",
        "product",
        "specification",
        "grade",
        "billing_doc_no",
        "invoice_no",
        "vehicle_no",
        "batch_no",
        "coil_no",
        "nominal_size",
        "pcs",
        "net_weight_mt",
        "width_mm",
        "thickness_mm",
        "c",
        "s",
        "p",
        "si",
        "al",
        "n",
        "nb_v_ti",
        "tensile_direction",
        "ys",
        "uts",
        "gl",
        "elongation",
        "ys_uts_ratio",
        "bend_direction",
        "bend_radius",
        "bend_result",
        "record_key",
    ]


def _append_master(record: TCRecord, master_path: Path) -> None:
    master_path.parent.mkdir(parents=True, exist_ok=True)
    headers = _master_headers()
    if master_path.exists():
        wb = openpyxl.load_workbook(master_path)
        ws = wb.active
        current_headers = [ws.cell(row=1, column=index).value for index in range(1, len(headers) + 1)]
        if current_headers != headers:
            if "MasterData" in wb.sheetnames:
                del wb["MasterData"]
            ws = wb.create_sheet("MasterData", 0)
            ws.append(headers)
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "MasterData"
        ws.append(headers)

    existing = {
        ws.cell(row=row, column=len(headers)).value
        for row in range(2, ws.max_row + 1)
        if ws.cell(row=row, column=len(headers)).value
    }
    processed_at = datetime.now().isoformat(timespec="seconds")
    for item in record.line_items:
        record_key = f"{record.test_certificate_no}|{item.coil_no}"
        if record_key in existing:
            continue
        ws.append(
            [
                processed_at,
                record.source_file,
                record.test_certificate_no,
                record.date,
                record.customer_name_address,
                record.so_no,
                record.so_date,
                record.product,
                record.specification,
                record.grade,
                record.billing_doc_no,
                record.invoice_no,
                record.vehicle_no,
                item.batch_no,
                item.coil_no,
                item.nominal_size,
                item.pcs,
                item.net_weight_mt,
                item.width_mm,
                item.thickness_mm,
                item.c,
                item.s,
                item.p,
                item.si,
                item.al,
                item.n,
                item.nb_v_ti,
                item.tensile_direction,
                item.ys,
                item.uts,
                item.gl,
                item.elongation,
                item.ys_uts_ratio,
                item.bend_direction,
                item.bend_radius,
                item.bend_result,
                record_key,
            ]
        )

    if "SupplierTCMaster" not in ws.tables and ws.max_row > 1:
        table_ref = f"A1:AK{ws.max_row}"
        table = Table(displayName="SupplierTCMaster", ref=table_ref)
        style = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True, showColumnStripes=False)
        table.tableStyleInfo = style
        ws.add_table(table)
    elif "SupplierTCMaster" in ws.tables:
        ws.tables["SupplierTCMaster"].ref = f"A1:AK{ws.max_row}"

    for column in ws.columns:
        letter = column[0].column_letter
        max_len = max(len(str(cell.value or "")) for cell in column[:50])
        ws.column_dimensions[letter].width = min(max(max_len + 2, 10), 45)
    wb.save(master_path)


def process_supplier_tc(
    input_path: str | Path,
    template_path: str | Path = DEFAULT_TEMPLATE,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    master_path: str | Path = DEFAULT_MASTER,
    include_file_content: bool = False,
    include_master_file_content: bool = False,
    tc_format: str = "auto",
) -> dict[str, Any]:
    input_path = Path(input_path)
    template_path = Path(template_path)
    output_dir = Path(output_dir)
    master_path = Path(master_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    record = _load_record(input_path, tc_format=tc_format)
    output_name = f"TC_Output_{_safe_name(record.test_certificate_no or input_path.stem)}.xlsx"
    output_path = output_dir / output_name
    json_path = output_dir / f"{output_path.stem}.json"

    _fill_output_template(record, template_path, output_path)
    _append_master(record, master_path)
    json_path.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")

    result = {
        "status": "success" if not record.warnings else "success_with_warnings",
        "source_file": str(input_path),
        "output_file_name": output_path.name,
        "output_file": str(output_path),
        "master_file": str(master_path),
        "json_file": str(json_path),
        "line_items": len(record.line_items),
        "tc_format": tc_format,
        "extracted_data": record.to_dict(),
        "warnings": record.warnings,
    }
    if include_file_content:
        result["output_file_base64"] = base64.b64encode(output_path.read_bytes()).decode("ascii")
    if include_master_file_content:
        result["master_file_name"] = master_path.name
        result["master_file_base64"] = base64.b64encode(master_path.read_bytes()).decode("ascii")
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate JSW One TC output from supplier TC PDF or image.")
    parser.add_argument("input_path")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--master", default=str(DEFAULT_MASTER))
    parser.add_argument("--tc-format", default="auto")
    args = parser.parse_args()

    result = process_supplier_tc(args.input_path, args.template, args.output_dir, args.master, tc_format=args.tc_format)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
