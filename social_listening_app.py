import streamlit as st
from textblob import TextBlob
import tweepy
import pandas as pd
import matplotlib.pyplot as plt

# Set up Twitter API keys from Streamlit Secrets
BEARER_TOKEN = st.secrets["BEARER_TOKEN"]

# Authenticate with Twitter API v2
def authenticate_twitter():
    client = tweepy.Client(bearer_token=BEARER_TOKEN)
    try:
        st.success("Twitter-Authentifizierung erfolgreich!")
    except Exception as e:
        st.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
    return client

# Search for tweets using Twitter API v2 with rate limit handling
def search_tweets_v2(client, query, count=10):
    try:
        tweets = client.search_recent_tweets(query=query, max_results=count, tweet_fields=["created_at", "text", "author_id"])
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
        st.error("Rate Limit erreicht. Wartezeit wird berechnet...")
        # Wartezeit aus der Header-Information berechnen
        reset_time = client.last_response.headers.get("x-rate-limit-reset")
        if reset_time:
            wait_time = int(reset_time) - int(time.time())
            st.warning(f"Wartezeit: {wait_time} Sekunden")
            time.sleep(max(wait_time, 1))
        else:
            st.error("Rate Limit-Reset-Zeit nicht verfügbar. Bitte 15 Minuten warten.")
            time.sleep(900)  # 15 Minuten warten
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
        tweets_df = search_tweets_v2(client, query, count=10)

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
