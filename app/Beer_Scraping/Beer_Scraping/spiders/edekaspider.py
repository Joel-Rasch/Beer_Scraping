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
    name = 'edekaspider'
    allowed_domains = 'edeka24.de'
    start_urls = ['https://www.edeka24.de/Wein-Spirituosen/Bier']

    def parse(self, response):
        products = response.css('div.product-item')
        beer_data = {}

        for product in products:

            items = {
                'name': product.css('a.title::attr(title)').get().strip(),
                'quantity': '1',
                'unit': 'L',
                'price': product.css('p.price-note').get().replace('<p class="price-note">','').replace('zzgl. 0,25 € Pfand','').replace('</p>','').replace('zzgl. 1,00 € Pfand','').replace('€/l','').strip(),
                'currency': '€',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'reseller': 'Edeka24.de',
                'zipcode': '0000',
                'alcohol_content': '0000'
            }
            beer_data.append(items)

        try:
            result = self.db.process_entries(beer_data)
            self.logger.info(f"Inserted data: {result}")
        except Exception as e:
            self.logger.error(f"Error inserting data: {e}")

        yield beer_data