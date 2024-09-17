import asyncio
from datetime import datetime
import pandas
from playwright.async_api import async_playwright
import re
import os
import sys

# Get the current directory of this file
current_directory = os.path.dirname(os.path.realpath(__file__))

# Get the parent directory
parent_directory = os.path.dirname(current_directory)

# Add the parent directory to sys.path
sys.path.append(parent_directory)

from Dbuploader import BeerDatabase

async def browse_page(link):
    CHROMIUM_ARGS= [
		'--disable-blink-features=AutomationControlled',
	]
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(user_data_dir='./userdata/', 
                                                             headless=False, slow_mo=5000, args=CHROMIUM_ARGS)
        page = await browser.new_page()
        await page.goto(link)
        swimlanes = await page.locator('.swimlane').all()
        for swimlane in swimlanes:
            swimlane_name = await swimlane.locator(".heading").inner_text()
            if "Kategorien" in swimlane_name:
                categories = await swimlane.locator('.items-wrapper').get_by_role('listitem').all()
                for category in categories:
                    category_name = await category.locator(".title").inner_text()
                    if "Bier" in category_name:
                        await category.click()
                        break
                break
        
        link = 'https://www.goflink.com/de-DE/shop/category/bier/'
        await get_content(page, link)
        await browser.close()    
        

def split_price(price):
    price = price.split()
    currency = price[1]
    price = price[0].replace(",", ".")
    return currency, price

def correct_name(name):
    name = name.replace("ˆ", "ö")
    name = name.replace("ﬂ", "ß")
    name = name.replace("‰", "ä")
    name = name.replace("¸", "ü")
    return name


def parse_product_string(product_string):
    # Preperation to replace missing 'l' if needed
    product_string = re.sub(r"(\d+(?:,\d+)?)(\s*MW|\s*$)", r"\1l\2", product_string)

    # Regular expression to parse product string
    pattern = r"^(.*?)(\d+x)?(\d+(?:,\d+)?)([a-zA-Z]+)"
    match = re.search(pattern, product_string)

    if match:
        name = match.group(1).strip()  # Produktname
        multiplier = match.group(2)    # Zahl vor 'x', wenn vorhanden
        quantity = match.group(3).replace(",", ".")  # Zahl nach 'x'
        unit = match.group(4)  # Einheit

        if multiplier:  # Wenn ein 'x' und ein Multiplikator vorhanden sind
            multiplier = int(multiplier[:-1])  # Entferne das 'x' und konvertiere zu int
            quantity = float(quantity) * multiplier

        return name, float(quantity), unit
    else:
        return product_string, float(0.0) , "k.A."

def create_csv(dataframe):
    dataframe.to_csv(f"./Export/flink_exports/flink_{datetime.now().strftime('%Y-%m-%d')}.csv", index=False)
    print("CSV created")	

def write_to_db(entry):
    db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password', host='postgres',
                      port='5432')
    try:
        result = db.process_entries(entry)
        print(f"Inserted data: {result}")
    except Exception as e:
        print(f"Error inserting data: {e}")

async def get_content(page, link):
    # Dictionary for current product data
    beer_data = {}

    #Get all products on the page
    products =  await page.locator('.product-card-grid-item').all()
    
    #Iterate over all products
    for product in products:
        title = await product.get_by_test_id("product-title").inner_text()
        name = correct_name(title)
        beer, quantity, unit = parse_product_string(name)
        price = await product.locator('.price-tag').inner_text()
        currency, price = split_price(price)
        current_date = datetime.now().strftime('%Y-%m-%d')
        reseller = "Flink"
        zipcode = "online"

        # Current product data
        beer_data =  {'name': beer,
               'quantity': quantity,
               'unit': unit,
               'price': price,
               'currency': currency,
               'alcohol_content': None,
               'date': current_date,
               'reseller': reseller,
               'zipcode': zipcode,
               'url': link}
        
        # Create DB entry with current product data
        write_to_db(beer_data)
        # print(beer_data)


async def main():
    link = "https://www.goflink.com/de-DE/shop"
    await browse_page(link)


if __name__ == "__main__":
    asyncio.run(main())
