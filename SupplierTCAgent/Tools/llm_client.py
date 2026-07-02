from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
from pathlib import Path
from typing import Any

import requests


LLM_PROMPT = """
You are an expert data extraction system for steel industry Test Certificates (TC).

Your job is to extract EVERY possible field from the provided Test Certificate document.
Return ONLY a valid JSON object. No explanation, no markdown, no code blocks. Just raw JSON.

Rules:
- Extract values EXACTLY as they appear in the document. Do not paraphrase or summarize.
- If a field is not found in the document, set its value to null.
- For fields with multiple rows (e.g., multiple coils/packets), return an array of objects.
- For boolean fields, return true/false/null.
- For numeric fields, return numbers not strings (e.g., 0.1580 not "0.1580").
- For process route flags (BOF, ARS, LHF, CCM, RH, HSM), return true if present, false if not.
- Extract ALL rows from chemical composition table and mechanical properties table.

Here is the complete field schema to extract:

{
  "document_type": null,
  "certificate_type": null,
  "test_certificate_number": null,
  "certificate_date": null,
  "document_page_number": null,
  "total_pages": null,
  "document_template_code": null,
  "certification_type": null,
  "standard_name": null,
  "grade": null,
  "specification": null,

  "manufacturer_name": null,
  "manufacturing_plant": null,
  "plant_location": null,
  "district": null,
  "state": null,
  "country": null,
  "registered_office": null,
  "cin_number": null,
  "bis_license_number": null,
  "authorized_signatory": null,
  "signatory_designation": null,

  "customer_name": null,
  "consignee_name": null,
  "consignee_address": null,
  "customer_location": null,

  "sales_order_number": null,
  "sales_order_date": null,
  "billing_document_number": null,
  "invoice_number": null,

  "mode_of_transport": null,
  "vehicle_number": null,

  "conforms_to_standard": null,
  "conforms_to_is2062": null,
  "conforms_to_en10204_type31": null,
  "conforms_to_rohs": null,
  "radioactive_content_compliance": null,
  "dimensional_tolerance_compliance": null,
  "overall_material_conformance": null,

  "product_name": null,
  "product_category": null,
  "material_type": null,
  "material_grade": null,
  "specification_grade": null,
  "steel_type": null,
  "killing_practice": null,
  "manufacturing_process_route": null,

  "process_bof": null,
  "process_ars": null,
  "process_lhf": null,
  "process_ccm": null,
  "process_rh": null,
  "process_hsm": null,

  "chemical_spec_c_min": null, "chemical_spec_c_max": null,
  "chemical_spec_mn_min": null, "chemical_spec_mn_max": null,
  "chemical_spec_s_min": null, "chemical_spec_s_max": null,
  "chemical_spec_p_min": null, "chemical_spec_p_max": null,
  "chemical_spec_si_min": null, "chemical_spec_si_max": null,
  "chemical_spec_al_min": null, "chemical_spec_al_max": null,
  "chemical_spec_n_min": null, "chemical_spec_n_max": null,
  "chemical_spec_b_min": null, "chemical_spec_b_max": null,
  "chemical_spec_nb_min": null, "chemical_spec_nb_max": null,
  "chemical_spec_v_min": null, "chemical_spec_v_max": null,
  "chemical_spec_ti_min": null, "chemical_spec_ti_max": null,
  "chemical_spec_cr_min": null, "chemical_spec_cr_max": null,
  "chemical_spec_mo_min": null, "chemical_spec_mo_max": null,
  "chemical_spec_ni_min": null, "chemical_spec_ni_max": null,
  "chemical_spec_cu_min": null, "chemical_spec_cu_max": null,
  "chemical_spec_mae_min": null, "chemical_spec_mae_max": null,
  "chemical_spec_carbon_equivalent_min": null, "chemical_spec_carbon_equivalent_max": null,

  "tensile_test_direction_requirement": null,
  "yield_strength_min_requirement": null,
  "yield_strength_max_requirement": null,
  "ultimate_tensile_strength_min_requirement": null,
  "ultimate_tensile_strength_max_requirement": null,
  "gauge_length_requirement": null,
  "elongation_min_requirement": null,
  "elongation_max_requirement": null,
  "yield_to_tensile_ratio_requirement": null,
  "bend_test_direction_requirement": null,
  "bend_diameter_requirement": null,
  "bend_test_requirement": null,
  "cvn_impact_requirement": null,
  "hardness_requirement": null,
  "grain_size_requirement": null,
  "inclusion_rating_requirement": null,
  "hole_expansion_ratio_requirement": null,
  "erichsen_cupping_requirement": null,
  "strain_age_embrittlement_requirement": null,

  "batches": [
    {
      "cast_number": null,
      "heat_number": null,
      "coil_number": null,
      "packet_number": null,
      "batch_identifier": null,
      "lot_number": null,
      "thickness": null,
      "width": null,
      "length": null,
      "nominal_size": null,
      "pieces_count": null,
      "quantity_mt": null,
      "carbon_percent": null,
      "manganese_percent": null,
      "sulphur_percent": null,
      "phosphorus_percent": null,
      "silicon_percent": null,
      "aluminium_percent": null,
      "nitrogen_ppm": null,
      "boron_ppm": null,
      "niobium_percent": null,
      "vanadium_percent": null,
      "titanium_percent": null,
      "chromium_percent": null,
      "molybdenum_percent": null,
      "nickel_percent": null,
      "copper_percent": null,
      "micro_alloying_elements_percent": null,
      "carbon_equivalent_percent": null,
      "tensile_test_direction": null,
      "yield_strength_mpa": null,
      "ultimate_tensile_strength_mpa": null,
      "gauge_length": null,
      "elongation_percent": null,
      "yield_to_tensile_ratio": null,
      "bend_test_direction": null,
      "bend_diameter": null,
      "bend_test_result": null,
      "cvn_impact_direction": null,
      "cvn_impact_temperature_c": null,
      "cvn_impact_average_energy_j": null,
      "hardness_hv10": null,
      "hardness_hrb": null,
      "grain_size": null,
      "inclusion_rating": null,
      "hole_expansion_ratio": null,
      "erichsen_cupping_value": null,
      "strain_age_embrittlement_test": null
    }
  ],

  "total_packets": null,
  "total_coils": null,
  "total_batches": null,
  "total_pieces": null,
  "total_weight_mt": null,
  "heat_count": null,
  "unique_cast_count": null,

  "chemical_composition_pass": null,
  "mechanical_properties_pass": null,
  "bend_test_pass": null,
  "dimensional_compliance_pass": null,
  "overall_pass_fail": null,

  "radioactive_compliance_statement": null,
  "rohs_compliance_statement": null,
  "dimensions_and_tolerance_statement": null,
  "certification_statement": null,
  "remarks": null,

  "thickness_unit_unit": null,
  "length_unit": null,
  "weight_unit": null,
  "chemistry_unit": null,
  "nitrogen_unit": null,
  "boron_unit": null,
  "yield_strength_unit": null,
  "tensile_strength_unit": null,
  "elongation_unit": null,
  "hardness_unit": null,
  "impact_energy_unit": null
}

Return ONLY the filled JSON object now. No other text.
"""


def is_llm_configured() -> bool:
    return bool(os.getenv("LLM_API_BASE_URL") and os.getenv("LLM_API_KEY"))


def _mime_type(path: Path) -> str:
    guessed = mimetypes.guess_type(path.name)[0]
    if guessed:
        return guessed
    if path.suffix.lower() == ".pdf":
        return "application/pdf"
    return "application/octet-stream"


def _extract_json_payload(response_json: Any) -> dict[str, Any]:
    if isinstance(response_json, dict):
        for key in ("json", "data", "output", "result"):
            value = response_json.get(key)
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                parsed = _parse_json_from_text(value)
                if parsed:
                    return parsed

        for key in ("text", "content", "message", "response"):
            value = response_json.get(key)
            if isinstance(value, str):
                parsed = _parse_json_from_text(value)
                if parsed:
                    return parsed

        choices = response_json.get("choices")
        if isinstance(choices, list) and choices:
            parsed = _extract_json_payload(choices[0])
            if parsed:
                return parsed

    if isinstance(response_json, str):
        parsed = _parse_json_from_text(response_json)
        if parsed:
            return parsed

    raise ValueError("LLM response did not contain a parseable JSON object.")


def _parse_json_from_text(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None


def invoke_document_extraction(path: str | Path, tc_format: str = "auto") -> dict[str, Any]:
    input_path = Path(path)
    configured_url = os.environ["LLM_API_BASE_URL"].rstrip("/")
    api_key = os.environ["LLM_API_KEY"]
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    user_id = os.getenv("LLM_USER_ID", "")
    timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))

    prompt = LLM_PROMPT
    # Do not add the selected output format to the extraction prompt. Format
    # selection is for the generated Excel layout, not for filtering TC rows.

    payload = {
        "model": model,
        "user_id": user_id,
        "prompt": prompt,
        "stream": False,
        "stream_mode": "passthrough",
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "32768")),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0")),
        "web_search": False,
        "attachments": [
            {
                "name": input_path.name,
                "mime_type": _mime_type(input_path),
                "data_base64": base64.b64encode(input_path.read_bytes()).decode("ascii"),
            }
        ],
    }
    invoke_url = configured_url if configured_url.endswith("/api/invoke") else f"{configured_url}/api/invoke"
    response = requests.post(
        invoke_url,
        headers={"Content-Type": "application/json", "x-api-key": api_key},
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    return _extract_json_payload(response.json())
