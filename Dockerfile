FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

RUN addgroup --system app && adduser --system --ingroup app app
USER app

# Railway supplies PORT at runtime; 8000 documents the local default.
EXPOSE 8000

# Keep exactly one worker: each process would otherwise start its own scheduler.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-8000}\" --workers 1"]
