import time
from datetime import datetime
import random
import re
from playwright.sync_api import sync_playwright

def extract_links(page):
    return page.evaluate('''
        () => {
            const links = Array.from(document.querySelectorAll('a'));
            return links.map(link => link.href).filter(href => href.includes('/p/'));
        }
    ''')

def scroll_and_wait(page, scroll_count=10, delay=1):
    last_height = page.evaluate('document.body.scrollHeight')
    scroll_distance = last_height // (scroll_count-1)
    links = []
    while True:
        for i in range(scroll_count):
            page.evaluate(f'window.scrollBy(0, {scroll_distance})')
            time.sleep(delay)
            print(f"Scroll {i+1}/{scroll_count}")
            links.extend(extract_links(page))
        button = page.query_selector('PostRequestGetForm_PostRequestGetFormButton__9Sp2R.PaginationArrow_paginationArrow__DXWng.PaginationArrow_paginationArrowEnabled___He_R.PaginationArrow_paginationArrowBack__3_LbC')
        if not button is None:
            button.click()
            print(f"'Load more' button found. Clicking...")
            time.sleep(0.2)
        else:
            break
    return links


def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://shop.rewe.de/c/bier-biermischgetraenke/", wait_until='networkidle')
    page.click('text="Alle erlauben"')
    page.click('text="Abholservice"', force=True)
    page.fill('.gbmc-zipcode-input.gbmc-undecided.svelte-1wkkum2', "25436", force = True)
    page.click('text="Abholmarkt wählen"', force=True)
    Anbieter = "Rewe"
    plz = "23456"
    links = scroll_and_wait(page, scroll_count=20, delay=0.001)
    unique_links = list(set(links))
    print(len(unique_links))
    
    for link in unique_links[2:5]:
        page.goto(link, wait_until='domcontentloaded')
        title = page.locator('h1.pdpr-Title').inner_text()
        price = page.locator('.pdpr-Price__Price.rs-qa-price').inner_text()
        anzahlMenge = page.locator('.rs-qa-price-base-pdsr-Grammage').inner_text()
        Anzahl = re.search(r'(\d+)\s*x\s*', anzahlMenge)
        mengeMitEinheit = re.search(r'(\d+(?:,\d+)?)\s*(ml|l)\b', anzahlMenge) 

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
    browser.close()
    
with sync_playwright() as playwright:
    run(playwright)

