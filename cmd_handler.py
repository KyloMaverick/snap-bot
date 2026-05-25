import requests
import time
import threading
from config import TELEGRAM_BOT_TOKEN

TOKEN = TELEGRAM_BOT_TOKEN
last_id = 0

def send(chat_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=5
        )
    except:
        pass

def loop():
    global last_id
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            r = requests.get(url, params={"offset": last_id + 1, "timeout": 10})
            for upd in r.json().get("result", []):
                last_id = upd["update_id"]
                msg = upd.get("message")
                if msg and "text" in msg:
                    chat = msg["chat"]["id"]
                    txt = msg["text"].lower()
                    if txt == "/status":
                        send(chat, "✅ Bot aktif | Mode SAFE | Balance $15.80")
                    elif txt == "/start":
                        send(chat, "🤖 SNAP Bot ready. Kirim /status")
                    elif txt == "/balance":
                        send(chat, "💰 Balance: $15.80")
        except:
            pass
        time.sleep(2)

def start():
    threading.Thread(target=loop, daemon=True).start()
