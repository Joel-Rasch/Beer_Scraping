import scrapy
from datetime import datetime
import os
import sys
import re

# Get the current directory of this file
current_directory = os.path.dirname(os.path.realpath(__file__))

# Get the parent directory
parent_directory = os.path.dirname(os.path.dirname(os.path.dirname(current_directory)))

# Add the parent directory to sys.path
sys.path.append(parent_directory)

# Import the BeerDatabase class
from Dbuploader import BeerDatabase

class BeerSpider(scrapy.Spider):
    name = "kauflandspider"
    allowed_domains = ["kaufland.de"]
    start_urls = ["https://www.kaufland.de/category/2551/p1"]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 5.0,  # Sekunden zwischen den Anfragen
        'LOG_LEVEL': 'DEBUG',    # Setzt das Log-Level
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 5.0,
        'AUTOTHROTTLE_MAX_DELAY': 60.0,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'AUTOTHROTTLE_DEBUG': True
    }
    
    def __init__(self, *args, **kwargs):
        super(BeerSpider, self).__init__(*args, **kwargs)
        self.db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password')
        self.site = 1

    def parse(self, response):
        # Extract all product links on the initial page
        products = response.css('div.results.results--grid a::attr(href)').getall()
        
        for link in products:
            full_url = response.urljoin(link)
            yield scrapy.Request(url=full_url, callback=self.parse_beer)
            logging.debug(f"Product URL: {full_url}")
        
        if not response.css('div.message-info.empty').get():
            if self.site < 10:
                self.site += 1
                next_page_url = f"https://www.kaufland.de/category/2551/p{self.site}"
                yield scrapy.Request(url=next_page_url, callback=self.parse)
                logging.debug(f"Next Page URL: {next_page_url}")
    
    def parse_beer(self, response):
        # Beispiel, wie man Artikelinformationen extrahiert
        items = {}
        
        #Name
        raw_name = response.css('div.above-the-fold__title-container h1::attr(title)').get()
        name_match = re.search(r"^[^\d\s]+(?:\s[^\d\s]+)*", raw_name)
        if name_match:
            items['name'] = name_match.group(0)  # Verwende .group(0) statt [0] für Klarheit
        else:
            items['name'] = 'Unknown'
        
        items['quantitiy'] = '1'
        items['unit'] = 'L'
        
        price_text = response.css('span.rd-price-information__price::text').get().strip()
        
        if price_text is not None:
            price_search = re.search(r"\d+.\d+", price_text)
            price = price_search.group().replace(',','.') if price_search else None
        else:
            price = ''
        
        items['price'] = price
        
        items['currency'] = '€'
        
        items['date'] = datetime.now().strftime('%Y-%m-%d')
        items['reseller'] = 'Kaufland'
        items['zipcode'] = ''
        items['alcohol_contet'] = ''
        

        try:
            result = self.db.process_entries(beer_data)
            self.logger.info(f"Inserted data: {result}")
        except Exception as e:
            self.logger.error(f"Error inserting data: {e}")

        yield items