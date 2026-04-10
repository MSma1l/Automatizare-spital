FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/models/saved_models /app/models/reports /app/models/training_data

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8001

CMD ["./entrypoint.sh"]
