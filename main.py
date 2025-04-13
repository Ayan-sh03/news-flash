import os
import requests
from typing import List, Dict
from google import genai
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()
import time

# Simple in-memory cache for summaries
CACHE_TTL = 40000  # seconds (5 minutes)
_summaries_cache = {
    "timestamp": 0,
    "data": None
}

class NewsSummarizer:
    def __init__(self):
        self.mediastack_url = "http://api.mediastack.com/v1/news"
        self.mediastack_params = {
            'access_key': os.getenv("MEDIASTACK_API_KEY"),
            'countries': 'in',
        }
        # Initialize Gemini client
        self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    def fetch_news(self) -> List[Dict]:
        """Fetch news articles from Mediastack API"""
        try:
            response = requests.get(self.mediastack_url, params=self.mediastack_params)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news: {e}")
            return []

    def extract_content(self, url: str) -> str:
        """Extract full article content using BeautifulSoup"""
        try:
            # Add headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style","a"]):
                script.decompose()

            # Extract text content
            text = soup.get_text()

            # Clean up text: remove blank lines and excessive whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text
        except Exception as e:
            print(f"Error extracting content: {e}")
            return ""

    def generate_summary(self, content: str) -> str:
        """Generate a 60-word summary using Gemini API"""
        try:
            prompt = f"""
            Summarize the following article in exactly 60 words or less, maintaining key information:

            {content}
            """
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            return ""

    def format_article(self, article: Dict) -> str:
        """Format article details for display"""
        return f"""
Title: {article.get('title', 'N/A')}
Source: {article.get('source', 'N/A')}
URL: {article.get('url', 'N/A')}
Published: {article.get('published_at', 'N/A')}
"""
# --- Flask App Setup ---
app = Flask(__name__)

@app.route('/summaries', methods=['GET'])
def get_summaries():
    """API endpoint to get news summaries."""
    now = time.time()
    if _summaries_cache["data"] is not None and (now - _summaries_cache["timestamp"] < CACHE_TTL):
        return jsonify(_summaries_cache["data"])

    summarizer = NewsSummarizer()
    articles = summarizer.fetch_news()
    results = []

    if not articles:
        return jsonify({"message": "No articles found."}), 404

    for article in articles:
        summary_data = {
            'title': article.get('title', 'N/A'),
            'source': article.get('source', 'N/A'),
            'url': article.get('url', 'N/A'),
            'published': article.get('published_at', 'N/A'),
            'summary': None,
            'error': None
        }

        url = article.get('url')
        if url:
            content = summarizer.extract_content(url)
            if content:
                summary = summarizer.generate_summary(content)
                if summary:
                    summary_data['summary'] = summary
                else:
                    summary_data['error'] = "Could not generate summary."
            else:
                summary_data['error'] = "Could not extract article content."
        else:
            summary_data['error'] = "No URL available for article."

        results.append(summary_data)

    _summaries_cache["timestamp"] = time.time()
    _summaries_cache["data"] = results
    return jsonify(results)

# Keep the original main function if needed for direct script execution

def main():
    summarizer = NewsSummarizer()

    # Fetch news articles
    print("Fetching news articles...")
    articles = summarizer.fetch_news()

    if not articles:
        print("No articles found.")
        return

    # Process each article
    for article in articles:
        print("\n" + "="*50)
        print(summarizer.format_article(article))

        # Extract full content
        url = article.get('url')
        if url:
            print("Extracting content...")
            content = summarizer.extract_content(url)
            if content:
                print("Generating summary...")
                # Generate and display summary
                summary = summarizer.generate_summary(content)
                if summary:
                    print("Summary:", summary)
                else:
                    print("Could not generate summary.")
            else:
                print("Could not extract article content.")
        else:
            print("No URL available for article.")

if __name__ == "__main__":
    # Run the Flask app instead of the original main function
    app.run(debug=True, host='0.0.0.0', port=5000)
    # To run the original script logic, you could still call main() here
    # or run the script with a specific argument, but the primary
    # execution path is now the Flask server.
    # main()