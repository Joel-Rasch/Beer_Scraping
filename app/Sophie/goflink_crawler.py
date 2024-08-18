import asyncio
from datetime import date
import pandas
from playwright.async_api import async_playwright
#from playwright_stealth import stealth_async

import re

# def parse_args(args, **kwargs):
#     shortopt = kwargs.get("short")
#     longopt = kwargs.get("long")
#     requiredopt = kwargs.get("required", False)

#     for i, arg in enumerate(args):
#         if arg == shortopt or arg == longopt:
#             if i + 1 < len(args):
#                 value = args[i + 1]
#                 args[:] = [item for idx, item in enumerate(args) if idx not in (i, i+2)]
#                 return value

#     if requiredopt:
#         print(f"Error: {longopt} or {shortopt} is a required argument")
#         exit(1)

#     return None

async def browse_page(link, logic_fn):
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
            #print(swimlane_name)
            if "Kategorien" in swimlane_name:
                #print("Kategorien gefunden")
                categories = await swimlane.locator('.items-wrapper').get_by_role('listitem').all()
                for category in categories:
                    category_name = await category.locator(".title").inner_text()
                    # print(category_name)
                    if "Bier" in category_name:
                        # print("Bier gefunden")
                        await category.click()
                        break
                break
        
        await logic_fn(page)
        await browser.close()    
        

def split_price(price):
    price = price.split()
    currency = price[1]
    price = price[0]
    return currency, price

def correct_name(name):
    name = name.replace("ˆ", "ö")
    name = name.replace("ﬂ", "ß")
    name = name.replace("‰", "ä")
    name = name.replace("¸", "ü")
    return name

# def get_screenshot_path(link):
#     # Extract domain name to use as screenshot path
#     match = re.search(r"https?://(?:www\.)?([^/]+)", link)
#     if match:
#         domain = match.group(1).split('.')[0]
#         screenshot_path = f"{domain}.png"
#     else:
#         print(f"The given URL {link} is invalid for the screenshot path")
#         exit(1)
#     return screenshot_path

def parse_product_string(product_string):
    # Preperatiom to replace missing l if needed
    product_string = re.sub(r"(\d+(?:,\d+)?)(\s*MW|\s*$)", r"\1l\2", product_string)
    
    # Regular expression to parse product string
    pattern = r"^(.*?)\s((?:\d+x)?\d+(?:,\d+)?)([a-zA-Z]+)"

    match = re.search(pattern, product_string)

    if match:
        name = match.group(1).strip()
        quantity = match.group(2)
        unit = match.group(3)
        return name, quantity, unit
    else:
        return product_string, None, None

async def get_content(page):
    dataframe = pandas. DataFrame(columns = ['name', 'quantity', 'unit', 'price', 'currency', 'date', 'reseller', 'zipcode'])
    products =  await page.locator('.product-card-grid-item').all()
    for product in products:
        title = await product.get_by_test_id("product-title").inner_text()
        #title_utf8 = title.encode('utf-8')
        name = correct_name(title)
        beer, quantity, unit = parse_product_string(name)
        price = await product.locator('.price-tag').inner_text()
        currency, price = split_price(price)
        current_date = date.today().strftime("%d/%m/%Y")
        reseller = "Flink"
        zipcode = ""
        # print(name)
        # print(quantity)
        # print(unit)
        # print(price)
        # print(currency)
        dataframe = dataframe._append({'name': beer, 'quantity': quantity, 'unit': unit, 'price': price, 'currency': currency, 'date': current_date, 'reseller': reseller, 'zipcode': zipcode}, ignore_index=True)
    return dataframe

def create_csv(dataframe):
    dataframe.to_csv(f"./flink_exports/flink_{date.today().strftime('%Y%m%d')}.csv", index=False)
    print("CSV created")	

async def main(args):
    # link = parse_args(args, short="-l", long="--link", required=True)
    link = "https://www.goflink.com/de-DE/shop"
    # screenshot_path = get_screenshot_path(link)
    async def page_logic(page):
        # await page.screenshot(path=screenshot_path)
        # print(await page.title())
        products = await get_content(page)          
        create_csv(products)
    await browse_page(link, page_logic)


if __name__ == "__main__":
    import sys
    asyncio.run(main(sys.argv[1:]))
    # asyncio.run(second_main(sys.argv[1:]))
