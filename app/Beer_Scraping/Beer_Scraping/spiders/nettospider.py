import scrapy
from datetime import datetime

class BeerPrice(scrapy.Spider):
    name = 'beer_price'
    allowed_domains = 'netto-online.de'
    start_urls = ['https://www.netto-online.de/bier']

    def parse(self, response):
        products = response.css('li.product-list__item')

        for product in products:

            yield {
                'Name': product.css('div.product__title').get().replace('<div class="product__title product__title__inner tc-product-name  line-clamp-2">','').replace('</div>','').strip(),
                'Preis': product.css('span.product-property__base-price').get().replace('<span class="product-property product-property__base-price">','').replace('<span class="product__current-price--digits-after-comma">','').replace('</span> / l</span>','').replace('– / l</span>','0').strip(),
                'Waehrung': 'Euro',
                'Menge': '1',
                'Mengeneinheit': 'L',
                'Anbieter': 'netto-online.de',
                'PLZ': '0000',
                'Scrape_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }