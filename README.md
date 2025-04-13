# EsportsBot AI

A streamlined, AI-powered chatbot that leverages Google’s Gemini LLM and the official Esports Earnings API to provide real-time esports data. Ask questions about players, teams, tournaments, or specific games, and EsportsBot AI will fetch relevant data and summarize it in clear, conversational responses.

---

## Project Files

1. **`esports.ipynb`**  
   - A Jupyter Notebook demonstrating end-to-end usage of the Esports Earnings API and Gemini LLM.  
   - Showcases how to make direct API requests, integrate the LLM for summarization, and prototype queries.

2. **`esports_app.py`**  
   - A Streamlit-based web application that provides a user-friendly chatbot interface.  
   - Leverages Google’s Gemini 2.0 Flash model to interpret user queries, choose the right Esports Earnings API endpoint, fetch data, and summarize responses.  
   - **Usage**:  
     ```bash
     streamlit run esports_app.py
     ```
     - Make sure to install the required dependencies (see [Installation](#installation)) and set your environment variables/keys.

3. **`esports_games.csv`**  
   - A CSV containing scraped game IDs and names from Esports Earnings.  
   - The chatbot reads from this file to dynamically map textual game names (like `"Valorant"`) to numeric IDs (e.g., `646`), avoiding hardcoding.  
   - If the user references a game name in their query, the app checks this file to find the correct ID.

---

## Installation

1. **Clone or Download** this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
