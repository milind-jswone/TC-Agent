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
Extract supplier test certificate data from the attached document.

Return only valid JSON. Do not wrap it in markdown. Use this exact shape:
{
  "test_certificate_no": "",
  "date": "",
  "product": "",
  "so_no": "",
  "so_date": "",
  "customer_name_address": "",
  "specification": "",
  "grade": "",
  "billing_doc_no": "",
  "invoice_no": "",
  "vehicle_no": "",
  "total_weight_mt": null,
  "total_coils_packets": null,
  "line_items": [
    {
      "batch_no": "",
      "coil_no": "",
      "nominal_size": "",
      "pcs": "",
      "net_weight_mt": null,
      "thickness_mm": null,
      "width_mm": null,
      "length_mm": null,
      "c": null,
      "s": null,
      "p": null,
      "si": null,
      "al": null,
      "n": null,
      "nb": null,
      "v": null,
      "ti": null,
      "nb_v_ti": null,
      "tensile_direction": "",
      "ys": null,
      "uts": null,
      "gl": "",
      "elongation": null,
      "ys_uts_ratio": null,
      "bend_direction": "",
      "bend_radius": "",
      "bend_result": ""
    }
  ],
  "warnings": []
}

Rules:
- Keep numbers as numbers, not strings, wherever possible.
- If a value is missing, use null for numeric fields and an empty string for text fields.
- Join chemical and mechanical rows by heat/batch number and coil/packet number.
- Calculate nb_v_ti as Nb + V + Ti when those values are available.
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
    base_url = os.environ["LLM_API_BASE_URL"].rstrip("/")
    api_key = os.environ["LLM_API_KEY"]
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    user_id = os.getenv("LLM_USER_ID", "")
    timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))

    prompt = LLM_PROMPT
    if tc_format and tc_format != "auto":
        prompt += f"\nSelected TC format: {tc_format}\n"

    payload = {
        "model": model,
        "user_id": user_id,
        "prompt": prompt,
        "stream": False,
        "stream_mode": "passthrough",
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "8192")),
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
    response = requests.post(
        f"{base_url}/api/invoke",
        headers={"Content-Type": "application/json", "x-api-key": api_key},
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    return _extract_json_payload(response.json())
