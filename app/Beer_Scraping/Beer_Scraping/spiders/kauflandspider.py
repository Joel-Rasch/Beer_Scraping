import scrapy
from datetime import datetime

class BeerPriceSpider(scrapy.Spider):
    name = "beer_price"
    allowed_domains = ["kaufland.de"]
    start_urls = ["https://www.kaufland.de/bier"]

    def parse(self, response):
        products = response.css('section.product__data')

        for product in products:

            yield {
                'Name': product.css('div.product__title').get().replace('<div class="product__title">','').replace('</div>','').strip(),
                #'Preis': product.css('div.price').get().replace('<div class="price">','').replace('</div>','').replace(' €',''),
                'Preis': product.css('div.product__base-price').get().replace('<div class="product__base-price">','').replace('<span>','').replace('1l = ','').replace(' €','').replace('</span></div>','').strip(),
                'Waehrung': 'Euro',
                'Menge': '1',
                'Mengeneinheit': 'L',
                'Anbieter': product.css('strong.product__seller-info-name').get().replace('<strong class="product__seller-info-name">','').replace('</strong>','').replace('            ','').replace('/n','').strip(),
                'PLZ': '0000',
                'Scrape_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }