import asyncio
import sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from playwright.sync_api import sync_playwright
import time

import os


def scrape_google_maps_reviews(place_url: str, max_reviews: int = 50):

    
    reviews = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(place_url, timeout=60000)

        page.wait_for_selector('div[role="article"]', timeout=10000)

        scroll_attempts = 0
        max_scrolls = max_reviews // 10 + 3

        while len(reviews) < max_reviews and scroll_attempts < max_scrolls:
            page.mouse.wheel(0, 3000)
            time.sleep(2)
            review_elements = page.query_selector_all('div[role="article"]')

            for r in review_elements:
                try:
                    text = r.query_selector('span[jsname="bN97Pc"]').inner_text()
                    if text and text not in reviews:
                        reviews.append(text)
                        if len(reviews) >= max_reviews:
                            break
                except:
                    continue

            scroll_attempts += 1

        browser.close()
    return reviews
