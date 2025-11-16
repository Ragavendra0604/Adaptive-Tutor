FROM python:3.10-slim

WORKDIR /app

COPY ./requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Copy .env to /app/.env to ensure FastAPI can read it
COPY .env /app/.env

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
