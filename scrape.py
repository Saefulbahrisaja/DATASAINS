import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Setelah event loop policy diset, baru import lain
from playwright.sync_api import sync_playwright
import time
import streamlit as st


def scrape_google_reviews(place_url, max_reviews):
    reviews = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(place_url)
        
        try:
            page.wait_for_selector('button[jsaction="pane.reviewChart.moreReviews"]', timeout=10000)
            see_all_button = page.query_selector('button[jsaction="pane.reviewChart.moreReviews"]')
            if see_all_button:
                see_all_button.click()
                time.sleep(3)
        except Exception as e:
            print("Tidak menemukan tombol 'See all reviews' atau timeout:", e)

        review_selector = 'div[data-review-id]'
        reviews_collected = set()

        while len(reviews) < max_reviews:
            page.evaluate('window.scrollBy(0, window.innerHeight)')
            time.sleep(2)

            review_elements = page.query_selector_all(review_selector)

            for review_el in review_elements:
                review_id = review_el.get_attribute('data-review-id')
                if review_id in reviews_collected:
                    continue
                
                comment_el = review_el.query_selector('span[jsname="bN97Pc"]')
                comment = comment_el.inner_text().strip() if comment_el else ''

                star_el = review_el.query_selector('span[role="img"]')
                rating = None
                if star_el:
                    aria_label = star_el.get_attribute('aria-label')
                    if aria_label and "Rated" in aria_label:
                        try:
                            rating = int(aria_label.split()[1])
                        except:
                            rating = None

                if comment:
                    reviews.append({"comment": comment, "rating": rating})
                    reviews_collected.add(review_id)

                if len(reviews) >= max_reviews:
                    break

            if len(reviews) >= max_reviews:
                break

        browser.close()
    return reviews

# Streamlit UI code sama seperti sebelumnya...


st.title("Scrape Google Maps Reviews")

place_url = st.text_input("Masukkan URL Google Maps tempat", 
    "https://www.google.com/maps/place/Starbucks/@-6.2087634,106.845599,17z/data=!4m7!3m6!1s0x2e69f14f1e0bbdf9:0x1b9f7e06b21a5e3b!8m2!3d-6.2087634!4d106.8477877!9m1!1b1")

max_reviews = st.slider("Maksimum jumlah review", 1, 50, 10)

if st.button("Mulai scraping"):
    with st.spinner("Sedang scraping..."):
        try:
            results = scrape_google_reviews(place_url, max_reviews)
            if results:
                for i, review in enumerate(results, 1):
                    st.markdown(f"**Review #{i}**")
                    st.markdown(f"- Rating: {review['rating']} ⭐")
                    st.markdown(f"- Komentar: {review['comment']}\n")
            else:
                st.write("Tidak ada review yang ditemukan.")
        except Exception as e:
            st.error(f"Terjadi error: {e}")
