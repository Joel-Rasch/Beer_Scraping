import asyncio
from datetime import datetime
import pandas
from playwright.async_api import async_playwright
import os
import sys
import re

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
        browser = await p.chromium.launch_persistent_context(user_data_dir='./userdata/', headless=False, slow_mo=5000, args=CHROMIUM_ARGS)
        page = await browser.new_page()
        await page.goto(link)
        await fill_zipcode(page, "22159") #inital zipcode to load 
        subcategory_links = await get_subcategory_links(page)
        zipcodes = get_zipcodes()
        for zipcode in zipcodes:
            valid_zip = await fill_zipcode(page, str(zipcode))
            if valid_zip:
                print(f"Zipcode {zipcode} is valid")
                await goto_subcategory(page, subcategory_links, zipcode)
            else:    
                print(f"Zipcode {zipcode} is invalid")
        await browser.close()

def get_zipcodes():
    zipcodes = pandas.read_csv(f"{current_directory}/zipcodes_fp.csv", sep=";")   
    zipcodes = zipcodes['zipcode'].tolist()
    zipcodes = list(set(zipcodes))
    return zipcodes

async def fill_zipcode(page, zipcode):
    element = None
    if (await page.locator('.zipcode').is_visible()):
        element = page.locator('.zipcode')
    elif (await page.locator('.fp_modal_container').is_visible()):
        element = page.locator('.fp_modal_container')

    valid_zip = False
    if element:
        await element.get_by_test_id("q3FmlhEfSKrk3eUtgXANe").fill(zipcode)
        if (await element.locator('.infotext.red').is_visible()):
            # if info text is visible, zip is invalid
            await element.get_by_test_id("q3FmlhEfSKrk3eUtgXANe").fill("")
        else:
            # click to check if zip is valid
            await element.locator('.fp_button_primary').click()
            if (await element.get_by_test_id("0pdGMRcP4XELJEwyP7aPr").is_visible() == False):
                # Zip is valid
                valid_zip = True 
            else:
                # Zip is invalid
                await page.locator('.closeButton').click()
                valid_zip = False
                # PLZ is invalid, valid_zip still false
                
    else:
        await page.locator('.change_zip_code').first.click()
        valid_zip = await fill_zipcode(page, zipcode)  # rekursive call with return value

    return valid_zip

async def get_subcategory_links(page):
    subcategories = await page.locator('.subCategory').all()
    subcategory_links = []
    for subcategory in subcategories:
            domain = "https://www.flaschenpost.de"
            link = await subcategory.locator('a').get_attribute('href')
            full_link = f"{domain}{link}"
            subcategory_links.append(full_link)
    return subcategory_links

async def goto_subcategory(page, links, zipcode):
    for link in links:
        await page.goto(link) 
        await get_content(page, zipcode, link)                  

def split_price(price):
    price = price.split()
    currency = price[1]
    price = price[0].replace(",", ".")
    return currency, price

def parse_product_string(amount_des):
    # Regular expression to extract only quantity and unit
    pattern = r"(\d+\s*x\s*)?(\d+(?:,\d+)?)(\s*[a-zA-Z]+)"
    match = re.search(pattern, amount_des)

    if match:
        multiplier = match.group(1).replace("x", "")  # Optionaler Multiplikator wie '6 x'
        print(multiplier) 
        quantity = match.group(2).replace(",", ".")  # Die Menge, z.B. '0,5'
        unit = match.group(3)  # Die Einheit, z.B. 'l'

        if multiplier:  # Wenn ein Multiplikator wie '6x' vorhanden ist
            multiplier = int(multiplier)  # Entferne das 'x' und konvertiere zu int
            quantity = float(quantity) * multiplier  # Berechne die Gesamtmenge

        return float(quantity), unit
    else:
        return float(0.0), ""
    

def create_csv(dataframe, postfix, zipcode):
    dataframe.to_csv(f"./Export/flaschenpost_exports/flaschenpost_{zipcode}_{postfix}_{datetime.now().strftime('%Y-%m-%d')}.csv", index=False)
    print("CSV created")

def write_to_db(entry):
    db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password', host='postgres',
                      port='5432')
    try:
        result = db.process_entries(entry)
        print(f"Inserted data: {result}")
    except Exception as e:
        print(f"Error inserting data: {e}")

async def get_content(page, zipcode, link):
    
    # Dictionary for current product data
    beer_data = {}

    products =  await page.locator('.product').all()
    
    # Iterate over all products
    for product in products:
        name = await product.get_by_role('heading').inner_text()
        
        #Get all variants of a product
        variants = await product.get_by_test_id("KkvSok_oKKBlcW0k_i_c3").all()
        
        # Iterate over all variants of a product
        for variant in variants:
            amount = await variant.locator('.amount_description').inner_text()
            quantity, unit = parse_product_string(amount)
            if (await variant.get_by_test_id("1720R6AKvkZb8WVvy4iDi").is_visible()):
                price = await variant.get_by_test_id("1720R6AKvkZb8WVvy4iDi").inner_text()
                currency, price = split_price(price)
            else:
                price = "Out of stock"
                currency = ""
            current_date = datetime.now().strftime('%Y-%m-%d')
            reseller = "Flaschenpost"
            zipcode = str(zipcode)
            
            # Current product data
            beer_data =  {'name': name,
               'quantity': quantity,
               'unit': unit,
               'price': price,
               'currency': currency,
               'alcohol_content': None,
               'date': current_date,
               'reseller': reseller,
               'zipcode': zipcode,
               'url': link}
            
            # Create entry with current product data
            write_to_db(beer_data)
            # print(beer_data)


    


async def main():
    startlink = "https://www.flaschenpost.de/bier/pils"    
    await browse_page(startlink)

if __name__ == "__main__":
    asyncio.run(main())
