FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install watchdog
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "hypertube.wsgi", "--reload"]
