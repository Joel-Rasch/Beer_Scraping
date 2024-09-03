import asyncio
from datetime import date
import pandas
from playwright.async_api import async_playwright
import os
import sys

# Get the current directory of this file
current_directory = os.path.dirname(os.path.realpath(__file__))

# Get the parent directory
parent_directory = os.path.dirname(current_directory)

# Add the parent directory to sys.path
sys.path.append(parent_directory)

from Dbuploader import BeerDatabase

async def browse_page(link, logic_fn):
    CHROMIUM_ARGS= [
		'--disable-blink-features=AutomationControlled',
	]
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(user_data_dir='./userdata/', headless=False, slow_mo=5000, args=CHROMIUM_ARGS)
        page = await browser.new_page()
        await page.goto(link)
        #await fill_zipcode(page, "22159") #inital zipcode to load 
        subcategory_links = await get_subcategory_links(page)
        zipcodes = get_zipcodes()
        for zipcode in zipcodes:
            valid_zip = await fill_zipcode(page, str(zipcode))
            if valid_zip:
                await goto_subcategory(page, subcategory_links, logic_fn, zipcode)
        await browser.close()

def get_zipcodes():
    zipcodes = pandas.read_csv(f"{current_directory}/zipcodes.csv", sep=";")   
    zipcodes = zipcodes['Name'].tolist()
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
            if (await element.locator('.modal_wrapper_container').is_visible()):
                await page.locator('.closeButton').click()
                # PLZ is invalid, valid_zip still false
            else:
                # Zip is valid
                valid_zip = True
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

async def goto_subcategory(page, links, logic_fn, zipcode):
    for link in links:
        postfix = link.replace("https://www.flaschenpost.de/bier/", "")
        await page.goto(link)
        await logic_fn(page, postfix, zipcode)                   

def split_price(price):
    price = price.split()
    currency = price[1]
    price = price[0]
    return currency, price

def parse_product_string(amount_des):
    amount_infos = amount_des.split('L')
    quantity = amount_infos[0]
    unit = 'L'
    return quantity, unit

async def get_content(page, zipcode):
    
    # Dictionary for current product data
    beer_data = {}

    # DataFrame for CSV export
    dataframe = pandas. DataFrame(columns = ['name', 'quantity', 
                                             'unit', 'price', 'currency', 
                                             'date', 'reseller', 'zipcode'])
    
    # Get all products on the page
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
            current_date = date.today().strftime("%d/%m/%Y")
            reseller = "Flaschenpost"
            zipcode = zipcode
            
            # Current product data
            beer_data =  {'name': name,
               'quantity': quantity,
               'unit': unit,
               'price': price,
               'currency': currency,
               'date': current_date,
               'reseller': reseller,
               'zipcode': zipcode}
            
            # Create entry with current product data
            write_to_db(beer_data)
            
            # Fill DataFrame for CSV export
            dataframe = dataframe._append({'name': name, 
            'quantity': quantity, 
            'unit': unit, 
            'price': price, 
            'currency': currency,
            'date': current_date,
            'reseller': reseller, 
            'zipcode': zipcode
            },  ignore_index=True)
    
    return dataframe

def create_csv(dataframe, postfix, zipcode):
    dataframe.to_csv(f"./Export/flaschenpost_exports/flaschenpost_{zipcode}_{postfix}_{date.today().strftime('%Y%m%d')}.csv", index=False)
    print("CSV created")

def write_to_db(entry):
    try:
        result = BeerDatabase.process_entries(entry)
        print(f"Inserted data: {result}")
    except Exception as e:
        print(f"Error inserting data: {e}")
    


async def main():
    startlink = "https://www.flaschenpost.de/bier/pils"
    first_zipcode = "22159"
    async def page_logic(page, postfix, zipcode):
        products_df = pandas. DataFrame(columns = ['name', 'quantity', 
                                             'unit', 'price', 'currency', 
                                             'date', 'reseller', 'zipcode'])
        products = await get_content(page, first_zipcode)
        products_df = products_df._append(products)
        #create_csv(products_df, postfix, zipcode)
    
    await browse_page(startlink, page_logic)

if __name__ == "__main__":
    asyncio.run(main())
