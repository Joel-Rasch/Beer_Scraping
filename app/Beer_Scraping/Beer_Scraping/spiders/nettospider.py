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
    allowed_domains = ['netto-online.de']
    start_urls = ['https://www.netto-online.de/bier/']

    def __init__(self, *args, **kwargs):
        super(BeerSpider, self).__init__(*args, **kwargs)
        self.db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password')

    def parse(self, response):
        # Extract all product links on the initial page
        products = response.css('ul.product-list a::attr(href)').getall()
        for link in products:
            full_url = response.urljoin(link)
            yield scrapy.Request(url=full_url, callback=self.parse_beer)

    def parse_beer(self, response):
        # Extract product details from the product page
        items = {}
        
        #Name
        name = response.xpath('//h1/text()').get()
        
        if name:
            name = name.strip()
            # Search for a name pattern and make sure to get the first group correctly
            name_search = re.search(r"^[^\d\s]+(?:\s[^\d\s]+)*", name)
            if name_search:
                name = name_search.group(0)
        
        items['name'] = name

        items['url'] = response.url
        
        # Extract price parts
        base_price_1 = response.css('.product-property__base-price .product-property__value::text').get(default='')
        base_price_2 = response.css('span.product__current-price--digits-after-comma::text').get(default='')

        # Concatenate and clean price text
        price_text = f'{base_price_1}{base_price_2}'

        # Check if price_text is not empty before processing
        if price_text is not None:
            # Replace commas with dots for decimal consistency and search for the price
            price_search = re.search(r"\d+\.\d+", price_text)
            price = price_search.group().replace(',','.') if price_search else None
        else:
            price = None
        
        items['price'] = float(price)
        items['date'] = datetime.now().strftime('%Y-%m-%d')
        items['reseller'] = 'Netto Online'
        items['quantity'] = 1
        items['unit'] = 'L'
        items['currency'] = '€'
        items['zipcode'] = ''
        
        #alcohol content
        alcohol_content = response.css('div.food-labeling__text p::text').re_first(r'Alkoholgehalt: (\d+,\d+ %)')
        
        if alcohol_content is not None and '%' in alcohol_content:
            alcohol_content = alcohol_content.replace('%', '').replace(',','.')
        
        items['alcohol_content'] = float(alcohol_content) if alcohol_content is not None else None
        

        try:
            result = self.db.process_entries(items)
            self.logger.info(f"Inserted data: {result}")
        except Exception as e:
            self.logger.error(f"Error inserting data: {e}")

        yield items
