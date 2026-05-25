"""
SNAP BOT - RAILWAY WORKER (FIXED)
Bot jalan 24/7 tanpa input, auto restart jika error
"""

import time
import sys
import os

import simple_cmd_bot

# Tambahkan path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Hapus database lama biar fresh (opsional, komentar kalau gak mau)
if os.path.exists("snap_bot_data.db"):
    os.remove("snap_bot_data.db")
    print("✅ Database reset")

from main import SnapBot

print("=" * 60)
print("🤖 SNAP BOT - RAILWAY WORKER MODE")
print("=" * 60)
print("Mode: SAFE (4% threshold)")
print("Paper Mode: ON")
print("Bot akan jalan terus 24/7")
print("=" * 60)

# Inisialisasi bot SEKALI di luar loop
bot = SnapBot(mode="SAFE", paper_mode=True)

# Loop infinity — bot jalan terus
while True:
    try:
        bot.scan_and_trade()
        print("⏳ Waiting 30 seconds...\n")
        time.sleep(30)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔄 Restarting in 10 seconds...\n")
        time.sleep(10)

from monitoring.telegram_bot import SimpleTelegramBot

# ... setelah bot = SnapBot(...)
tg_bot = SimpleTelegramBot(telegram.bot_token, bot)
import threading
threading.Thread(target=tg_bot.run, daemon=True).start()
