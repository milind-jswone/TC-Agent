from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pdfplumber

from llm_client import invoke_document_extraction, is_llm_configured
from ocr_utils import is_image_file, ocr_image_file, ocr_pdf_file


@dataclass
class TCLineItem:
    batch_no: str
    coil_no: str
    nominal_size: str
    pcs: str
    net_weight_mt: float
    thickness_mm: float | None = None
    width_mm: float | None = None
    length_mm: float | None = None
    c: float | None = None
    s: float | None = None
    p: float | None = None
    si: float | None = None
    al: float | None = None
    n: float | None = None
    nb: float | None = None
    v: float | None = None
    ti: float | None = None
    nb_v_ti: float | None = None
    tensile_direction: str = ""
    ys: float | None = None
    uts: float | None = None
    gl: str = ""
    elongation: float | None = None
    ys_uts_ratio: float | None = None
    bend_direction: str = ""
    bend_radius: str = ""
    bend_result: str = ""
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class TCRecord:
    source_file: str
    test_certificate_no: str = ""
    date: str = ""
    product: str = ""
    so_no: str = ""
    so_date: str = ""
    customer_name_address: str = ""
    specification: str = ""
    grade: str = ""
    billing_doc_no: str = ""
    invoice_no: str = ""
    vehicle_no: str = ""
    total_weight_mt: float | None = None
    total_coils_packets: int | None = None
    line_items: list[TCLineItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _to_float(value: Any) -> float | None:
    text = _clean(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _to_int(value: Any) -> int | None:
    text = _clean(value)
    if not text:
        return None


def _to_text(value: Any) -> str:
    return _clean(value)


def _first_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value is not None and value != "":
            return value
    return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _match(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return _clean(match.group(1)) if match else ""


def _parse_size(size: str) -> tuple[float | None, float | None, float | None]:
    parts = re.findall(r"\d+(?:\.\d+)?", size)
    if len(parts) < 3:
        return None, None, None
    return float(parts[0]), float(parts[1]), float(parts[2])


def _record_from_llm_payload(path: Path, payload: dict[str, Any]) -> TCRecord:
    record = TCRecord(source_file=path.name)
    record.raw_data = payload
    record.test_certificate_no = _to_text(_first_value(payload, "test_certificate_no", "test_certificate_number"))
    record.date = _to_text(_first_value(payload, "date", "certificate_date"))
    record.product = _to_text(_first_value(payload, "product", "product_name"))
    record.so_no = _to_text(_first_value(payload, "so_no", "sales_order_number"))
    record.so_date = _to_text(_first_value(payload, "so_date", "sales_order_date"))
    record.customer_name_address = _to_text(_first_value(payload, "customer_name_address", "consignee_address"))
    if not record.customer_name_address:
        customer_parts = [
            _to_text(_first_value(payload, "customer_name", "consignee_name")),
            _to_text(payload.get("customer_location")),
        ]
        record.customer_name_address = ", ".join(part for part in customer_parts if part)
    record.specification = _to_text(payload.get("specification"))
    record.grade = _to_text(_first_value(payload, "grade", "material_grade", "specification_grade")) or (
        record.specification.split()[-1] if record.specification else ""
    )
    record.billing_doc_no = _to_text(_first_value(payload, "billing_doc_no", "billing_document_number"))
    record.invoice_no = _to_text(_first_value(payload, "invoice_no", "invoice_number"))
    record.vehicle_no = _to_text(_first_value(payload, "vehicle_no", "vehicle_number"))
    record.total_weight_mt = _to_float(payload.get("total_weight_mt"))
    record.total_coils_packets = _to_int(_first_value(payload, "total_coils_packets", "total_coils", "total_packets", "total_batches"))
    warnings = payload.get("warnings")
    if isinstance(warnings, list):
        record.warnings.extend(_to_text(item) for item in warnings if _to_text(item))

    raw_items = payload.get("line_items") or payload.get("batches") or []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        nominal_size = _to_text(raw_item.get("nominal_size"))
        thickness, width, length = _parse_size(nominal_size)
        coil_no = _to_text(_first_value(raw_item, "coil_no", "coil_number", "packet_number"))
        item = TCLineItem(
            batch_no=_to_text(_first_value(raw_item, "batch_no", "heat_number", "cast_number", "batch_identifier")),
            coil_no=coil_no,
            nominal_size=nominal_size,
            pcs=_to_text(_first_value(raw_item, "pcs", "pieces_count")),
            net_weight_mt=_to_float(_first_value(raw_item, "net_weight_mt", "quantity_mt")) or 0.0,
            thickness_mm=_to_float(_first_value(raw_item, "thickness_mm", "thickness")) or thickness,
            width_mm=_to_float(_first_value(raw_item, "width_mm", "width")) or width,
            length_mm=_to_float(_first_value(raw_item, "length_mm", "length")) or length,
            c=_to_float(_first_value(raw_item, "c", "carbon_percent")),
            s=_to_float(_first_value(raw_item, "s", "sulphur_percent")),
            p=_to_float(_first_value(raw_item, "p", "phosphorus_percent")),
            si=_to_float(_first_value(raw_item, "si", "silicon_percent")),
            al=_to_float(_first_value(raw_item, "al", "aluminium_percent")),
            n=_to_float(_first_value(raw_item, "n", "nitrogen_ppm")),
            nb=_to_float(_first_value(raw_item, "nb", "niobium_percent")),
            v=_to_float(_first_value(raw_item, "v", "vanadium_percent")),
            ti=_to_float(_first_value(raw_item, "ti", "titanium_percent")),
            nb_v_ti=_to_float(_first_value(raw_item, "nb_v_ti", "micro_alloying_elements_percent")),
            tensile_direction=_to_text(_first_value(raw_item, "tensile_direction", "tensile_test_direction")),
            ys=_to_float(_first_value(raw_item, "ys", "yield_strength_mpa")),
            uts=_to_float(_first_value(raw_item, "uts", "ultimate_tensile_strength_mpa")),
            gl=_to_text(_first_value(raw_item, "gl", "gauge_length")),
            elongation=_to_float(_first_value(raw_item, "elongation", "elongation_percent")),
            ys_uts_ratio=_to_float(_first_value(raw_item, "ys_uts_ratio", "yield_to_tensile_ratio")),
            bend_direction=_to_text(_first_value(raw_item, "bend_direction", "bend_test_direction")),
            bend_radius=_to_text(_first_value(raw_item, "bend_radius", "bend_diameter")),
            bend_result=_to_text(_first_value(raw_item, "bend_result", "bend_test_result")),
            raw_data=raw_item,
        )
        if item.nb_v_ti is None:
            parts = [value for value in (item.nb, item.v, item.ti) if value is not None]
            item.nb_v_ti = round(sum(parts), 6) if parts else None
        if item.batch_no or item.coil_no:
            record.line_items.append(item)

    return record


def _missing(value: Any) -> bool:
    return value is None or value == ""


def _fill_missing(target: Any, attr: str, source: Any) -> None:
    if _missing(getattr(target, attr)) and not _missing(getattr(source, attr)):
        setattr(target, attr, getattr(source, attr))


def _enrich_record(target: TCRecord, source: TCRecord) -> TCRecord:
    for attr in (
        "test_certificate_no",
        "date",
        "product",
        "so_no",
        "so_date",
        "customer_name_address",
        "specification",
        "grade",
        "billing_doc_no",
        "invoice_no",
        "vehicle_no",
        "total_weight_mt",
        "total_coils_packets",
    ):
        _fill_missing(target, attr, source)

    source_by_key = {(item.batch_no, item.coil_no): item for item in source.line_items}
    for item in target.line_items:
        source_item = source_by_key.get((item.batch_no, item.coil_no))
        if source_item is None:
            continue
        for attr in (
            "nominal_size",
            "pcs",
            "net_weight_mt",
            "thickness_mm",
            "width_mm",
            "length_mm",
            "c",
            "s",
            "p",
            "si",
            "al",
            "n",
            "nb",
            "v",
            "ti",
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
        ):
            _fill_missing(item, attr, source_item)

    if target.total_coils_packets is None and target.line_items:
        target.total_coils_packets = len(target.line_items)
    return target


def _extract_customer(text: str) -> str:
    match = re.search(
        r"To,\s*(.*?)\s*(?:We certified|Specification\s*:)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    block = match.group(1)
    block = re.sub(r"\bSO No\.\s*:.*", "", block, flags=re.IGNORECASE)
    block = re.sub(r"\bSO Date\s*:.*", "", block, flags=re.IGNORECASE)
    lines = [_clean(line) for line in block.splitlines()]
    return ", ".join(line for line in lines if line)


def _extract_tables(pdf_path: Path) -> tuple[str, list[list[list[Any]]]]:
    page_text: list[str] = []
    tables: list[list[list[Any]]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            page_text.append(page.extract_text(x_tolerance=1, y_tolerance=3) or "")
            tables.extend(page.extract_tables() or [])
    return "\n".join(page_text), tables


def _extract_source(path: Path) -> tuple[str, list[list[list[Any]]], list[str]]:
    warnings: list[str] = []
    suffix = path.suffix.lower()
    if is_image_file(path):
        warnings.append("Input was processed with OCR because it is an image file.")
        return ocr_image_file(path), [], warnings
    if suffix == ".pdf":
        text, tables = _extract_tables(path)
        if len(_clean(text)) < 100:
            warnings.append("PDF text layer was empty or too small; OCR fallback was used.")
            return ocr_pdf_file(path), [], warnings
        return text, tables, warnings
    raise ValueError(f"Unsupported input file type: {suffix}. Supported types are PDF and common image files.")


def _is_item_row(row: list[Any]) -> bool:
    return bool(_clean(row[0])) and bool(_clean(row[1])) and bool(_clean(row[2])) and _to_float(row[5]) is not None


def _parse_line_items_from_text(text: str) -> list[TCLineItem]:
    items_by_key: dict[tuple[str, str], TCLineItem] = {}
    chemical_section = text.split("Mechanical Properties", 1)[0]
    mechanical_section = text.split("Mechanical Properties", 1)[1] if "Mechanical Properties" in text else ""
    row_pattern = re.compile(
        r"^(?P<batch>[A-Z]\d{6})\s+"
        r"(?P<coil>[A-Za-z0-9/-]+)\s+"
        r"(?P<size>\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?)\s+"
        r"(?P<pcs>\d+)\s+"
        r"(?P<qty>\d+(?:\.\d+)?)\s+"
        r"(?P<rest>.+)$",
        flags=re.IGNORECASE,
    )

    for line in chemical_section.splitlines():
        match = row_pattern.match(_clean(line))
        if not match:
            continue
        values = re.findall(r"-?\d+(?:\.\d+)?", match.group("rest"))
        if len(values) < 11:
            continue
        thickness, width, length = _parse_size(match.group("size"))
        item = TCLineItem(
            batch_no=match.group("batch"),
            coil_no=match.group("coil"),
            nominal_size=_clean(match.group("size")),
            pcs=match.group("pcs"),
            net_weight_mt=float(match.group("qty")),
            thickness_mm=thickness,
            width_mm=width,
            length_mm=length,
            c=_to_float(values[0]),
            s=_to_float(values[2]),
            p=_to_float(values[3]),
            si=_to_float(values[4]),
            al=_to_float(values[5]),
            n=_to_float(values[6]),
            nb=_to_float(values[7]),
            v=_to_float(values[8]),
            ti=_to_float(values[9]),
        )
        parts = [value for value in (item.nb, item.v, item.ti) if value is not None]
        item.nb_v_ti = round(sum(parts), 6) if parts else None
        items_by_key[(item.batch_no, item.coil_no)] = item

    for line in mechanical_section.splitlines():
        match = row_pattern.match(_clean(line))
        if not match:
            continue
        key = (match.group("batch"), match.group("coil"))
        item = items_by_key.get(key)
        if item is None:
            thickness, width, length = _parse_size(match.group("size"))
            item = TCLineItem(
                batch_no=match.group("batch"),
                coil_no=match.group("coil"),
                nominal_size=_clean(match.group("size")),
                pcs=match.group("pcs"),
                net_weight_mt=float(match.group("qty")),
                thickness_mm=thickness,
                width_mm=width,
                length_mm=length,
            )
            items_by_key[key] = item

        tokens = match.group("rest").split()
        if len(tokens) >= 9:
            item.tensile_direction = tokens[0]
            item.ys = _to_float(tokens[1])
            item.uts = _to_float(tokens[2])
            item.gl = tokens[3]
            item.elongation = _to_float(tokens[4])
            item.ys_uts_ratio = _to_float(tokens[5])
            item.bend_direction = tokens[6]
            item.bend_radius = tokens[7]
            item.bend_result = tokens[8]

    return list(items_by_key.values())


def parse_supplier_tc(input_path: str | Path, tc_format: str = "auto", prefer_llm: bool = True) -> TCRecord:
    path = Path(input_path)
    if prefer_llm and is_llm_configured():
        try:
            # Keep extraction format-neutral. The user's selected format only
            # controls the output workbook layout after all TC rows are read.
            record = _record_from_llm_payload(path, invoke_document_extraction(path, tc_format="auto"))
            if record.line_items:
                try:
                    return _enrich_record(record, parse_supplier_tc(path, tc_format="auto", prefer_llm=False))
                except Exception as exc:
                    if record.total_coils_packets is None:
                        record.total_coils_packets = len(record.line_items)
                    record.warnings.append(f"Local enrichment failed after LLM extraction: {exc}")
                    return record
            record.warnings.append("LLM extraction returned no line items; falling back to parser/OCR.")
            fallback_record = record
        except Exception as exc:
            fallback_record = TCRecord(source_file=path.name)
            fallback_record.warnings.append(f"LLM extraction failed; falling back to parser/OCR: {exc}")
    else:
        fallback_record = TCRecord(source_file=path.name)

    text, tables, source_warnings = _extract_source(path)
    record = TCRecord(source_file=path.name)
    record.warnings.extend(fallback_record.warnings)
    record.warnings.extend(source_warnings)

    record.test_certificate_no = _match(text, r"Test Certificate No\.\s*:\s*([A-Za-z0-9/-]+)")
    record.date = _match(text, r"Test Certificate No\..*?Date\s*:\s*([0-9.\/-]+)")
    record.product = _match(text, r"Product\s*:\s*(.+)")
    record.so_no = _match(text, r"SO No\.\s*:\s*([A-Za-z0-9/-]+)")
    record.so_date = _match(text, r"SO Date\s*:\s*([0-9.\/-]+)")
    record.customer_name_address = _extract_customer(text)
    record.specification = _match(text, r"Specification\s*:\s*(.*?)\s+(?:Chemical Composition|Mechanical Properties)")
    record.grade = record.specification.split()[-1] if record.specification else ""
    record.billing_doc_no = _match(text, r"Billing Doc No\.\s*:\s*([A-Za-z0-9/-]+)")
    record.invoice_no = _match(text, r"Invoice No\.\s*:\s*([A-Za-z0-9/-]+)")
    record.vehicle_no = _match(text, r"Vehicle No\.\s*:\s*([A-Za-z0-9/-]+)")
    total_weight = _match(text, r"Total weight in Metric Tonnes\s*([0-9.]+)")
    total_count = _match(text, r"Grand total of coils\s*/\s*packets\s*([0-9]+)")
    record.total_weight_mt = _to_float(total_weight)
    record.total_coils_packets = _to_int(total_count)

    items_by_key: dict[tuple[str, str], TCLineItem] = {}
    for table in tables:
        table_text = " ".join(_clean(cell) for row in table for cell in row)
        table_kind = ""
        if "Chemical Composition" in table_text:
            table_kind = "chemical"
        elif "Mechanical Properties" in table_text:
            table_kind = "mechanical"

        for row in table:
            if len(row) < 15 or not _is_item_row(row):
                continue
            batch_no = _clean(row[0])
            coil_no = _clean(row[1])
            key = (batch_no, coil_no)
            item = items_by_key.get(key)
            if item is None:
                thickness, width, length = _parse_size(_clean(row[2]))
                item = TCLineItem(
                    batch_no=batch_no,
                    coil_no=coil_no,
                    nominal_size=_clean(row[2]),
                    pcs=_clean(row[4]),
                    net_weight_mt=_to_float(row[5]) or 0.0,
                    thickness_mm=thickness,
                    width_mm=width,
                    length_mm=length,
                )
                items_by_key[key] = item

            if table_kind == "chemical":
                item.c = _to_float(row[6])
                item.s = _to_float(row[8])
                item.p = _to_float(row[9])
                item.si = _to_float(row[10])
                item.al = _to_float(row[11])
                item.n = _to_float(row[12])
                item.nb = _to_float(row[14])
                item.v = _to_float(row[15])
                item.ti = _to_float(row[16])
                parts = [value for value in (item.nb, item.v, item.ti) if value is not None]
                item.nb_v_ti = round(sum(parts), 6) if parts else None
            elif table_kind == "mechanical":
                item.tensile_direction = _clean(row[6])
                item.ys = _to_float(row[7])
                item.uts = _to_float(row[8])
                item.gl = _clean(row[9])
                item.elongation = _to_float(row[10])
                item.ys_uts_ratio = _to_float(row[11])
                item.bend_direction = _clean(row[12])
                item.bend_radius = _clean(row[13])
                item.bend_result = _clean(row[14])

    record.line_items = list(items_by_key.values())
    if not record.line_items:
        record.line_items = _parse_line_items_from_text(text)

    if not record.line_items:
        record.warnings.append("No coil line items were extracted.")
    if record.total_coils_packets is None and record.line_items:
        record.total_coils_packets = len(record.line_items)
    if record.total_coils_packets is not None and record.total_coils_packets != len(record.line_items):
        record.warnings.append(
            f"Extracted {len(record.line_items)} line items but source total says {record.total_coils_packets}."
        )
    return record


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Extract supplier TC PDF data as JSON.")
    parser.add_argument("pdf_path")
    parser.add_argument("--json-out")
    args = parser.parse_args()

    record = parse_supplier_tc(args.pdf_path)
    payload = json.dumps(record.to_dict(), indent=2)
    if args.json_out:
        Path(args.json_out).write_text(payload, encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
