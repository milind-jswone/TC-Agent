FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV TESSERACT_CMD=/usr/bin/tesseract

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY SupplierTCAgent/Tools/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY SupplierTCAgent /app/SupplierTCAgent

WORKDIR /app/SupplierTCAgent/Tools

CMD ["sh", "-c", "uvicorn webhook_listener:app --host 0.0.0.0 --port ${PORT:-8080}"]
