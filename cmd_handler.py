"""
CMD HANDLER
FIX 5: Terhubung ke bot_state real, bukan hardcoded string
"""
import requests
import threading
import time
from config import TELEGRAM_BOT_TOKEN

TOKEN   = TELEGRAM_BOT_TOKEN
last_id = 0

# Import shared state dari main
# Pakai lazy import supaya tidak circular
def _get_bot_state():
    try:
        from main import bot_state
        return bot_state
    except:
        return {}


def send(chat_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=5
        )
    except:
        pass


def handle_command(chat_id, txt):
    state = _get_bot_state()

    if txt == "/start":
        send(chat_id,
             "🤖 <b>SNAP Bot</b>\n"
             "Trading bot aktif di Polymarket.\n\n"
             "Commands:\n"
             "/status — status bot\n"
             "/balance — cek balance\n"
             "/positions — posisi terbuka\n"
             "/help — bantuan")

    elif txt == "/status":
        status      = state.get('status', 'unknown')
        mode        = state.get('mode', '?')
        last_cycle  = state.get('last_cycle', 'belum ada')
        trades      = state.get('total_trades', 0)
        winrate     = state.get('winrate', 0.0)

        emoji = "✅" if status == "running" else "🔴"
        send(chat_id,
             f"{emoji} <b>Status Bot</b>\n"
             f"Status:      {status}\n"
             f"Mode:        {mode}\n"
             f"Last cycle:  {last_cycle}\n"
             f"Total trades:{trades}\n"
             f"Winrate:     {winrate}%")

    elif txt == "/balance":
        balance  = state.get('balance', 0.0)
        pnl      = state.get('total_pnl', 0.0)
        pnl_pct  = (pnl / 20.0 * 100) if pnl else 0.0
        pnl_sign = "+" if pnl >= 0 else ""

        send(chat_id,
             f"💰 <b>Balance</b>\n"
             f"Balance: ${balance:.4f}\n"
             f"PnL:     {pnl_sign}${pnl:.4f} ({pnl_sign}{pnl_pct:.2f}%)")

    elif txt == "/positions":
        open_pos = state.get('open_positions', 0)
        if open_pos == 0:
            send(chat_id, "📭 Tidak ada posisi terbuka saat ini.")
        else:
            send(chat_id, f"📊 <b>Open Positions: {open_pos}</b>\n"
                          f"Cek Railway logs untuk detail.")

    elif txt == "/help":
        send(chat_id,
             "📖 <b>SNAP Bot Commands</b>\n\n"
             "/start    — mulai\n"
             "/status   — cek status bot\n"
             "/balance  — cek balance & PnL\n"
             "/positions— posisi terbuka\n"
             "/help     — bantuan ini")

    else:
        send(chat_id, f"❓ Command tidak dikenal: {txt}\nKirim /help untuk daftar command.")


def loop():
    global last_id
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            r   = requests.get(url,
                               params={"offset": last_id + 1, "timeout": 10},
                               timeout=15)
            for upd in r.json().get("result", []):
                last_id = upd["update_id"]
                msg     = upd.get("message")
                if msg and "text" in msg:
                    chat = msg["chat"]["id"]
                    txt  = msg["text"].lower().strip()
                    handle_command(chat, txt)
        except:
            pass
        time.sleep(2)


def start():
    threading.Thread(target=loop, daemon=True).start()
    print("✅ Telegram cmd handler started")