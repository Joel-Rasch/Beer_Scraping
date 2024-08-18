import scrapy
from datetime import datetime

class BeerPrice(scrapy.Spider):
    name = 'beer_price'
    allowed_domains = 'edeka24.de'
    start_urls = ['https://www.edeka24.de/Wein-Spirituosen/Bier']

    def parse(self, response):
        products = response.css('div.product-item')

        for product in products:

            yield {
                #'Name': product.css('div.product-details').get(),
                'Name': product.css('a.title::attr(title)').get().strip(),
                #'Preis': product.css('div.price').get().replace('<div class="price">\n                                        ','').replace(' €\n                                                                            </div>',''),
                'Preis': product.css('p.price-note').get().replace('<p class="price-note">','').replace('zzgl. 0,25 € Pfand','').replace('</p>','').replace('zzgl. 1,00 € Pfand','').replace('€/l','').strip(),
                'Waehrung': 'Euro',
                #'Menge': product.css('a.title::attr(title)').get()[-6:].replace('L','').replace('l',''),
                'Menge': '1',
                'Mengeneinheit': 'L',
                'Anbieter': 'Edeka24.de',
                'PLZ': '0000',
                'Scrape_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
