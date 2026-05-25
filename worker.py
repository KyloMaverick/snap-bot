"""
Worker untuk Railway - Bot jalan terus 24/7
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

bot = SnapBot(mode="SAFE", paper_mode=True)

# Jalankan loop forever
while True:
    try:
        print("\n[INFO] Starting scan cycle...")
        bot.scan_and_trade()
        print("[INFO] Cycle complete. Waiting 30 seconds...")
        time.sleep(30)
    except Exception as e:
        print(f"[ERROR] {e}")
        print("[INFO] Restarting in 10 seconds...")
        time.sleep(10)
