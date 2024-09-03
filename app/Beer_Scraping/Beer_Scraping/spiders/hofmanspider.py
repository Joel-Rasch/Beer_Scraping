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
    name = 'hofmanspider'
    start_urls = ['https://www.hoffmannbringts.de/bier?p=1']

    def __init__(self, *args, **kwargs):
        super(BeerSpider, self).__init__(*args, **kwargs)
        self.db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password')
        self.site = 1

    def parse(self, response):
        # Extract links to individual beer pages
        beer_links = response.css('a.product-item-link::attr(href)').getall()

        for link in beer_links:
            yield scrapy.Request(url=response.urljoin(link), callback=self.parse_beer)

        # Follow pagination if available by checking for error message
        if not response.css('div.message.info.empty').get():
            self.site += 1
            yield scrapy.Request(url=f"https://www.hoffmannbringts.de/bier?p={self.site}", callback=self.parse)

    def parse_beer(self, response):
        beer_data = {}
        beer_data['date'] = datetime.now()
        beer_data['reseller'] = 'Getränke Hoffmann'
        # Extract price
        price = response.css('span.price::text').get()
        if price:
            parts = price.split('\xa0') if '\xa0' in price else price.split()
            beer_data['currency'] = parts[1]
            beer_data['price'] = float(parts[0].replace(',','.'))
        beer_data['zipcode'] = '15831'

        amount_list = response.xpath('//div[@class="product-attribute product-attribute-m29"]/div/span/text()').re_first('\d+\w\d+\.\d+').split('x')
        beer_data['quantity'] = round(float(amount_list[0]) * float(amount_list[1]),2)
        beer_data['unit'] = response.xpath('//div[@class="product-attribute product-attribute-m29"]/div/span/text()').get()[-1]

        # Extract data from product attributes
        detail_list = response.css('div.product-info-attribute-container')
        labels = detail_list.css('div.type::text').getall()
        values = detail_list.css('div.product-attribute-value span::text').getall()
        for label, value in zip(labels, values):
            if label and value:
                beer_data[label.strip()] = value.strip()

        # Extract name and other relevant information
        beer_data['name'] = response.css('span.base::text').get()
        beer_data['name'] = re.search(r"^[^\d\s]+(?:\s[^\d\s]+)*",beer_data['name'])
        # Extract alcohol content
        alcohol_content = response.xpath("//div[contains(@class, 'product-attribute-logistikdetails')]//text()[contains(., 'Alkoholgehalt:')]/following::text()[1]").re_first(r'(\d+\.\d+).*\%')

        if alcohol_content:
            beer_data['alcohol_content'] = float(alcohol_content)

        try:
            result = self.db.process_entries(beer_data)
            self.logger.info(f"Inserted data: {result}")
        except Exception as e:
            self.logger.error(f"Error inserting data: {e}")

        yield beer_data

    def errback_httpbin(self, failure):
        # Log any errors
        self.logger.error(repr(failure))