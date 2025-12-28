FROM python:3.11-slim

WORKDIR /app

# Install system deps required for some libraries (minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libxml2-dev libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "src/bot.py"]
