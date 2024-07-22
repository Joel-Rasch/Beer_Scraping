# Verwenden Sie ein offizielles Python-Runtime-Image als Basis
FROM python:3.9-slim

# Setzen Sie das Arbeitsverzeichnis im Container
WORKDIR /app

# Kopieren Sie die Anforderungsdatei und installieren Sie die Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieren Sie den Projektcode in den Container
COPY app/ .

# Führen Sie die Anwendung aus, wenn der Container gestartet wird
CMD ["python", "main.py"]