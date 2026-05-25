import requests
import threading
import time

TOKEN = "8967861560:AAEGe_Y4Jqn7BB0WIpgYnvlm8eIFjQcPVu8"  # GANTI dengan token asli lo
LAST_UPDATE = 0

def send(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def loop():
    global LAST_UPDATE
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            r = requests.get(url, params={"offset": LAST_UPDATE + 1, "timeout": 10})
            for upd in r.json().get("result", []):
                LAST_UPDATE = upd["update_id"]
                msg = upd.get("message")
                if msg and "text" in msg:
                    chat = msg["chat"]["id"]
                    txt = msg["text"].lower()
                    if txt == "/status":
                        send(chat, "✅ Bot aktif | Mode SAFE | Balance $15.80")
                    elif txt == "/start":
                        send(chat, "🤖 SNAP Bot siap. Kirim /status")
                    elif txt == "/balance":
                        send(chat, "💰 Balance: $15.80")
        except:
            pass
        time.sleep(2)

def start():
    threading.Thread(target=loop, daemon=True).start()