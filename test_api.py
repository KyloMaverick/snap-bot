"""
Test koneksi ke Polymarket API dengan custom headers & IPv4
"""

import requests
import time
import socket

# === FORCE IPv4 (menghindari masalah IPv6) ===
old_getaddrinfo = socket.getaddrinfo
def force_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return old_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = force_ipv4

API_URL = "https://gamma-api.polymarket.com/markets"

# === Headers biar kaya browser ===
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

print("=" * 50)
print("TESTING POLYMARKET API CONNECTION (IPv4 + Headers)")
print("=" * 50)

def test_api_with_retry(max_retry=3):
    for attempt in range(1, max_retry + 1):
        print(f"\n🔄 Percobaan ke-{attempt}...")
        try:
            params = {"limit": 5, "active": True}
            # timeout (koneksi, baca data)
            response = requests.get(
                API_URL, 
                params=params, 
                headers=HEADERS,
                timeout=(10, 20)
            )
            response.raise_for_status()
            markets = response.json()
            
            print(f"✅ SUCCESS! (attempt {attempt})")
            print(f"   Found {len(markets)} active markets")
            if markets:
                print(f"   Example: {markets[0].get('question', 'N/A')[:60]}...")
            return True
            
        except requests.exceptions.Timeout:
            print(f"⚠️ Percobaan {attempt} timeout (server lambat atau koneksi ditolak)")
        except requests.exceptions.ConnectionError as e:
            print(f"⚠️ Percobaan {attempt} connection error: {e}")
        except Exception as e:
            print(f"❌ Percobaan {attempt} error: {e}")
        
        if attempt < max_retry:
            print(f"   Menunggu 5 detik sebelum mencoba lagi...")
            time.sleep(5)
    
    print("\n❌ Semua percobaan gagal")
    return False

# Jalankan test
success = test_api_with_retry(max_retry=3)

print("\n" + "=" * 50)
if success:
    print("✅ API Polymarket bisa diakses!")
    print("Bot siap mengambil data real")
else:
    print("⚠️ Gagal konek ke Polymarket API via script")
    print("Coba cek di browser: https://gamma-api.polymarket.com/markets")
    print("Kalau di browser bisa, mungkin ada pembatasan dari sisi server.")
print("=" * 50)