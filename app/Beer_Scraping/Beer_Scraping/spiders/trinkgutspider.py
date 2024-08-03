import scrapy
import re
from scrapy.exceptions import DropItem
from urllib.parse import urljoin
from datetime import datetime

class BeerSpider(scrapy.Spider):
    name = 'trinkgut_spider'
    start_urls = ['https://www.trinkgut.de/search?order=name-asc&p=1&search=bier']

    def parse(self, response):
        # Extract beer product links
        beer_links = response.css('a.product-image-link::attr(href)').getall()

        for link in beer_links:
            yield scrapy.Request(urljoin(response.url, link), callback=self.parse_beer)

        # Check for next page and follow if it exists
        next_page = response.xpath('//*[@id="p-next-bottom"]/@value').get()
        if next_page:
            yield scrapy.Request(urljoin(response.url, f"https://www.trinkgut.de/search?order=name-asc&p={next_page}&search=bier"), callback=self.parse)

    def parse_beer(self, response):
        beer_data = {}
        beer_data['waehrung'] = 'Eur'
        beer_data['scrape_date'] = datetime.now()
        beer_data['anbieter'] = 'Trinkgut'
        beer_data['plz'] = '00000'
        try:
            beer_data['name'] = response.css('h1.product-detail-name::text').get().strip()
        except AttributeError:
            beer_data['name'] = None
        try:
            beer_data['price'] = response.xpath('//meta[@itemprop="price"]/@content').get()
        except AttributeError:
            beer_data['price'] = None
        try:
             raw_text = response.xpath('//dd[@itemprop="description"]/text()').get()
             pattern = re.search(r"(\d+)\s*x\s*(\d+[.,]\d+)\s*(\w+)", raw_text)
             result = int(pattern.group(1)) * float(pattern.group(2).replace(',', '.'))
             beer_data['amount'] = result
             beer_data['unit'] = pattern.group(3)
        except AttributeError:
            beer_data['amount'] = None
            beer_data['unit'] = None

        # Extract all data from product-detail-definition-list
        definition_list = response.css('dl.product-detail-definition-list')
        for dt, dd in zip(definition_list.css('dt'), definition_list.css('dd')):
            key = dt.css('::text').get().strip().lower().replace(' ', '_')
            value = dd.css('::text').get().strip()
            beer_data[key] = value

        # Only yield the item if we have at least some data
        if beer_data:
            yield beer_data
        else:
            raise DropItem("Empty item found")