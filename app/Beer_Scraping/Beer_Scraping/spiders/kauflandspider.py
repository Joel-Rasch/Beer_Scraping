import scrapy
from datetime import datetime
import os
import sys

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
    start_urls = ["https://www.kaufland.de/bier"]

    def parse(self, response):
        products = response.css('section.product__data')

        for product in products:

            yield {
                'name': product.css('div.product__title').get().replace('<div class="product__title">','').replace('</div>','').strip(),
                'quantity': '1',
                'unit': 'L',
                'price': product.css('div.product__base-price').get().replace('<div class="product__base-price">','').replace('<span>','').replace('1l = ','').replace(' €','').replace('</span></div>','').strip(),
                'currency': '€',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'reseller': product.css('strong.product__seller-info-name').get().replace('<strong class="product__seller-info-name">','').replace('</strong>','').replace('            ','').replace('/n','').strip(),
                'zipcode': '0000',
                'alcohol_contet': '0000'
            }

        try:
            result = self.db.process_entries(beer_data)
            self.logger.info(f"Inserted data: {result}")
        except Exception as e:
            self.logger.error(f"Error inserting data: {e}")