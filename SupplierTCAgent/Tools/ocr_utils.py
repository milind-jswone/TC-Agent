from __future__ import annotations

import os
from pathlib import Path

from PIL import Image


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


def is_image_file(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def ocr_image(image: Image.Image) -> str:
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError(
            "OCR requires pytesseract. Install requirements.txt before processing image/scanned files."
        ) from exc

    tesseract_cmd = os.getenv("TESSERACT_CMD")
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    try:
        return pytesseract.image_to_string(image, config="--psm 6")
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "OCR requires the Tesseract application. Install Tesseract OCR and set TESSERACT_CMD if it is not on PATH."
        ) from exc


def ocr_image_file(path: str | Path) -> str:
    with Image.open(path) as image:
        return ocr_image(image)


def ocr_pdf_file(path: str | Path, scale: float = 2.5) -> str:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise RuntimeError(
            "OCR for scanned PDFs requires pypdfium2. Install requirements.txt before processing scanned PDFs."
        ) from exc

    pdf = pdfium.PdfDocument(str(path))
    page_text: list[str] = []
    for page_index in range(len(pdf)):
        page = pdf[page_index]
        bitmap = page.render(scale=scale).to_pil()
        page_text.append(ocr_image(bitmap))
    return "\n".join(page_text)
