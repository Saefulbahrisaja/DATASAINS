import streamlit as st
import pandas as pd
import os
import re
import nltk
import subprocess
import matplotlib.pyplot as plt
import seaborn as sns

from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from wordcloud import WordCloud
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from sklearn.feature_extraction.text import TfidfTransformer

nltk.download('punkt')
nltk.download('stopwords')

# ==== Load Stopwords ====
def load_stopwords(file_path):
    stopwords_list = set(stopwords.words("indonesian"))
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            additional_stopwords = {line.strip() for line in f.readlines()}
        stopwords_list.update(additional_stopwords)
    except Exception as e:
        st.warning(f"Terjadi kesalahan saat memuat stopword list dari file: {e}")
    return stopwords_list

stop_words = load_stopwords("stopwords.txt")
factory = StemmerFactory()
stemmer = factory.create_stemmer()

# ==== Scraper YouTube ====
def scrape_youtube_comments(url, limit=300):
    output_file = "comments.csv"
    if os.path.exists(output_file):
        os.remove(output_file)
    cmd = [
        "youtube-comment-downloader",
        "--url", url,
        "--output", output_file,
        "--limit", str(limit)
    ]
    subprocess.run(cmd)
    return pd.read_csv(output_file, on_bad_lines='skip', quoting=3, encoding='utf-8')

# ==== Scraper TikTok ====
def scrape_tiktok_comments(url, limit=300):
    output_file = "comments_tiktok.csv"
    if os.path.exists(output_file):
        os.remove(output_file)
    cmd = [
        "tiktok-comment-scraper",
        "--url", url,
        "--number", str(limit),
        "--output", output_file
    ]
    subprocess.run(cmd)
    return pd.read_csv(output_file, on_bad_lines='skip', quoting=3, encoding='utf-8')

# ==== Preprocessing ====
def get_root_words(text):
    text = str(text).lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    words = text.split()
    return [stemmer.stem(w) for w in words if w not in stop_words and len(w) > 1]

def clean_text(text):
    return " ".join(get_root_words(text))

# ==== Sentiment Analysis ====
def load_lexicon(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f.readlines())
    except Exception as e:
        st.warning(f"Gagal memuat kamus dari {file_path}: {e}")
        return set()

positive_words = load_lexicon("positif.txt")
negative_words = load_lexicon("negatif.txt")

def get_sentiment(text):
    words = text.split()
    pos = sum(1 for w in words if w in positive_words)
    neg = sum(1 for w in words if w in negative_words)
    if pos > neg:
        return "Positif"
    elif neg > pos:
        return "Negatif"
    else:
        return "Netral"
        
# ==== Load Emotion Lexicon ====
def load_emotion_lexicon(file_path):
    emotions = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    emotion, words = line.strip().split(":")
                    emotions[emotion.strip()] = set(w.strip() for w in words.split(","))
    except Exception as e:
        st.warning(f"Gagal memuat leksikon emosi dari {file_path}: {e}")
    return emotions

emotion_lexicon = load_emotion_lexicon("emosi.txt")

def get_emotion(text):
    words = text.split()
    scores = {e: 0 for e in emotion_lexicon}
    for word in words:
        for emotion, wordlist in emotion_lexicon.items():
            if word in wordlist:
                scores[emotion] += 1
    if not any(scores.values()):
        return 
    return max(scores, key=scores.get)


# ==== UI ====
st.title("Analisis Komentar YouTube & TikTok: Sentimen dan Topik (Bahasa Indonesia)")

platform = st.selectbox("Pilih Platform:", ["YouTube", "TikTok"])
url = st.text_input(f"Masukkan URL video {platform}:", "")
limit = st.slider("Jumlah komentar:", 50, 5000, 300, 100)

if st.button("Analisis Sekarang") and url:
    with st.spinner("Mengambil komentar..."):
        try:
            df = scrape_youtube_comments(url, limit) if platform == "YouTube" else scrape_tiktok_comments(url, limit)
            if df.empty:
                st.warning("Tidak ada komentar ditemukan.")
                st.stop()
        except Exception as e:
            st.error(f"Gagal mengambil komentar: {e}")
            st.stop()

    comment_col = next((col for col in df.columns if "text" in col.lower() or "comment" in col.lower()), None)
    if not comment_col:
        st.error("Kolom komentar tidak ditemukan.")
        st.stop()

    df["root_words"] = df[comment_col].astype(str).apply(get_root_words)
    df["clean_text"] = df["root_words"].apply(lambda x: " ".join(x))
    df = df[df["clean_text"].str.strip() != ""]

    if df.empty:
        st.error("Semua komentar kosong setelah dibersihkan.")
        st.stop()

    df["sentimen"] = df["clean_text"].apply(get_sentiment)
    df["emosi"] = df["clean_text"].apply(get_emotion)

    # ==== Sentiment Chart ====
    st.subheader("Distribusi Sentimen")
    counts = df["sentimen"].value_counts()
    fig, ax = plt.subplots()
    sentimen_colors = {
        "Positif": "#4CAF50",
        "Negatif": "#F44336",
        "Netral": "#9E9E9E"
    }
    sns.barplot(
        x=counts.index, 
        y=counts.values, 
        ax=ax, 
        palette=[sentimen_colors.get(s, "#607D8B") for s in counts.index]
    )
    ax.set_ylabel("Jumlah Komentar")
    st.pyplot(fig)

    # ==== Emotion Chart ====
    st.subheader("Distribusi Emosi")
    emotion_counts = df["emosi"].value_counts()
    emotion_colors = {
        "senang": "#4CAF50",
        "sedih": "#2196F3",
        "marah": "#F44336",
        "takut": "#9C27B0",
        "Netral": "#9E9E9E"
    }
    fig, ax = plt.subplots()
    sns.barplot(
        x=emotion_counts.index,
        y=emotion_counts.values,
        ax=ax,
        palette=[emotion_colors.get(e, "#607D8B") for e in emotion_counts.index]
    )
    ax.set_ylabel("Jumlah Komentar")
    st.pyplot(fig)

    # ==== Topic Modeling ====
    st.subheader("Topik Komentar (LDA + WordCloud)")
    vectorizer = CountVectorizer(max_df=0.9, min_df=2)
    X = vectorizer.fit_transform(df["clean_text"])
    lda = LatentDirichletAllocation(n_components=5, random_state=42)
    lda.fit(X)

    vocab = vectorizer.get_feature_names_out()
    combined_word_freq = {}

    # Apply TF-IDF weighting
    tfidf_transformer = TfidfTransformer()
    X_tfidf = tfidf_transformer.fit_transform(X)

    for i, topic in enumerate(lda.components_):
        top_idx = topic.argsort()[:-11:-1]
        top_words = [(vocab[j], X_tfidf[:, j].mean()) for j in top_idx]
        label = vocab[top_idx[0]]
        st.markdown(f"#### Topik {i+1}: {label.capitalize()}")
        st.write(", ".join(w for w, _ in top_words))
        for w, score in top_words:
            combined_word_freq[w] = combined_word_freq.get(w, 0) + score

    # ==== Word Cloud ====
    st.markdown("#### Word Cloud Gabungan")
    wc = WordCloud(width=800, height=500, background_color="white").generate_from_frequencies(combined_word_freq)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)

    with st.expander("🔍 Lihat Data Lengkap"):
        st.dataframe(df[[comment_col, "root_words", "clean_text", "sentimen"]])
        st.download_button("Unduh Data", df.to_csv(index=False).encode('utf-8'), "data.csv", "text/csv")
        st.download_button("Unduh Komentar", df[comment_col].to_csv(index=False).encode('utf-8'), "komentar.csv", "text/csv")