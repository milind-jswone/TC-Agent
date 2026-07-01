from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from generate_tc_output import process_supplier_tc


app = FastAPI(title="Supplier TC Agent")
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


class TCProcessRequest(BaseModel):
    file_name: str
    file_content_base64: str


def _process_pdf(path: Path) -> dict[str, Any]:
    try:
        return process_supplier_tc(path, include_file_content=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tc/process")
async def process_tc_upload(file: UploadFile = File(...)) -> JSONResponse:
    if not file.filename or Path(file.filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and common image supplier TC files are supported.")
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / file.filename
        pdf_path.write_bytes(await file.read())
        result = _process_pdf(pdf_path)
    return JSONResponse(result)


@app.post("/tc/process-base64")
def process_tc_base64(request: TCProcessRequest) -> JSONResponse:
    if Path(request.file_name).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and common image supplier TC files are supported.")
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / request.file_name
        try:
            pdf_path.write_bytes(base64.b64decode(request.file_content_base64))
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid base64 PDF content.") from exc
        result = _process_pdf(pdf_path)
    return JSONResponse(result)
