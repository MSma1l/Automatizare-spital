FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=300 --retries 5 -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads

COPY entrypoint.sh .
# Strip any CRLF line endings (happens when cloned on Windows without .gitattributes)
# then make executable. Without this, Linux errors with:
#   exec ./entrypoint.sh: no such file or directory
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

EXPOSE 8000

CMD ["./entrypoint.sh"]
