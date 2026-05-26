import cmd_handler
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import SnapBot

print("=" * 60)
print("🤖 SNAP BOT - RAILWAY WORKER")
print("=" * 60)

cmd_handler.start()

bot = SnapBot(mode="AGGRESSIVE", paper_mode=True)

while True:
    try:
        bot.scan_and_trade()
        print("⏳ Waiting 30 seconds...")
        time.sleep(30)
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(10)