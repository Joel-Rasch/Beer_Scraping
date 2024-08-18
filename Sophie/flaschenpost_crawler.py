import asyncio
from datetime import date
import pandas
from playwright.async_api import async_playwright
#from playwright_stealth import stealth_async

import json
import re

def parse_args(args, **kwargs):
    shortopt = kwargs.get("short")
    longopt = kwargs.get("long")
    requiredopt = kwargs.get("required", False)

    for i, arg in enumerate(args):
        if arg == shortopt or arg == longopt:
            if i + 1 < len(args):
                value = args[i + 1]
                args[:] = [item for idx, item in enumerate(args) if idx not in (i, i+2)]
                return value

    if requiredopt:
        print(f"Error: {longopt} or {shortopt} is a required argument")
        exit(1)

    return None

async def browse_page(link, logic_fn):
    CHROMIUM_ARGS= [
		'--disable-blink-features=AutomationControlled',
	]
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(user_data_dir='./userdata/', headless=False, slow_mo=5000, args=CHROMIUM_ARGS)
        page = await browser.new_page()
        await page.goto(link)
        await fill_zipcode(page, "22159")
        subcategories = await page.locator('.subCategory').all()
        subcategory_links = []
        for subcategory in subcategories:
            domain = "https://www.flaschenpost.de"
            link = await subcategory.locator('a').get_attribute('href')
            full_link = f"{domain}{link}"
            subcategory_links.append(full_link)
        for link in subcategory_links:
            postfix = link.replace("https://www.flaschenpost.de/bier/", "")
            await page.goto(link)
            await logic_fn(page, postfix)
        await browser.close()



def split_price(price):
    price = price.split()
    currency = price[1]
    price = price[0]
    return currency, price

def get_screenshot_path(link):
    # Extract domain name to use as screenshot path
    match = re.search(r"https?://(?:www\.)?([^/]+)", link)
    if match:
        domain = match.group(1).split('.')[0]
        screenshot_path = f"{domain}.png"
    else:
        print(f"The given URL {link} is invalid for the screenshot path")
        exit(1)
    return screenshot_path

def parse_product_string(amount_des):
    amount_infos = amount_des.split('L')
    quantity = amount_infos[0]
    unit = 'L'
    return quantity, unit

async def get_content(page, zipcode):
    dataframe = pandas. DataFrame(columns = ['name', 'quantity', 
                                             'unit', 'price', 'currency', 
                                             'date', 'reseller', 'zipcode'])
    products =  await page.locator('.product').all()
    for product in products:
        title = await product.get_by_role('heading').inner_text()
        variants = await product.get_by_test_id("KkvSok_oKKBlcW0k_i_c3").all()
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
            # print(title)
            # print(name)
            # print(quantity)
            # print(unit)
            # print(price)
            # print(currency)
            dataframe = dataframe._append({'name': title, 
            'quantity': quantity, 
            'unit': unit, 
            'price': price, 
            'currency': currency,
            'date': current_date,
            'reseller': reseller, 
            'zipcode': zipcode
            },  ignore_index=True)
    
    return dataframe

def create_csv(dataframe, postfix):
    dataframe.to_csv(f"./flaschenpost_exports/flaschenpost_{postfix}_{date.today().strftime('%Y%m%d')}.csv", index=False)

async def fill_zipcode(page, zipcode):
    if (await page.locator('.fp_modal_container').is_visible()):
        await page.get_by_test_id("q3FmlhEfSKrk3eUtgXANe").fill(zipcode)
        await page.get_by_test_id("bpytcH0GkAtjmZakRMjs").click()

async def main(args):
    startlink = parse_args(args, short="-l", long="--link", required=True)
    #screenshot_path = get_screenshot_path(link)
    zipcode = "22159"
    async def page_logic(page, postfix):
        products_df = pandas. DataFrame(columns = ['name', 'quantity', 
                                             'unit', 'price', 'currency', 
                                             'date', 'reseller', 'zipcode'])
        #await fill_zipcode(page, zipcode)
        #await page.screenshot(path=screenshot_path)
        #print(await page.title())
        #await get_content(page, zipcode)
        products = await get_content(page, zipcode)
        #products_df = products_df.append(products)
        #create_csv(products)
        products_df = products_df._append(products)
        create_csv(products_df, postfix)
    
    await browse_page(startlink, page_logic)
    

    #create_csv(products_df)


if __name__ == "__main__":
    import sys
    asyncio.run(main(sys.argv[1:]))
    # asyncio.run(second_main(sys.argv[1:]))
