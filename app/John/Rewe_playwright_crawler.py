import time
from datetime import datetime
import random
import re
import csv
import sys
import os
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)
from Dbuploader import BeerDatabase

def extract_links(page):
    return page.evaluate('''
        () => {
            const links = Array.from(document.querySelectorAll('a'));
            return links.map(link => link.href).filter(href => href.includes('/p/'));
        }
    ''')

def simulate_human_behavior(page):
    time.sleep(random.uniform(0.1, 0.4))
    scroll_amount = random.randint(100, 500)
    page.evaluate(f'window.scrollBy(0, {scroll_amount})')
    for _ in range(random.randint(3, 5)):
        x = random.randint(0, page.viewport_size['width'])
        y = random.randint(0, page.viewport_size['height'])
        page.mouse.move(x, y)
        time.sleep(random.uniform(0.1, 0.4))
    if random.random() < 0.3:
        elements = page.query_selector_all('p, h1, h2, h3, span')
        if elements:
            element = random.choice(elements)
            box = element.bounding_box()
            if box:
                page.mouse.move(box['x'], box['y'])
                page.mouse.down()
                page.mouse.move(box['x'] + box['width'], box['y'] + box['height'])
                page.mouse.up()
    time.sleep(random.uniform(0.1, 0.5))

def scroll_and_wait(page, scroll_count=10, delay=1):
    last_height = page.evaluate('document.body.scrollHeight')
    scroll_distance = last_height // (scroll_count-1)
    links = []
    while True:
        for i in range(scroll_count):
            page.evaluate(f'window.scrollBy(0, {scroll_distance})')
            links.extend(extract_links(page))
        button = page.query_selector('Button.PostRequestGetForm_PostRequestGetFormButton__9Sp2R.PaginationArrow_paginationArrow__DXWng.PaginationArrow_paginationArrowEnabled___He_R.PaginationArrow_paginationArrowBack__3_LbC')
        if button is not None:
            button.click()
        else:
            break
    return links

def parse_beer_info(page):
    beer_info = {
        'name': None,
        'quantity': None,
        'unit': None,
        'price': None,
        'currency': None,
        'alcohol_content': None
    }

    try:
        beer_info['name'] = page.locator('h1.pdpr-Title').inner_text()
    except:
        print(f'Could not find name for {page.url}')

    try:
        price_str = page.locator('.pdpr-Price__Price.rs-qa-price').inner_text()
        price_match = re.match(r'(\d+(?:,\d+)?)\s*([€$£])', price_str)
        beer_info['price'] = float(price_match.group(1).replace(',', '.'))
        beer_info['currency'] = price_match.group(2)
    except:
        print(f'Could not find price for {page.url}')

    try:
        quantity_info = page.locator('.rs-qa-price-base.pdsr-Grammage').inner_text()
        quantity_match = re.search(r'(\d+)\s*x\s*', quantity_info)
        unit_match = re.search(r'(\d+(?:,\d+)?)\s*(ml|l)\b', quantity_info) 

        if quantity_match is not None and unit_match is not None:
            beer_info['quantity'] = float(unit_match.group(1).replace(',','.')) * float(quantity_match.group(1))
        elif unit_match is not None:
            beer_info['quantity'] = float(unit_match.group(1).replace(',','.'))

        beer_info['unit'] = unit_match.group(2) if unit_match else None
    except:
        print(f'Could not find quantity info for {page.url}')

    try:
        #page.locator('.pdpr-TabCordionItem__Label:has-text("Artikeldetails")').click()
        alcohol_content = page.locator('.pdpr-Attribute:has-text("Alkoholgehalt")')
        properties = page.locator('.pdpr-Attribute:has-text("Eigenschaften")')

        if alcohol_content.count() > 0:
            alcohol_content = alcohol_content.inner_text()
        elif properties.count() > 0:
            alcohol_content = properties.inner_text()
        
        if alcohol_content is not None and re.search(r'alkohol\s*frei', alcohol_content, re.IGNORECASE) is not None:
            beer_info['alcohol_content'] = 0.0
        elif alcohol_content is not None:
            alcohol_match = re.search(r'(\d+(?:,\d+)?)', alcohol_content)
            if alcohol_match:
                beer_info['alcohol_content'] = float(alcohol_match.group(1).replace(',', '.'))
    except:
        print(f'Could not find alcohol content for {page.url}')

    return beer_info

def run(output='database', db=None, csv_filename='beer_data.csv'):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, 
            args=[
            '--window-size=1920,1080',
            '--start-maximized',
            '--window-position=0,0',
            '--ignore-certifcate-errors',
            '--ignore-certifcate-errors-spki-list',
            '--disable-setuid-sandbox',
            '--disable-extensions',
            '--disable-plugins-discovery',
            '--disable-blink-features=AutomationControlled',
            '--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"',
            '--disable-infobars',
            '--disable-features=WebGL',
            '--lang=de-DE,de',
            '--start-maximized',
            ],
            slow_mo=100
        )

        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
        )
        
        page = context.new_page()

        first = True
        reseller = 'Rewe'
        zip_codes = ['25436', '22089']
        
        if output == 'csv':
            save_to_csv({}, csv_filename, write_header=True) 

        for zip_code in zip_codes:
            links = []
            page.goto('https://shop.rewe.de/c/bier-biermischgetraenke/', wait_until='load')
            page.wait_for_load_state('load')
            time.sleep(random.uniform(3, 4))
            simulate_human_behavior(page)
            if page.get_by_test_id('uc-accept-all-button').is_visible():
                page.get_by_test_id('uc-accept-all-button').click()
            if first:
                delivery_type = page.get_by_test_id('gbmc-highlightable-button').nth(1)
                delivery_type.click(force=True)
                page.fill('input.gbmc-zipcode-input.gbmc-undecided.svelte-1wkkum2', zip_code, force=True)
                first = False
            else:
                change_button = page.locator('button.gbmc-trigger.gbmc-qa-trigger:has-text("ändern")')
                change_button.click()
                change_zip_code = page.locator('a.gbmc-change-zipcode-link.svelte-yhv3au')
                change_zip_code.click()
                page.fill('input.gbmc-zipcode-input.gbmc-undecided.svelte-1wkkum2', zip_code)
                delivery_type = page.locator('button.gbmc-qa-delivery-trigger.svelte-1uef6g3.gbmc-wide')
                delivery_type.click()
            time.sleep(random.uniform(2, 4))
            links = scroll_and_wait(page, scroll_count=10, delay=0.001)
            unique_links = list(set(links))
            
            for link in unique_links:
                try:
                    page.goto(link, wait_until='load')
                    category = page.locator('.lr-breadcrumbs')
                    if 'Bier' in category.inner_text():
                        simulate_human_behavior(page)

                        beer_info = parse_beer_info(page)
                        
                        entry = {
                            **beer_info,
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'reseller': reseller,
                            'zipcode': zip_code,
                        }

                        if output == 'database' and db is not None:
                            try:
                                db.process_entry(entry)
                                print(f'Rewe Crawler - Entry inserted into database: {entry}')
                            except Exception as e:
                                print(f'Error inserting entry into database: {str(e)}')
                        elif output == 'csv':
                            save_to_csv(entry, csv_filename)

                except Exception as e:
                    print(f'Error processing {link}: {str(e)}')

        browser.close()

def save_to_csv(entry, filename, write_header=False):
    fieldnames = ['name', 'quantity', 'unit', 'price', 'currency', 'date', 'reseller', 'zipcode', 'alcohol_content']
    mode = 'w' if write_header else 'a'
    with open(filename, mode, newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(entry)
        
if __name__ == '__main__':
    db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password', host='postgres', port='5432')
    
    run(output='database', db=db)
    date = datetime.now().strftime('%Y-%m-%d')
    #run(output='csv', csv_filename=f'rewe_beer_data_{date}.csv')
