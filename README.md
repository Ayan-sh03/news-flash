# NewsFlash

A fast, simple API for fetching and summarizing the latest news headlines.

## Features
- Fetches top news from India (English)
- Summarizes each article using Gemini AI
- Caches results for 5 minutes to reduce API calls
- Easy-to-use `/summaries` endpoint (JSON output)

## Setup

1. Clone the repository and install requirements:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with your Gemini API key:
   ```
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

3. Run the server:
   ```
   python main.py
   ```

4. Get news summaries:
   ```
   curl http://localhost:5000/summaries