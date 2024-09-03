import time
from datetime import datetime
import random
import re
import csv
import os
import sys
from playwright.sync_api import sync_playwright

current_directory = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current_directory)
sys.path.append(parent_directory)
from Dbuploader import BeerDatabase


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


def extract_links(page):
    return page.evaluate('''
        () => {
            const links = Array.from(document.querySelectorAll('a'));
            return links.map(link => link.href).filter(href => href.includes('/pv/'));
        }
    ''')


def scroll_and_wait(page, scroll_count=10, delay=1):
    last_height = page.evaluate('document.body.scrollHeight')
    scroll_distance = last_height // (scroll_count - 1)
    links = []
    while True:
        for i in range(scroll_count):
            page.evaluate(f'window.scrollBy(0, {scroll_distance})')
            links.extend(extract_links(page))
        button = page.query_selector('.mfcss_load-more-articles')
        if button is not None:
            button.click()
            time.sleep(random.uniform(0.5, 1))
        else:
            break
    return links


def parse_beer_info(page, reseller, zipcode):
    beer_info = {
        'name': None,
        'quantity': None,
        'unit': None,
        'price': None,
        'currency': None,
        'alcohol_content': None,
        'reseller': reseller,
        'zipcode': zipcode
    }

    try:
        beer_info['name'] = page.locator('//h2').inner_text()
        beer_info['name'] = re.search(r"^[^\d\s]+(?:\s[^\d\s]+)*", beer_info['name'])[0]
    except:
        print(f'Could not find name for {page.url}')

    try:
        price_str = page.locator('.mfcss_article-detail--price-breakdown').nth(1).inner_text()
        price_match = re.search(r'(\d+(?:[.,]\d+)?)\s*([€$£])', price_str)
        if price_match:
            beer_info['price'] = float(price_match.group(1).replace(',', '.'))
            beer_info['currency'] = price_match.group(2)
    except:
        print(f'Could not find price for {page.url}')

    try:
        count = re.search(r'(\d+)\s*(?:x|×)\s*', beer_info['name'])
        amount_with_unit = re.search(r'(\d+(?:[.,]\d+)?)\s*(ml|l)\b', beer_info['name'])
        if count and amount_with_unit:
            beer_info['quantity'] = float(amount_with_unit.group(1).replace(',', '.')) * float(count.group(1))
        elif amount_with_unit:
            beer_info['quantity'] = float(amount_with_unit.group(1).replace(',', '.'))

        beer_info['unit'] = amount_with_unit.group(2) if amount_with_unit else None
    except:
        print(f'Could not find quantity info for {page.url}')

    try:
        table = page.locator('.table.table-responsive.table-striped tr')
        for row in range(1, table.count()):
            if 'Volumenprozente' in table.nth(row).inner_text():
                alcohol_content = table.nth(row).locator('td').inner_text()
                beer_info['alcohol_content'] = float(alcohol_content)
            elif 'Alkoholfrei' in table.nth(row).inner_text():
                beer_info['alcohol_content'] = float(0.0)

    except:
        print(f'Could not find alcohol content for {page.url}')

    return beer_info


def save_to_csv(entry, filename, write_header=False):
    fieldnames = ['name', 'quantity', 'unit', 'price', 'currency', 'date', 'alcohol_content', 'reseller', 'zipcode']
    mode = 'w' if write_header else 'a'
    with open(filename, mode, newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(entry)


def run(output='database', db=None, csv_filename='metro_beer_data.csv'):
    if output == 'csv':
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_filename = os.path.join(script_dir, csv_filename)
        save_to_csv({}, csv_filename, write_header=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(user_data_dir='./userdata/',
                                                       headless=True, slow_mo=100,
                                                       args=['--disable-blink-features=AutomationControlled'])
        page = browser.new_page()

        try:
            page.goto('https://produkte.metro.de/shop/category/food/alkoholische-getr%C3%A4nke/bier',
                      wait_until='networkidle')
            # page.click('text="Alle akzeptieren"')
            page.click('text="Ausgewählter Markt"')
            page.locator('div.css-1hwfws3.Select__value-container').click()
            elements = page.locator('.Select__menu .Select__option')
            for element in elements.all()[3:5]:
                element.click()
                page.locator('div.css-1hwfws3.Select__value-container').click()
                reseller = element.inner_text()
                zipcode_text = page.locator('div.brandbar-popover-store-address').inner_text()
                zipcode = re.search(r'\d{5}', zipcode_text).group()
                page.click('text="Markt auswählen"')
                links = scroll_and_wait(page, scroll_count=10, delay=0.001)
                unique_links = list(set(links))

                for link in unique_links:
                    try:
                        page.goto(link, wait_until='domcontentloaded')
                        simulate_human_behavior(page)
                        beer_info = parse_beer_info(page, reseller, zipcode)

                        entry = {
                            **beer_info,
                            'date': datetime.now().strftime('%Y-%m-%d'),
                        }

                        if output == 'database' and db is not None:
                            try:
                                db.process_entry(entry)
                                print(f'Metro Crawler - Entry inserted into database: {entry}')
                            except Exception as e:
                                print(f'Error inserting entry into database: {str(e)}')
                        elif output == 'csv':
                            save_to_csv(entry, csv_filename)

                    except Exception as e:
                        print(f'Error processing {link}: {str(e)}')

                page.goto('https://produkte.metro.de/shop/category/food/alkoholische-getr%C3%A4nke/bier',
                          wait_until='networkidle')
                page.click('text="Ausgewählter Markt"')
                page.locator('div.css-1hwfws3.Select__value-container').click()

        except Exception as e:
            print(f'An error occurred: {str(e)}')
        finally:
            browser.close()


if __name__ == '__main__':
    db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password', host='postgres',
                      port='5432')

    run(output='database', db=db)

    # Uncomment the following lines if you want to run in CSV mode
    # date = datetime.now().strftime('%Y-%m-%d')
    # run(output='csv', csv_filename=f'metro_beer_data_{date}.csv')