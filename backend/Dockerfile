FROM python:3.10

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install watchdog
COPY . .
RUN mkdir -p /app/downloads
CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:8000 hypertube.wsgi --reload"]
