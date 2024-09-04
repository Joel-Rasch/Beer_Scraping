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
    name = 'nettospider'
    allowed_domains = 'netto-online.de'
    start_urls = ['https://www.netto-online.de/bier']

    def __init__(self, *args, **kwargs):
        super(BeerSpider, self).__init__(*args, **kwargs)
        self.db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password')
        self.site = 1

    def parse(self, response):
        products = response.css('li.product-list__item')
        beer_data = {}

        for product in products:

            items = {
                'name': product.css('div.product__title').get().replace('<div class="product__title product__title__inner tc-product-name  line-clamp-2">','').replace('</div>','').strip(),
                'quantity': '1',
                'unit': 'L',
                'price': product.css('span.product-property__base-price').get().replace('<span class="product-property product-property__base-price">','').replace('<span class="product__current-price--digits-after-comma">','').replace('</span> / l</span>','').replace('– / l</span>','0').strip(),
                'currency': '€',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'reseller': 'netto-online.de',
                'zipcode': '0000',
                'alcohol_contet': '0000'
            }
            beer_data.append(items)

        beer_data['name'] = re.search(r"^[^\d\s]+(?:\s[^\d\s]+)*",beer_data['name'])[0]

        try:
            result = self.db.process_entries(beer_data)
            self.logger.info(f"Inserted data: {result}")
        except Exception as e:
            self.logger.error(f"Error inserting data: {e}")

        yield beer_data