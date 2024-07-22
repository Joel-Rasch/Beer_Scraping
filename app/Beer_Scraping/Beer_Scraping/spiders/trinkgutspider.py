import scrapy


class TrinkgutspiderSpider(scrapy.Spider):
    name = "trinkgutspider"
    allowed_domains = ["www.trinkgut.de"]
    start_urls = ["https://www.trinkgut.de/search?order=score&p=1&search=bier"]

    def parse(self, response):
        beers = response.xpath('//*[contains(@class,"product-box")]/div/a/@href').extract()
        next_page = response.xpath('//*[contains(@id,"p-next-bottom")]/@value').extract()

        pass
