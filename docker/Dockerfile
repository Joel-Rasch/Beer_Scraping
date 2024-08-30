# Basis-Image mit Python 3.9
FROM python:3.9

# Arbeitsverzeichnis erstellen
WORKDIR /app

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    curl \
    xvfb \
    xauth \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir scrapy playwright

# Playwright installieren
RUN playwright install --with-deps

# Anwendungscode kopieren
COPY app/ /app/

# Ausführungsbefehl
CMD xvfb-run -a python /app/Playwright/Lidl_playwright_crawler_neu.py & \
    xvfb-run -a python /app/Playwright/Metro_playwright_crawler_neu.py & \
    xvfb-run -a python /app/Playwright/Rewe_playwright_crawler_neu.py & \
    cd /app/Beer_Scraping && scrapy crawl banachspider