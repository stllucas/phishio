# Configuração do contêiner Docker para a API FastAPI do Phishio.
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/runtime

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m nltk.downloader stopwords punkt

COPY . .

CMD ["uvicorn", "runtime.main:app", "--host", "0.0.0.0", "--port", "8000"]
