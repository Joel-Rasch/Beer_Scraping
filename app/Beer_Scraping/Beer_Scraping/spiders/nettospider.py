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
    name = 'nettospider'
    allowed_domains = 'netto-online.de'
    start_urls = ['https://www.netto-online.de/bier']

    def parse(self, response):
        products = response.css('li.product-list__item')

        for product in products:

            yield {
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