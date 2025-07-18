import pandas as pd
from transformers import pipeline
import streamlit as st

@st.cache_resource
def load_sentiment_model():
    return pipeline("text-classification", model="indobenchmark/indobert-base-p1-sentiment")

def analyze_sentiment(reviews):
    model = load_sentiment_model()
    df = pd.DataFrame(reviews, columns=["review"])
    df["sentimen"] = df["review"].apply(lambda x: model(str(x))[0]["label"])
    return df
