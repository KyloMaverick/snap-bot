"""
CRYPTO PRICE FETCHER - With Real Data & Probability Calculation
Ambil harga BTC/ETH dari CoinGecko API (gratis, no API key)
"""

import requests
import re
from typing import Optional

class CryptoPriceFetcher:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache = {}
        # Fallback prices (akan diupdate setiap kali fetch berhasil)
        self.btc_price = 65000
        self.eth_price = 3200
    
    def get_btc_price(self) -> Optional[float]:
        """Ambil harga BTC dalam USD"""
        try:
            url = f"{self.base_url}/simple/price"
            params = {"ids": "bitcoin", "vs_currencies": "usd"}
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.btc_price = data.get('bitcoin', {}).get('usd', self.btc_price)
            return self.btc_price
        except Exception as e:
            print(f"⚠️ Error fetching BTC price: {e}, using fallback ${self.btc_price}")
            return self.btc_price
    
    def get_eth_price(self) -> Optional[float]:
        """Ambil harga ETH dalam USD"""
        try:
            url = f"{self.base_url}/simple/price"
            params = {"ids": "ethereum", "vs_currencies": "usd"}
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.eth_price = data.get('ethereum', {}).get('usd', self.eth_price)
            return self.eth_price
        except Exception as e:
            print(f"⚠️ Error fetching ETH price: {e}, using fallback ${self.eth_price}")
            return self.eth_price
    
    def get_probability_from_price(self, market_question: str, current_price: float) -> float:
        """
        Konversi harga crypto ke probabilitas untuk Polymarket
        
        Args:
            market_question: Contoh "BTC > $70k?" atau "Will bitcoin hit $100k?"
            current_price: Harga market saat ini dari Polymarket (fallback)
        
        Returns:
            Probabilitas (0.00 - 1.00)
        """
        # Extract target price dari question
        question_lower = market_question.lower()
        
        # Pattern untuk mencari angka dengan suffix k/m
        patterns = [
            r'[\$]?(\d+(?:[.,]\d+)?)\s*([kKmM])',  # $70k, 70k, $70K
            r'[\$]?(\d+(?:[.,]\d+)?)\s*(?:thousand|million|billion)',  # 70 thousand
            r'[\$]?(\d+(?:[.,]\d+)?)',  # just numbers
        ]
        
        target = None
        suffix = None
        
        for pattern in patterns:
            match = re.search(pattern, question_lower)
            if match:
                target_str = match.group(1).replace(',', '')
                try:
                    target = float(target_str)
                    if len(match.groups()) > 1 and match.group(2):
                        suffix = match.group(2).lower()
                    break
                except:
                    continue
        
        if target is None:
            print(f"   [DEBUG] No target price found in: {market_question[:50]}")
            return current_price
        
        # Handle suffix (k = ribu, m = juta, b = miliar)
        if suffix in ['k', 'thousand']:
            target = target * 1000
        elif suffix in ['m', 'million']:
            target = target * 1000000
        elif suffix in ['b', 'billion']:
            target = target * 1000000000
        
        # Tentukan coin (BTC atau ETH)
        if 'btc' in question_lower or 'bitcoin' in question_lower:
            current_coin_price = self.get_btc_price()
            coin_name = "BTC"
        elif 'eth' in question_lower or 'ethereum' in question_lower:
            current_coin_price = self.get_eth_price()
            coin_name = "ETH"
        else:
            return current_price
        
        if not current_coin_price:
            print(f"   [DEBUG] No {coin_name} price available, using fallback")
            return current_price
        
        print(f"   [DEBUG] {coin_name} price: ${current_coin_price:,.0f}, Target: ${target:,.0f}")
        
        # Hitung probabilitas berdasarkan hubungan > atau <
        if '>' in question_lower or 'higher' in question_lower or 'above' in question_lower:
            # Market: coin > target
            if current_coin_price >= target:
                prob = 0.95  # Sudah di atas target, sangat mungkin
            else:
                # Hitung rasio jarak ke target
                ratio = current_coin_price / target
                # Sigmoid function: prob = 1 / (1 + e^(-k*(ratio - 0.5)))
                # Semakin tinggi ratio, semakin tinggi prob
                k = 12  # steepness factor
                prob = 1 / (1 + 2.718 ** (-k * (ratio - 0.5)))
                prob = max(0.05, min(0.95, prob))
        
        elif '<' in question_lower or 'lower' in question_lower or 'below' in question_lower:
            # Market: coin < target (coin harus di BAWAH target)
            if current_coin_price <= target:
                prob = 0.95  # Sudah di bawah target, sangat mungkin
            else:
                # Coin di ATAS target, harus turun dulu
                ratio = target / current_coin_price
                # Semakin kecil ratio, semakin kecil probabilitas
                # Jika ratio = 0.5 (target setengah dari harga saat ini), prob kecil
                prob = ratio ** 2
                prob = max(0.01, min(0.95, prob))
        
        else:
            # Default: semakin dekat ke target, semakin tinggi prob
            ratio = current_coin_price / target
            if ratio >= 1:
                prob = 0.9
            else:
                prob = ratio ** 2
                prob = max(0.05, min(0.95, prob))
        
        print(f"   [DEBUG] Calculated probability: {prob:.1%}")
        return round(prob, 3)


# Instance global
crypto_fetcher = CryptoPriceFetcher()


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Crypto Price Fetcher")
    print("=" * 50)
    
    print(f"\nBTC Price: ${crypto_fetcher.get_btc_price():,.0f}")
    print(f"ETH Price: ${crypto_fetcher.get_eth_price():,.0f}")
    
    test_cases = [
        "BTC > $70k?",
        "Bitcoin to reach $100k?",
        "BTC below $50k?",
        "Will ethereum hit $4000?",
        "ETH > $3500?",
        "BTC < $60k?"
    ]
    
    print("\nProbability calculations:")
    for test in test_cases:
        prob = crypto_fetcher.get_probability_from_price(test, 0.5)
        print(f"   {test:35} → {prob:.1%}")
    
    print("\n" + "=" * 50)