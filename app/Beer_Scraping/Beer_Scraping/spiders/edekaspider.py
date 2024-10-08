import scrapy
from datetime import datetime
import os
import sys
import re
import logging

# Get the current directory of this file
current_directory = os.path.dirname(os.path.realpath(__file__))

# Get the parent directory
parent_directory = os.path.dirname(os.path.dirname(os.path.dirname(current_directory)))

# Add the parent directory to sys.path
sys.path.append(parent_directory)

# Import the BeerDatabase class
from Dbuploader import BeerDatabase

class BeerSpider(scrapy.Spider):
    name = 'edekaspider'
    allowed_domains = ['edeka24.de']
    start_urls = ['https://www.edeka24.de/Wein-Spirituosen/Bier/']

    def __init__(self, *args, **kwargs):
        super(BeerSpider, self).__init__(*args, **kwargs)
        self.db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password')
    
    
    def parse(self, response):
        # Extract all product links on the initial page
        products = response.css('div.product-details a::attr(href)').getall()
        for link in products:
            full_url = response.urljoin(link)
            yield scrapy.Request(url=full_url, callback=self.parse_beer)
    
    def parse_beer(self, response):
        # Extract product details from the product page
        items = {}
        name = response.css('h1::text').get()
        price_text = response.css('li.price-note::text').get()

        if name:
            name = name.strip()
            # Search for a name pattern and make sure to get the first group correctly
            name_search = re.search(r"^[^\d\s]+(?:\s[^\d\s]+)*", name)
            if name_search:
                name = name_search.group(0)

        try:
            # Beispiel für das Extrahieren eines Preises mit einem regulären Ausdruck
            price_text = re.search(r'\d+,\d+', response.text)  # Beispiel: Suchmuster
            if price_text:
                price = price_text.group().replace(',', '.')
                # Weiterverarbeitung des Preises
            else:
                # Falls kein Preis gefunden wird, logge eine Warnung
                logging.warning(f"No price found on {response.url}")
                # Optional: Setze den Preis auf einen Standardwert oder überspringe die Verarbeitung
                price = ''
        except Exception as e:
            logging.error(f"Error processing {response.url}: {e}")

        
        items['name'] = name
        items['quantity'] = int(1)
        items['unit'] = 'L'
        items['price'] = float(price)
        items['currency'] = '€'
        items['date'] = datetime.now().strftime('%Y-%m-%d')
        items['reseller'] = 'Edeka24'
        items['zipcode'] = ''
        items['url'] = response.url
        
        alcohol_content = response.xpath('//strong[contains(text(), "Alkoholgehalt:")]/following-sibling::text()').re_first(r'\b\d+\.\d+%')

        alcohol_content = alcohol_content.replace('%', '').replace(',','.') if alcohol_content is not None else None
        alcohol_content = float(alcohol_content) if alcohol_content is not None else None
        
        items['alcohol_content'] = alcohol_content

        try:
            result = self.db.process_entries(items)
            self.logger.info(f"Inserted data: {result}")
        except Exception as e:
            self.logger.error(f"Error inserting data: {e}")

        yield items
