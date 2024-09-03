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
    name = 'biertaxispider'
    start_urls = ['https://www.biertaxi-duesseldorf.de/shop/:group_biere-flasche.2036']

    def __init__(self, *args, **kwargs):
        super(BeerSpider, self).__init__(*args, **kwargs)
        self.db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password')
        self.site = 0
        self.maxsite = 6

    def parse(self, response):
        # Extract links to individual beer pages
        beer_links = response.xpath("//div[contains(@class,'article')]/a/@href").getall()

        next_page = ''
        for link in beer_links:
            yield scrapy.Request(url=response.urljoin(link), callback=self.parse_beer)

        # Follow pagination if available by checking for error message
        if not beer_links:
            self.site += 1
            yield scrapy.Request(url=f"https://www.biertaxi-duesseldorf.de/shop/:group_biere-flasche.2036:page_{self.site}", callback=self.parse)

    def parse_beer(self, response):
        beer_data = {}
        beer_data['date'] = datetime.now()
        beer_data['reseller'] = 'Biertaxi'
        # Extract price
        price = response.xpath("//span[contains(@class,'price')]/text()").get()
        if price:
            parts = price.split(' ')
            beer_data['currency'] = parts[0][-1]
            beer_data['price'] = float(parts[0][0:-1].replace(',', '.'))
        beer_data['zipcode'] = response.css("table.table.table-striped").re_first('40549')

        beer_data['quantity'] = round(float(response.xpath("//span[contains(@class,'info package')]/text()").get().split('x')[0]
        ) * float(response.xpath("//span[contains(@class,'info package')]/text()").get().split('x')[-1].split('l')[0]),2)
        beer_data['unit'] = response.xpath("//span[contains(@class,'info package')]/text()").get().split('x')[-1].split(' ')[0][-1]


        # Extract name and other relevant information
        beer_data['name'] = response.xpath("//div[contains(@class,'article-wrapper')]/h1/text()").get()
        beer_data['name'] = re.search(r"^[^\d\s]+(?:\s[^\d\s]+)*",beer_data['name'])[0]
        # Extract alcohol content
        beer_data['alcohol_content'] = round(float(response.css("table.table.table-striped").re_first('(\d*\.\d*)%')),2)

        try:
            result = self.db.process_entries(beer_data)
            self.logger.info(f"Inserted data: {result}")
        except Exception as e:
            self.logger.error(f"Error inserting data: {e}")

        yield beer_data

    def errback_httpbin(self, failure):
        # Log any errors
        self.logger.error(repr(failure))