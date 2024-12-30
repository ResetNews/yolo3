import streamlit as st
from textblob import TextBlob
import tweepy
import pandas as pd
import matplotlib.pyplot as plt
from decouple import config

# Set up Twitter API keys from Streamlit Secrets or .env file
API_KEY = config("API_KEY")
API_SECRET_KEY = config("API_SECRET_KEY")
ACCESS_TOKEN = config("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = config("ACCESS_TOKEN_SECRET")

# Authenticate with Twitter API
def authenticate_twitter():
    auth = tweepy.OAuthHandler(API_KEY, API_SECRET_KEY)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    try:
        api.verify_credentials()
        st.success("Twitter-Authentifizierung erfolgreich!")
    except tweepy.errors.Unauthorized:
        st.error("Fehler bei der Authentifizierung: Ungültige API-Schlüssel oder Tokens.")
    except Exception as e:
        st.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
    return api

# Search for tweets mentioning the company
def search_tweets(api, query, count=100):
    try:
        tweets = tweepy.Cursor(api.search_tweets, q=query, lang="en", tweet_mode="extended").items(count)
        data = []
        for tweet in tweets:
            data.append({
                "text": tweet.full_text,
                "user": tweet.user.screen_name,
                "created_at": tweet.created_at
            })
        return pd.DataFrame(data)
    except tweepy.errors.Forbidden as e:
        st.error(f"Fehler: Zugriff verweigert. Details: {e}")
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
        api = authenticate_twitter()
        st.write("Tweets werden abgerufen...")
        tweets_df = search_tweets(api, query, count=100)

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
