"""
Worker untuk Railway - Bot jalan otomatis tanpa input
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import SnapBot

print("=" * 60)
print("🤖 SNAP BOT - RAILWAY WORKER MODE")
print("=" * 60)
print("Mode: SAFE (4% threshold)")
print("Paper Mode: ON")
print("=" * 60)

# Jalankan bot langsung dengan mode SAFE
bot = SnapBot(mode="SAFE", paper_mode=True)

# Loop infinite
while True:
    try:
        bot.scan_and_trade()
        print("⏳ Waiting 30 seconds...")
        time.sleep(30)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")
        break
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(30)
