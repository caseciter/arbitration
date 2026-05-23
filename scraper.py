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
    """Load previously scraped links to avoid duplicate alerts."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_history(history):
    """Save updated links back to the history tracking file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(list(history), f, indent=4)

def send_telegram_message(message):
    """Post message to the assigned Telegram channel."""
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(telegram_url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")

def scrape_and_notify():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch webpage. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    history = load_history()
    new_items_found = False

    # CaseCiter wraps its updates inside structural element blocks (like standard blogs)
    articles = soup.find_all("article") or soup.find_all("div", class_="post")

    for article in articles:
        link_tag = article.find("a")
        if not link_tag or not link_tag.get("href"):
            continue
            
        title = link_tag.text.strip()
        link = link_tag["href"]
        
        # Build absolute URLs if they appear relative
        if link.startswith("/"):
            link = "https://www.caseciter.com" + link

        # Identify items uniquely using their exact link
        if link not in history:
            print(f"New CrPC Update Found: {title}")
            
            # Format the Telegram Notification text
            message = (
                f"⚖️ *New CrPC Update (CaseCiter)* ⚖️\n\n"
                f"📝 *Title:* {title}\n\n"
                f"🔗 [Read Full Notes Here]({link})"
            )
            
            send_telegram_message(message)
            history.add(link)
            new_items_found = True

    if new_items_found:
        save_history(history)
    else:
        print("No new CrPC cases found today.")

if __name__ == "__main__":
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Missing Telegram Environment Secrets.")
    else:
        scrape_and_notify()
