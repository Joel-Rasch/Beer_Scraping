import time
from datetime import datetime
import random
import re
from playwright.sync_api import sync_playwright


def scroll_and_wait(page, scroll_count=10, delay=1):
    last_height = page.evaluate('document.body.scrollHeight')
    scroll_distance = last_height // (scroll_count-1)
    while True:
        for i in range(scroll_count):
            page.evaluate(f'window.scrollBy(0, {scroll_distance})')
            time.sleep(delay)
            print(f"Scroll {i+1}/{scroll_count}")
        button = page.query_selector('button.s-load-more__button')
        if not button is None:
            button.click()
            print(f"'Load more' button found. Clicking...")
            time.sleep(0.2)
        else:
            break

def extract_links(page):
    return page.evaluate('''
        () => {
            const links = Array.from(document.querySelectorAll('a'));
            return links.map(link => link.href).filter(href => href.includes('/p/'));
        }
    ''')

def run(playwright):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    try:
        page.goto("https://www.lidl.de/h/bier/h10023946?pageId=10005566%2F10023946", wait_until='networkidle')
        
        #print("Initial page load complete. Starting content loading process...")
        page.click('text="Zustimmen"') 
        # Scroll process
        scroll_and_wait(page, scroll_count=20, delay=0.001)
        links = extract_links(page)
        unique_links = list(set(links))
        
        for link in unique_links:
            try:
                page.goto(link, wait_until='domcontentloaded')
                
                title = page.query_selector('h1.keyfacts__title').inner_text()
                price = page.query_selector('div.m-price__price').inner_text().replace(".",",")
                currency = "Euro"
                anbieter = "Lidl"
                plz = "online"
                scrape_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                mengeMitEinheit = page.query_selector('li.wine.bottlesize span').inner_text()
                menge, einheit = re.search(r'(\d+)\-([a-zA-Z]+)', mengeMitEinheit).groups()

                if title and price:
                    print(f"Title: {title}")
                    print(f"Price: {price}")
                    print(f"Currency: {currency}")
                    print(f"Anbieter: {anbieter}")
                    print(f"PLZ: {plz}")
                    print(f"Scrape Date: {scrape_date}")
                    print(f"Menge: {menge}")
                    print(f"Einheit: {einheit}")
                    print("-" * 50) 
                else:
                    print(f"Error retrieving details from {link}")
            except Exception as e:
                print(f"Error processing {link}: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        browser.close()

with sync_playwright() as playwright:
    run(playwright)