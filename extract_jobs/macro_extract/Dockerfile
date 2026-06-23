FROM python:3.10-slim

WORKDIR /app

COPY extract_jobs/macro_extract/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY extract_jobs/ ./extract_jobs/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "-m", "extract_jobs.macro_extract.flows.fetch_fx_rate"]
