import requests
import threading
import time

TOKEN = "7220766351:AAHn0djbRMW2r-OmdPdsHxZkCvyPT2yYx5w"
last_id = 0

def kirim(chat_id, teks):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": teks})
    except:
        pass

def loop():
    global last_id
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            r = requests.get(url, params={"offset": last_id + 1, "timeout": 10})
            for u in r.json().get("result", []):
                last_id = u["update_id"]
                msg = u.get("message")
                if msg and "text" in msg:
                    chat = msg["chat"]["id"]
                    teks = msg["text"].lower()
                    if teks == "/status":
                        kirim(chat, "✅ Bot aktif | Mode SAFE | Balance $15.80")
                    elif teks == "/start":
                        kirim(chat, "🤖 SNAP Bot ready. Kirim /status")
                    elif teks == "/balance":
                        kirim(chat, "💰 Balance: $15.80")
        except:
            pass
        time.sleep(2)

def start():
    threading.Thread(target=loop, daemon=True).start()
