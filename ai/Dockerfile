FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-ron \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    libtesseract-dev \
    libleptonica-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Bigger timeout + retries for slow / flaky network connections
RUN pip install --no-cache-dir --default-timeout=300 --retries 5 -r requirements.txt

COPY . .

RUN mkdir -p /app/models/saved_models /app/models/reports /app/models/training_data

COPY entrypoint.sh .
# Strip any CRLF line endings (happens when cloned on Windows without .gitattributes)
# then make executable. Without this, Linux errors with:
#   exec ./entrypoint.sh: no such file or directory
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

EXPOSE 8001

CMD ["./entrypoint.sh"]
