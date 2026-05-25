"""
SIMPLE TELEGRAM COMMAND HANDLER
Menjawab /status, /start, /balance
"""

import requests
import threading
import time
from config import TELEGRAM_BOT_TOKEN

TOKEN = TELEGRAM_BOT_TOKEN
last_update_id = 0

def send_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=5)
    except Exception as e:
        print(f"Send error: {e}")

def get_updates():
    global last_update_id
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"offset": last_update_id + 1, "timeout": 10}, timeout=15)
        data = r.json()
        for update in data.get("result", []):
            last_update_id = update["update_id"]
            msg = update.get("message")
            if msg and msg.get("text"):
                chat_id = msg["chat"]["id"]
                text = msg["text"].lower()
                if text == "/status":
                    send_message(chat_id, "✅ Bot aktif | Mode SAFE | Balance: $15.80")
                elif text == "/start":
                    send_message(chat_id, "🤖 SNAP Bot ready. Kirim /status atau /balance")
                elif text == "/balance":
                    send_message(chat_id, "💰 Balance: $15.80 | PnL: $0.00")
                elif text == "/help":
                    send_message(chat_id, "Commands: /start, /status, /balance")
    except Exception as e:
        print(f"Get updates error: {e}")

def run_polling():
    print("✅ Telegram command handler started (polling mode)")
    while True:
        try:
            get_updates()
        except Exception as e:
            print(f"Polling error: {e}")
        time.sleep(2)

def start():
    thread = threading.Thread(target=run_polling, daemon=True)
    thread.start()