FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY api /app/api
COPY metrics_engine /app/metrics_engine
COPY semantic_layer /app/semantic_layer
COPY spark /app/spark

EXPOSE 8000
