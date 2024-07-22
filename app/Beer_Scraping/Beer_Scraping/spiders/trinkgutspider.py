import scrapy


class TrinkgutspiderSpider(scrapy.Spider):
    name = "trinkgutspider"
    allowed_domains = ["www.trinkgut.de"]
    start_urls = ["https://www.trinkgut.de/search?search=bier"]

    def parse(self, response):
        pass
