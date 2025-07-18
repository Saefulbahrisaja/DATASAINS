import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from scraper import scrape_google_maps_reviews
from analyzer import analyze_sentiment

st.set_page_config(page_title="Analisis Sentimen Google Maps", layout="centered")

st.title("📍 Analisis Sentimen Google Maps Review")
st.write("Upload file atau masukkan URL Google Maps untuk analisis sentimen.")

# --- Upload file CSV ---
uploaded_file = st.file_uploader("📄 Upload File CSV (kolom: review)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if "review" not in df.columns:
        st.error("Kolom 'review' tidak ditemukan.")
    else:
        st.success(f"{len(df)} ulasan dimuat.")
        df_result = analyze_sentiment(df["review"].tolist())

        st.subheader("📊 Visualisasi Sentimen")
        counts = df_result["sentimen"].value_counts()
        st.bar_chart(counts)

        st.subheader("📥 Unduh Hasil")
        st.dataframe(df_result)
        csv = df_result.to_csv(index=False).encode("utf-8")
        st.download_button("Unduh CSV", data=csv, file_name="hasil_sentimen.csv")

# --- URL Input ---
st.markdown("---")
st.subheader("🔍 Scrape dari Google Maps")
place_url = st.text_input("Masukkan URL Google Maps tempat")

if place_url and st.button("Scrape & Analisis"):
    with st.spinner("Mengambil dan menganalisis ulasan..."):
        reviews = scrape_google_maps_reviews(place_url, max_reviews=100)
        if not reviews:
            st.error("Gagal mengambil ulasan.")
        else:
            df_result = analyze_sentiment(reviews)

            st.subheader("📊 Visualisasi Sentimen")
            counts = df_result["sentimen"].value_counts()
            st.bar_chart(counts)

            st.subheader("📥 Unduh Hasil")
            st.dataframe(df_result)
            csv = df_result.to_csv(index=False).encode("utf-8")
            st.download_button("Unduh CSV", data=csv, file_name="hasil_sentimen_scraped.csv")
