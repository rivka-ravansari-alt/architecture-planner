# Production image for Google Cloud Run (and other container hosts).
# Cloud Run sets PORT (default 8080); do not hard-code the listen port.

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Default for Cloud Run: persist generations to GCS (override via service env vars).
ENV OBJECT_STORAGE_PROVIDER=gcs \
    OBJECT_STORAGE_BUCKET=archsari-generations-prod

EXPOSE 8080

# --proxy-headers: honor X-Forwarded-* from Cloud Run / nginx (HTTPS, host).
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
