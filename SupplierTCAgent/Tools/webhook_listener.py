from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from generate_tc_output import available_tc_formats, process_supplier_tc


app = FastAPI(title="Supplier TC Agent")
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


class TCProcessRequest(BaseModel):
    file_name: str
    file_content_base64: str
    tc_format: str = "auto"
    master_file_name: str | None = None
    master_file_base64: str | None = None


def _process_pdf(path: Path, tc_format: str = "auto", master_path: Path | None = None) -> dict[str, Any]:
    try:
        kwargs: dict[str, Any] = {}
        if master_path is not None:
            kwargs["master_path"] = master_path
        return process_supplier_tc(
            path,
            **kwargs,
            include_file_content=True,
            include_master_file_content=master_path is not None,
            tc_format=tc_format,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tc/formats")
def tc_formats() -> dict[str, Any]:
    return {"formats": available_tc_formats()}


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
        master_path = None
        if request.master_file_base64:
            master_name = request.master_file_name or "Master TC.xlsx"
            if Path(master_name).suffix.lower() != ".xlsx":
                raise HTTPException(status_code=400, detail="Master file must be an .xlsx workbook.")
            master_path = Path(tmpdir) / master_name
            try:
                master_path.write_bytes(base64.b64decode(request.master_file_base64))
            except Exception as exc:
                raise HTTPException(status_code=400, detail="Invalid base64 master workbook content.") from exc
        result = _process_pdf(pdf_path, tc_format=request.tc_format, master_path=master_path)
    return JSONResponse(result)
