import streamlit as st
from textblob import TextBlob
import tweepy
import pandas as pd
import matplotlib.pyplot as plt
import time
from decouple import config

# Set up Twitter API keys from Streamlit Secrets or .env file
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAALhUxwEAAAAAW2qljtJBEia39TG7mCIHQUFxIHs%3Dq7X0RqBHiOlrlY0CQMXLNRtgMyLsxchif4QAYqJd8dWOY1aLuf"

# Authenticate with Twitter API v2
def authenticate_twitter():
    client = tweepy.Client(bearer_token=BEARER_TOKEN)
    try:
        st.success("Twitter-Authentifizierung erfolgreich!")
    except Exception as e:
        st.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
    return client

# Check rate limit status
def check_rate_limit(client):
    try:
        rate_limit_status = client.get_rate_limit_status()
        remaining = rate_limit_status['resources']['search']['/search/tweets']['remaining']
        reset_time = rate_limit_status['resources']['search']['/search/tweets']['reset']
        st.write(f"Verbleibende Anfragen: {remaining}")
        if remaining == 0:
            wait_time = reset_time - int(time.time())
            st.warning(f"Rate Limit erreicht. Wartezeit: {wait_time} Sekunden")
            time.sleep(wait_time + 1)
    except Exception as e:
        st.error(f"Fehler beim Überprüfen des Rate Limits: {e}")

# Search for tweets using Twitter API v2 with rate limit handling
def search_tweets_v2(client, query, count=5):
    try:
        check_rate_limit(client)
        tweets = client.search_recent_tweets(query=query, max_results=count, tweet_fields=["created_at", "text", "author_id"])
        time.sleep(15)  # Erhöhte Pause zwischen den Anfragen, um Rate Limits zu vermeiden
        data = []
        if tweets.data:
            for tweet in tweets.data:
                data.append({
                    "text": tweet.text,
                    "user": tweet.author_id,
                    "created_at": tweet.created_at
                })
        return pd.DataFrame(data)
    except tweepy.errors.TooManyRequests:
        st.error("Rate Limit erreicht. Bitte warten Sie 15 Minuten und versuchen Sie es erneut.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ein Fehler ist aufgetreten: {e}")
        return pd.DataFrame()

# Perform sentiment analysis
def analyze_sentiment(tweets_df):
    def get_sentiment(text):
        analysis = TextBlob(text)
        if analysis.sentiment.polarity > 0:
            return "Positive"
        elif analysis.sentiment.polarity < 0:
            return "Negative"
        else:
            return "Neutral"

    tweets_df["sentiment"] = tweets_df["text"].apply(get_sentiment)
    return tweets_df

# Visualize sentiment distribution
def visualize_sentiment(tweets_df):
    sentiment_counts = tweets_df["sentiment"].value_counts()
    fig, ax = plt.subplots()
    sentiment_counts.plot(kind="bar", title="Sentiment Analysis", ylabel="Count", xlabel="Sentiment", ax=ax)
    st.pyplot(fig)

# Streamlit app
st.title("Social Listening Tool")

st.write("Willkommen beim Social Listening Tool! Geben Sie ein Keyword ein, um die Social-Media-Stimmung zu analysieren.")

if st.button("Test Authentifizierung"):
    authenticate_twitter()

query = st.text_input("Geben Sie ein Keyword oder einen Firmennamen ein:")

if st.button("Analysieren"):
    if query:
        client = authenticate_twitter()
        st.write("Tweets werden abgerufen...")
        tweets_df = search_tweets_v2(client, query, count=5)

        if not tweets_df.empty:
            st.write(f"Gefundene Tweets für '{query}':", tweets_df.head())
            st.write("Stimmungsanalyse wird durchgeführt...")
            tweets_df = analyze_sentiment(tweets_df)

            visualize_sentiment(tweets_df)

            st.write("Vorschläge basierend auf negativer Stimmung:")
            negative_tweets = tweets_df[tweets_df["sentiment"] == "Negative"]
            if not negative_tweets.empty:
                for tweet in negative_tweets["text"]:
                    st.write(f"- {tweet}")
            else:
                st.write("Keine negative Stimmung gefunden. Gut gemacht!")
        else:
            st.write("Keine Tweets gefunden. Versuchen Sie es mit einem anderen Keyword.")
    else:
        st.write("Bitte geben Sie ein Keyword ein.")
