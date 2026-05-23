import os
import json
import requests
from bs4 import BeautifulSoup

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
URL = "https://www.caseciter.com/tag/crpc/"
HISTORY_FILE = "history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(list(history), f, indent=4)

def send_telegram_link(link):
    """Sends only the plain link to the Telegram channel."""
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": link  # Sends raw URL string directly
    }
    try:
        response = requests.post(telegram_url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending link to Telegram: {e}")

def scrape_and_notify():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch webpage. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    history = load_history()
    new_items_found = False

    articles = soup.find_all("article") or soup.find_all("div", class_="post")

    for article in articles:
        link_tag = article.find("a")
        if not link_tag or not link_tag.get("href"):
            continue
            
        link = link_tag["href"]
        
        # Build absolute URLs if they appear relative
        if link.startswith("/"):
            link = "https://www.caseciter.com" + link

        # If link hasn't been sent before, send just the link
        if link not in history:
            print(f"Sending new link: {link}")
            send_telegram_link(link)
            history.add(link)
            new_items_found = True

    if new_items_found:
        save_history(history)
    else:
        print("No new links found today.")

if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Missing Telegram Environment Secrets.")
    else:
        scrape_and_notify()
