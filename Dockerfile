FROM python:3.11-slim

# Tizim paketlarini yangilash
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha fayllarini nusxalash
COPY . .

# Ishchi papka yaratish
RUN mkdir -p /app/workspace

ENV PYTHONUNBUFFERED=1
ENV WORKSPACE_DIR=/app/workspace

CMD ["python", "main.py", "--bot"]
