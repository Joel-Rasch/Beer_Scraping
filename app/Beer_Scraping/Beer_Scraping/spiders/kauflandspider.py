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
    start_urls = ["https://www.kaufland.de/bier"]

    def __init__(self, *args, **kwargs):
        super(BeerSpider, self).__init__(*args, **kwargs)
        self.db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password')
        self.site = 1

    def parse(self, response):
        products = response.css('section.product__data')
        beer_data = []

        for product in products:

            items = {
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
            items['name'] = re.search(r"^[^\d\s]+(?:\s[^\d\s]+)*", items['name'])[0]

        try:
            result = self.db.process_entries(beer_data)
            self.logger.info(f"Inserted data: {result}")
        except Exception as e:
            self.logger.error(f"Error inserting data: {e}")

        yield beer_data