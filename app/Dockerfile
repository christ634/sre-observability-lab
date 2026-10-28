FROM python:3.12-slim

WORKDIR /srv/app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# opentelemetry-instrument aplica auto-instrumentación (FastAPI, requests, logging)
CMD ["opentelemetry-instrument", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
