# Basis-Image mit Python 3.9
FROM python:3.9

# Arbeitsverzeichnis erstellen
WORKDIR /app

ARG DEBIAN_FRONTEND=noninteractive

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    curl \
    xvfb \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libnss3 \
    libpango-1.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libnspr4 \
    libnss3 \
    libxss1 \
    fonts-liberation \
    fonts-noto-color-emoji \
    locales \
    xdg-utils \
    libgbm-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Setzen Sie die Locale
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN locale-gen de_DE.UTF-8

# Python-Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir scrapy playwright

# Playwright installieren
RUN playwright install --with-deps chromium

# Anwendungscode kopieren
COPY app/ /app/

# Umgebungsvariable für Display setzen
ENV DISPLAY=:99

# Entrypoint-Skript
RUN echo '#!/bin/bash\n\
Xvfb :99 -screen 0 1024x768x16 &\n\
python /app/John/Metro_playwright_crawler.py \n\
Xvfb :99 -screen 0 1024x768x16 &\n\
python /app/John/Lidl_playwright_crawler.py \n\
Xvfb :99 -screen 0 1024x768x16 &\n\
python /app/Sophie/flaschenpost_crawler.py \n\
Xvfb :99 -screen 0 1024x768x16 &\n\
python /app/Sophie/goflink_crawler.py \n\
cd /app/Beer_Scraping && scrapy crawl banachspider \n\
cd /app/Beer_Scraping && scrapy crawl banachspider \n\
cd /app/Beer_Scraping && scrapy crawl product_links \n\
cd /app/Beer_Scraping && scrapy crawl edekaspider \n\
cd /app/Beer_Scraping && scrapy crawl hofmanspider \n\
cd /app/Beer_Scraping && scrapy crawl kauflandspider \n\
cd /app/Beer_Scraping && scrapy crawl nettospider \n\
cd /app/Beer_Scraping && scrapy crawl trinkgut_spider \n\
Xvfb :99 -screen 0 1024x768x16 &\n\
python /app/John/Rewe_playwright_crawler.py \n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

# Entrypoint-Skript
ENTRYPOINT ["/entrypoint.sh"]


