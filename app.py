import streamlit as st
import pandas as pd
import re
import nltk
import matplotlib.pyplot as plt
import seaborn as sns
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.decomposition import LatentDirichletAllocation
from wordcloud import WordCloud
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from downloader import get_comments_from_url

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
        st.warning(f"Gagal memuat stopword dari file: {e}")
    return stopwords_list

stop_words = load_stopwords("stopwords.txt")
stemmer = StemmerFactory().create_stemmer()

# ==== Scrape YouTube ====
def scrape_youtube_comments(url, limit=300):
    try:
        comments = get_comments_from_url(url, sort_by="top", count=limit)
        df = pd.DataFrame(comments)
        return df
    except Exception as e:
        st.error(f"Gagal mengambil komentar: {e}")
        return pd.DataFrame()

# ==== Preprocessing ====
def get_root_words(text):
    text = str(text).lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    words = text.split()
    return [stemmer.stem(w) for w in words if w not in stop_words and len(w) > 1]

def clean_text(text):
    return " ".join(get_root_words(text))

# ==== Sentiment ====
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
    return "Netral"

# ==== Emosi ====
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
    return max(scores, key=scores.get) if any(scores.values()) else "Netral"

# ==== UI ====
st.title("📊 Analisis Komentar YouTube (Sentimen, Emosi, Topik)")

url = st.text_input("Masukkan URL video YouTube:")
limit = st.slider("Jumlah komentar:", 50, 5000, 300, 100)

if st.button("Analisis Sekarang") and url:
    with st.spinner("Mengambil komentar..."):
        df = scrape_youtube_comments(url, limit)

    if df.empty:
        st.warning("Tidak ada komentar ditemukan.")
        st.stop()

    comment_col = next((col for col in df.columns if "text" in col.lower() or "comment" in col.lower()), None)
    if not comment_col:
        st.error("Kolom komentar tidak ditemukan.")
        st.stop()

    df["root_words"] = df[comment_col].astype(str).apply(get_root_words)
    df["clean_text"] = df["root_words"].apply(lambda x: " ".join(x))
    df = df[df["clean_text"].str.strip() != ""]

    if df.empty:
        st.warning("Komentar kosong setelah dibersihkan.")
        st.stop()

    df["sentimen"] = df["clean_text"].apply(get_sentiment)
    df["emosi"] = df["clean_text"].apply(get_emotion)

    # Sentimen Chart
    st.subheader("📈 Distribusi Sentimen")
    sentimen_counts = df["sentimen"].value_counts()
    fig, ax = plt.subplots()
    sns.barplot(x=sentimen_counts.index, y=sentimen_counts.values, palette="Set2", ax=ax)
    ax.set_ylabel("Jumlah Komentar")
    st.pyplot(fig)

    # Emosi Chart
    st.subheader("😊 Distribusi Emosi")
    emosi_counts = df["emosi"].value_counts()
    fig, ax = plt.subplots()
    sns.barplot(x=emosi_counts.index, y=emosi_counts.values, palette="Set3", ax=ax)
    ax.set_ylabel("Jumlah Komentar")
    st.pyplot(fig)

    # LDA Topik
    st.subheader("🧠 Topik Komentar (LDA + WordCloud)")
    vectorizer = CountVectorizer(max_df=0.9, min_df=2)
    X = vectorizer.fit_transform(df["clean_text"])
    lda = LatentDirichletAllocation(n_components=5, random_state=42)
    lda.fit(X)

    vocab = vectorizer.get_feature_names_out()
    tfidf = TfidfTransformer().fit_transform(X)
    topik_freq = {}

    for i, topic in enumerate(lda.components_):
        top_idx = topic.argsort()[:-11:-1]
        top_words = [(vocab[j], tfidf[:, j].mean()) for j in top_idx]
        label = vocab[top_idx[0]]
        st.markdown(f"**Topik {i+1}: {label.capitalize()}**")
        st.write(", ".join(w for w, _ in top_words))
        for w, score in top_words:
            topik_freq[w] = topik_freq.get(w, 0) + score

    wc = WordCloud(width=800, height=500, background_color="white").generate_from_frequencies(topik_freq)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)

    with st.expander("📥 Lihat & Unduh Data"):
        st.dataframe(df[[comment_col, "clean_text", "sentimen", "emosi"]])
        st.download_button("📄 Unduh Data CSV", df.to_csv(index=False).encode("utf-8"), "komentar_analisis.csv", "text/csv")
