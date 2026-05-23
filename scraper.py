import os
import json
import requests
from bs4 import BeautifulSoup

# Configuration from Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
URL = "https://www.caseciter.com/tag/arbitration"
HISTORY_FILE = "history.json"

def load_history():
    """Load previously scraped item identifiers to avoid duplicate alerts."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_history(history):
    """Save updated item identifiers back to the history file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(list(history), f, indent=4)

def send_telegram_message(message):
    """Send a text message to the specified Telegram channel."""
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(telegram_url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")

def scrape_and_notify():
    # Fetch page content
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch webpage. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    history = load_history()
    new_items_found = False

    # --- ADJUST SELECTORS BASED ON CASECITER'S ACTUAL HTML STRUCTURE ---
    # This assumes standard article/card structures. 
    # Inspect the website elements if structure updates are needed.
    articles = soup.find_all("article") or soup.find_all("div", class_="post") or soup.find_all("div", class_="card")

    for article in articles:
        # Try to find a link and title inside the item
        link_tag = article.find("a")
        if not link_tag or not link_tag.get("href"):
            continue
            
        title = link_tag.text.strip() or "New Arbitration Update"
        link = link_tag["href"]
        
        # Ensure absolute URL
        if link.startswith("/"):
            link = "https://www.caseciter.com" + link

        # Use the URL link as a unique identifier
        item_id = link

        if item_id not in history:
            print(f"Found new item: {title}")
            # Format message in Markdown
            message = f"🚨 *New Arbitration Update* 🚨\n\n📢 [{title}]({link})"
            send_telegram_message(message)
            
            history.add(item_id)
            new_items_found = True

    if new_items_found:
        save_history(history)
    else:
        print("No new updates found today.")

if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID environment variables.")
    else:
        scrape_and_notify()
