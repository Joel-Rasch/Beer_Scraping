import time
from datetime import datetime
import random
import re
from playwright.sync_api import sync_playwright

def extract_links(page):
    return page.evaluate('''
        () => {
            const links = Array.from(document.querySelectorAll('a'));
            return links.map(link => link.href).filter(href => href.includes('/pv/'));
        }
    ''')

def scroll_and_wait(page, scroll_count=10, delay=1):
    last_height = page.evaluate('document.body.scrollHeight')
    scroll_distance = last_height // (scroll_count-1)
    while True:
        for i in range(scroll_count):
            page.evaluate(f'window.scrollBy(0, {scroll_distance})')
            time.sleep(delay)
            print(f"Scroll {i+1}/{scroll_count}")
        button = page.query_selector('.mfcss_load-more-articles')
        if not button is None:
            button.click()
            print(f"'Load more' button found. Clicking...")
            time.sleep(0.2)
        else:
            break


def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://produkte.metro.de/shop/category/food/alkoholische-getr%C3%A4nke/bier", wait_until='networkidle')
    page.click('text="Alle akzeptieren"')
    page.click('text="Ausgewählter Markt"')
    page.locator('div.css-1hwfws3.Select__value-container').click()
    elements = page.locator('.Select__menu .Select__option')
    for element in elements.all()[10:12]:
        element.click()
        page.locator('div.css-1hwfws3.Select__value-container').click()
        #page.locator('.css-19bqh2r').click()
        Anbieter = element.inner_text()
        print (Anbieter)    
        plz = page.locator('div.brandbar-popover-store-address').inner_text()
        plz = re.search(r'\d{5}', plz).group()
        page.click('text="Markt auswählen"')
        scroll_and_wait(page, scroll_count=20, delay=0.001)
        extract_links(page)
        links = extract_links(page)
        unique_links = list(set(links))
        print(len(unique_links))
        for link in unique_links[2:5]:
            page.goto(link, wait_until='domcontentloaded')
            title = page.locator('//h2').inner_text()
            price = page.locator('.mfcss_article-detail--price-breakdown').nth(1).inner_text()
            Anzahl = re.search(r'(\d+)\s*x\s*', title)
            mengeMitEinheit = re.search(r'(\d+(?:,\d+)?)\s*(ml|l)\b', title) 

            if Anzahl is not None:
                Menge = float(mengeMitEinheit.group(1).replace(",",".")) * float(Anzahl.group(1))
            else:
                Menge = mengeMitEinheit.group(1)
            Einheit = mengeMitEinheit.group(2)
            print(Anbieter)
            print(plz)
            print(title)
            print(price)
            print(Menge)
            print(Einheit)
            print("-" * 50) 

        page.goto("https://produkte.metro.de/shop/category/food/alkoholische-getr%C3%A4nke/bier", wait_until='networkidle')
        page.click('text="Ausgewählter Markt"')
        page.locator('div.css-1hwfws3.Select__value-container').click()



    browser.close()
    
with sync_playwright() as playwright:
    run(playwright)

