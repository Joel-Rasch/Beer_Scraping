import scrapy
import re
from datetime import date
import pandas

class ProductLinksSpider(scrapy.Spider):
    name = "product_links"
    start_urls = ['https://durstquelle.de/biere.html?product_list_limit=36']  # Replace with the path to your HTML file

    def parse(self, response):
        # dataframe = pandas. DataFrame(columns = ['name', 'quantity', 'unit', 
        #                                          'price', 'currency', 'date', 
        #                                          'reseller', 'zipcode'])
        # Extract all product links
        links = response.css('a.product-item-link::attr(href)').extract()
        for link in links:
            # Follow each link to scrape the product details
            yield response.follow(link, self.parse_product)
        # dataframe.to_csv(f"./durtquelle_{date.today().strftime('%Y%m%d')}.csv", index=False)

    def parse_product(self, response):
        # Extract the product title
        title = response.css('h1.page-title span.base::text').get()
        title = re.sub(r"(\d+(?:,\d+)?)(\s*MW|\s*$)", r"\1l\2", title)
        pattern = r"^(.*?)\s((?:\d+x)?\d+(?:,\d+)?)([a-zA-Z]+)"
        match = re.search(pattern, title)
        if match:
            name = match.group(1).strip()
            quantity = match.group(2)
            unit = match.group(3)

        # Extract the product price
        price_curr = response.css('.price::text').get()
        # Split the price into currency and amount
        price = price_curr.split()[0]
        currency = price_curr.split()[1]
        
        # Reseller & Crawling Details
        current_date = date.today().strftime("%d/%m/%Y")
        reseller = "Durstquelle"
        zipcode = "hamburg"
        yield {'name': name,
               'quantity': quantity,
               'unit': unit,
               'price': price,
               'currency': currency,
               'date': current_date,
               'reseller': reseller,
               'zipcode': zipcode}
        # dataframe = dataframe._append({'name': name,
        #                                 'quantity': quantity, 
        #                                 'unit': unit, 
        #                                 'price': price, 
        #                                 'currency': currency, 
        #                                 'date': current_date, 
        #                                 'reseller': reseller, 
        #                                 'zipcode': zipcode},
        #                                 ignore_index=True)