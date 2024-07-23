import scrapy
import re


class BeerSpider(scrapy.Spider):
    name = 'hofman_spider'
    start_urls = ['https://www.hoffmannbringts.de/bier?p=1']

    def __init__(self, *args, **kwargs):
        super(BeerSpider, self).__init__(*args, **kwargs)
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

        # Extract price
        price = response.css('span.price::text').get()
        if price:
            beer_data['price'] = price.strip().replace('\xa0', '')

        # Extract data from product attributes
        detail_list = response.css('div.product-info-attribute-container')
        labels = detail_list.css('div.type::text').getall()
        values = detail_list.css('div.product-attribute-value span::text').getall()
        for label, value in zip(labels, values):
            if label and value:
                beer_data[label.strip()] = value.strip()

        # Extract name and other relevant information
        beer_data['name'] = response.css('span.base::text').get()
        description = response.css('div.product-view-shortdescription span::text').get()
        if description:
            beer_data['description'] = description.strip()

        # Extract alcohol content
        alcohol_content = response.css('div.product-attribute-logistikdetails ::text').re_first(
            r'\d.*\%')
        if alcohol_content:
            beer_data['alcohol_content'] = alcohol_content

        yield beer_data

    def errback_httpbin(self, failure):
        # Log any errors
        self.logger.error(repr(failure))