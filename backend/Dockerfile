FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app

# Cloud Run injeta a variável PORT dinamicamente; localmente usa 8000.
ENV PORT=8000
EXPOSE 8000

CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
