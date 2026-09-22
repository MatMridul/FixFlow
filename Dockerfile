FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY catalog/ catalog/
COPY resolution/ resolution/
COPY eval/ eval/
COPY data/ data/
COPY tests/ tests/

# api/ (Dev A) doesn't exist yet. Until it does, the container's job is to
# be a working, reproducible test + eval gate - swap this CMD for
# `uvicorn api.main:app --host 0.0.0.0 --port 8000` once /v1/troubleshoot
# and /health are built (FixFlow_TwoDev_Plan.md P0, Dev A).
CMD ["sh", "-c", "python -m pytest tests/ -v && python -m eval.run_screen_eval"]
