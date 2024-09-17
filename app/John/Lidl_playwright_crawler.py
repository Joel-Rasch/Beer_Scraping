import time
from datetime import datetime
import random
import os
import re
import csv
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


def scroll_and_wait(page, scroll_count=10, delay=1):
    last_height = page.evaluate('document.body.scrollHeight')
    scroll_distance = last_height // (scroll_count - 1)
    links = []
    while True:
        for i in range(scroll_count):
            page.evaluate(f'window.scrollBy(0, {scroll_distance})')
            links.extend(extract_links(page))
        button = page.query_selector('button.s-load-more__button')
        if button is not None:
            button.click()
            time.sleep(random.uniform(0.5, 1))
        else:
            break
    return links


def extract_links(page):
    return page.evaluate('''
        () => {
            const links = Array.from(document.querySelectorAll('a'));
            return links.map(link => link.href).filter(href => href.includes('/p/'));
        }
    ''')


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
        beer_name = page.query_selector('h1.keyfacts__title').inner_text()
        beer_name = re.sub(r"^\d+.*?(Bierfass|Bierfässer)\s*", "", beer_name, flags=re.IGNORECASE)
        beer_name = re.sub(r"\s+\d+\s*L.*$", "", beer_name, flags=re.IGNORECASE)
        beer_name = re.sub(r", Bierfass.*$", "", beer_name, flags=re.IGNORECASE)
        beer_name = re.sub(r" mit Zapfhahn.*$", "", beer_name, flags=re.IGNORECASE)
        beer_name = beer_name.strip()
        beer_info['name'] = beer_name
    except:
        print(f'Could not find name for {page.url}')

    try:
        price_str = page.query_selector('div.m-price__price').inner_text()
        price_match = re.match(r'(\d+(?:,\d+)?)', price_str)
        if price_match:
            beer_info['price'] = float(price_match.group(1).replace(',', '.'))
            beer_info['currency'] = '€'
    except:
        print(f'Could not find price for {page.url}')

    try:
        anzahl = re.search(r'(\d+)\s*(?:x|×)\s*', page.query_selector('h1.keyfacts__title').inner_text())
        quantity_info = page.query_selector('li.wine.bottlesize span').inner_text()
        quantity_match = re.search(r'(\d+)\-([a-zA-Z]+)', quantity_info)
        if quantity_match and anzahl:
            beer_info['quantity'] = round(float(quantity_match.group(1)) * float(anzahl.group(1)),2)
            beer_info['unit'] = quantity_match.group(2)
        elif quantity_match:
            beer_info['quantity'] = round(float(quantity_match.group(1)),2)
            beer_info['unit'] = quantity_match.group(2)
    except:
        print(f'Could not find quantity info for {page.url}')

    try:
        alcohol_content = page.query_selector('li.wine.alcoholiccontent span').inner_text()
        alcohol_match = re.search(r'(\d+(?:,\d+)?)', alcohol_content)
        if alcohol_match:
            beer_info['alcohol_content'] = float(alcohol_match.group(1).replace(',', '.'))
    except:
        print(f'Could not find alcohol content for {page.url}')

    return beer_info


def run(output='database', db=None, csv_filename='lidl_beer_data.csv'):
    if output == 'csv':
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_filename = os.path.join(script_dir, csv_filename)
        save_to_csv({}, csv_filename, write_header=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(user_data_dir='./userdata/',
                                                       headless=True, slow_mo=100,
                                                       args=['--disable-blink-features=AutomationControlled'])
        page = browser.new_page()

        reseller = 'Lidl'
        zip_code = 'online'

        try:
            page.goto('https://www.lidl.de/h/bier/h10023946?pageId=10005566%2F10023946')
            time.sleep(random.uniform(2, 3))
            links = scroll_and_wait(page, scroll_count=10, delay=0.001)
            unique_links = list(set(links))

            for link in unique_links:
                try:
                    page.goto(link, wait_until='domcontentloaded')
                    simulate_human_behavior(page)
                    beer_info = parse_beer_info(page)

                    entry = {
                        **beer_info,
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'reseller': reseller,
                        'zipcode': zip_code,
                        'url': link
                    }

                    if output == 'database' and db is not None:
                        try:
                            db.process_entry(entry)
                            print(f'Lidl Crawler - Entry inserted into database: {entry}')
                        except Exception as e:
                            print(f'Error inserting entry into database: {str(e)}')
                    elif output == 'csv':
                        save_to_csv(entry, csv_filename)

                except Exception as e:
                    print(f'Error processing {link}: {str(e)}')

        except Exception as e:
            print(f'An error occurred: {str(e)}')
        finally:
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
    db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password', host='postgres',
                      port='5432')

    run(output='database', db=db)

    date = datetime.now().strftime('%Y-%m-%d')
