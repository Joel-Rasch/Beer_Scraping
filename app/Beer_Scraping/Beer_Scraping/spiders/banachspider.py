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


class BanachspiderSpider(scrapy.Spider):
    name = "banachspider"
    allowed_domains = ["www.shop.banach-getraenke.de"]
    start_urls = ["https://www.shop.banach-getraenke.de/bier/"]

    def __init__(self, *args, **kwargs):
        super(BanachspiderSpider, self).__init__(*args, **kwargs)
        self.db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password')

    def parse(self, response,**kwargs):
        # Extract links to individual beer pages
        beer_links = response.css('a.product--title::attr(href)').getall()

        for link in beer_links:
            yield scrapy.Request(url=response.urljoin(link), callback=self.parse_beer)

        # Follow pagination if available by checking for error message

        next_page = response.xpath('//a[@title="Nächste Seite"]/@href').get()

        if not response.css('div.message.info.empty').get():
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse)

    def parse_beer(self, response):
        beer_data = {}
        beer_data['date'] = datetime.now()
        beer_data['reseller'] = 'Banach'
        # Extract price
        price_value = response.xpath('//meta[@itemprop="price"]/@content').get()

        price = response.xpath(
            '//span[contains(@class,"price--content") and contains(@class,"content--default")]/text()').getall()[1]

        if price:
            parts = price.split('\xa0') if '\xa0' in price else price.split()
            beer_data['currency'] = parts[1][0]
            beer_data['price'] = price_value

        # Extract data from product attributes
        detail_list = response.css('div.product-info-attribute-container')

        beer_data['quantity'] = response.css('div.product--price.price--unit').re_first('\d+')
        beer_data['unit'] = response.xpath('//div[contains(@class,"product--price") and contains(@class,"price--unit")]/text()').re_first('\d+ (\w+)')


        labels = detail_list.css('div.type::text').getall()
        values = detail_list.css('div.product-attribute-value span::text').getall()
        for label, value in zip(labels, values):
            if label and value:
                beer_data[label.strip()] = value.strip()

        # Extract name and other relevant information
        beer_data['name'] = response.css('h1.product--title::text').get().split('\n')[1]
        beer_data['zipcode'] = 'online'

        # Extract alcohol content
        alcohol_content = response.xpath('//div[@class="product--description"]/p/strong/text()').re_first(r'(\d.*)\%')
        alcohol_content = alcohol_content.replace(',', '.')
        alcohol_content = float(alcohol_content)
        if alcohol_content:
            beer_data['alcohol_content'] = alcohol_content

        try:
            result = self.db.process_entries(beer_data)
            self.logger.info(f"Inserted data: {result}")
        except Exception as e:
            self.logger.error(f"Error inserting data: {e}")

        yield beer_data

    def errback_httpbin(self, failure):
        # Log any errors
        self.logger.error(repr(failure))