import streamlit as st
import requests
import google.generativeai as genai

genai.configure(api_key="YOUR_GEMINI_API_KEY")

ESPORTS_API_KEY = "YOUR_ESPORTS_API_KEY"
BASE_URL = "http://api.esportsearnings.com/v0/"

def fetch_player_data(player_id):
    response = requests.get(f"{BASE_URL}LookupPlayerById", params={"apikey": ESPORTS_API_KEY, "playerid": player_id})
    return response.json()

def summarize_data(query, api_response):
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"User Query: {query}\n\nAPI Data: {api_response}\n\nSummarize this data clearly:"
    response = model.generate_content(prompt)
    return response.text

st.title("🎮 EsportsBot AI with Gemini")
query = st.text_input("Ask EsportsBot anything about esports earnings:")

if st.button("Get Information"):
    player_id = 1490  # Example player id, replace dynamically as needed
    api_data = fetch_player_data(player_id)
    summary = summarize_data(query, api_data)
    st.write(summary)
