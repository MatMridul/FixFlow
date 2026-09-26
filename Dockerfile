FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY schema.py schema.py
COPY api/ api/
COPY cache/ cache/
COPY enrichment/ enrichment/
COPY extraction/ extraction/
COPY validation/ validation/
COPY catalog/ catalog/
COPY resolution/ resolution/
COPY eval/ eval/
COPY data/ data/
COPY tests/ tests/

EXPOSE 8000

# FixFlow Full Engine Server
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
