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
CMD xvfb-run -a python /app/John/Lidl_playwright_crawler.py & \
    xvfb-run -a python /app/John/Metro_playwright_crawler.py & \
    xvfb-run -a python /app/Sophie/flaschenpost_crawler.py & \
    xvfb-run -a python /app/Sophie/goflink_crawler.py & \
    cd /app/Beer_Scraping && scrapy crawl banachspider & \
    cd /app/Beer_Scraping && scrapy crawl product_links & \
    cd /app/Beer_Scraping && scrapy crawl edekaspider & \
    cd /app/Beer_Scraping && scrapy crawl hofmanspider & \
    cd /app/Beer_Scraping && scrapy crawl kauflandspider & \
    cd /app/Beer_Scraping && scrapy crawl nettospider & \
    cd /app/Beer_Scraping && scrapy crawl trinkgut_spider  & \
    xvfb-run -a python /app/John/Rewe_playwright_crawler.py