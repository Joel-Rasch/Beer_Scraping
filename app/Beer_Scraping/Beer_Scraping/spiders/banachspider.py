import scrapy
from datetime import datetime

class BanachspiderSpider(scrapy.Spider):
    name = "banachspider"
    allowed_domains = ["www.shop.banach-getraenke.de"]
    start_urls = ["https://www.shop.banach-getraenke.de/bier/"]

    def parse(self, response):
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
        beer_data['scrape_date'] = datetime.now()
        beer_data['anbieter'] = 'Banach'
        # Extract price
        price_value = response.xpath('//meta[@itemprop="price"]/@content').get()

        price = response.xpath(
            '//span[contains(@class,"price--content") and contains(@class,"content--default")]/text()').getall()[1]

        if price:
            parts = price.split('\xa0') if '\xa0' in price else price.split()
            beer_data['currency'] = parts[1]
            beer_data['price'] = price_value

        # Extract data from product attributes
        detail_list = response.css('div.product-info-attribute-container')
        labels = detail_list.css('div.type::text').getall()
        values = detail_list.css('div.product-attribute-value span::text').getall()
        for label, value in zip(labels, values):
            if label and value:
                beer_data[label.strip()] = value.strip()

        # Extract name and other relevant information
        beer_data['name'] = response.css('h1.product--title::text').get().split('\n')[1]
        description = response.xpath('//div[@class="product--description"]/p/text()').get()
        if description:
            beer_data['description'] = description.strip()

        # Extract alcohol content
        alcohol_content = response.xpath('//div[@class="product--description"]/p/strong/text()').re_first(
            r'\d.*\%')
        if alcohol_content:
            beer_data['alcohol_content'] = alcohol_content

        yield beer_data

    def errback_httpbin(self, failure):
        # Log any errors
        self.logger.error(repr(failure))