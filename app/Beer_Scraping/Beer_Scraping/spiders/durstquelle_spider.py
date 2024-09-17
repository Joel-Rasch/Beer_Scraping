import scrapy
import re
from datetime import datetime
import pandas
import os
import sys

# Get the current directory of this file
current_directory = os.path.dirname(os.path.realpath(__file__))

# Get the parent directory
parent_directory = os.path.dirname(current_directory)

# Add the parent directory to sys.path
sys.path.append(parent_directory)

from Dbuploader import BeerDatabase

class DurstquelleSpider(scrapy.Spider):
    name = "durstquelle_spider"
    allowed_domains = ['durstquelle.de']
    start_urls = ['https://durstquelle.de/biere.html?product_list_limit=36'] 

    def __init__(self, *args, **kwargs):
        super(DurstquelleSpider, self).__init__(*args, **kwargs)
        self.db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password')

    def parse(self, response):
        # Extract all product links
        links = response.css('a.product-item-link::attr(href)').extract()
        for link in links:
            # Follow each link to scrape the product details
            yield response.follow(link, self.parse_product)
        
    def parse_product(self, response):
        beer_data = {}
        # Extract the product title
        title = response.css('h1.page-title span.base::text').get()
        # Preperation to replace missing 'l' if needed
        product_string = re.sub(r"(\d+(?:,\d+)?)(\s*MW|\s*$)", r"\1l\2", title)

        # Regular expression to parse product string
        pattern = r"^(.*?)(\d+x)?(\d+(?:,\d+)?)([a-zA-Z]+)"
        match = re.search(pattern, product_string)

        if match:
            name = match.group(1).strip()  # Produktname
            multiplier = match.group(2)    # Zahl vor 'x', wenn vorhanden
            quantity = match.group(3).replace(",", ".")  # Zahl nach 'x'
            unit = match.group(4)  # Einheit

            if multiplier:  # Wenn ein 'x' und ein Multiplikator vorhanden sind
                multiplier = int(multiplier[:-1])  # Entferne das 'x' und konvertiere zu int
                quantity = float(quantity) * multiplier
        else:
            name = product_string, 
            quantity = float(0.0)
            unit = ""

        # Extract the product price
        price_curr = response.css('.price::text').get()
        # Split the price into currency and amount
        price = price_curr.split()[0].replace(",", ".")
        currency = price_curr.split()[1]
        
        # Reseller & Crawling Details
        current_date = datetime.now().strftime('%Y-%m-%d')
        reseller = "Durstquelle"
        zipcode = "hamburg"
        
        beer_data =  {'name': name,
               'quantity': quantity,
               'unit': unit,
               'price': price,
               'currency': currency,
               'alcohol_content': None,
               'date': current_date,
               'reseller': reseller,
               'zipcode': zipcode,
               'url':response.url}
        
        try:
            result = self.db.process_entries(beer_data)
            self.logger.info(f"Inserted data: {result}")
        except Exception as e:
            self.logger.error(f"Error inserting data: {e}")

        yield beer_data
        
