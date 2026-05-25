"""
Polymarket API Wrapper - Version 2 (Fixed JSON Parsing)
"""

import requests
import time
import json
from typing import Dict, List, Optional

class PolymarketAPI:
    def __init__(self):
        self.gamma_url = "https://gamma-api.polymarket.com"
        self.clob_url = "https://clob.polymarket.com"
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_interval = 2
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9"
        })
    
    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()
    
    def get_markets(self, limit: int = 10) -> List[Dict]:
        """Ambil daftar market dari Polymarket"""
        self._rate_limit()
        
        url = f"{self.gamma_url}/markets"
        params = {"limit": limit, "active": True}
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            # Parse JSON langsung
            markets = response.json()
            
            formatted = []
            for m in markets:
                # Parse outcomePrices yang berupa string JSON
                outcome_prices = m.get('outcomePrices', '["0.5", "0.5"]')
                if isinstance(outcome_prices, str):
                    outcome_prices = json.loads(outcome_prices)
                
                # Ambil clobTokenIds
                clob_ids = m.get('clobTokenIds', '[]')
                if isinstance(clob_ids, str):
                    clob_ids = json.loads(clob_ids)
                
                formatted.append({
                    'id': m.get('id'),
                    'question': m.get('question'),
                    'category': m.get('category', 'unknown'),
                    'volume': float(m.get('volume', 0)),
                    'price': float(outcome_prices[0]) if outcome_prices else 0.5,
                    'best_bid': float(m.get('bestBid', 0)),
                    'best_ask': float(m.get('bestAsk', 0)),
                    'clob_token_id': clob_ids[0] if clob_ids else None,
                    'end_date': m.get('endDate'),
                    'active': m.get('active', True)
                })
            return formatted
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def get_market_price(self, clob_token_id: str) -> Optional[float]:
        """Ambil harga dari CLOB"""
        self._rate_limit()
        
        url = f"{self.clob_url}/price"
        params = {"token_id": clob_token_id}
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data.get('price', 0.5))
        except:
            return None


# ============ TEST ============
if __name__ == "__main__":
    print("=" * 60)
    print("TESTING POLYMARKET API WRAPPER v2")
    print("=" * 60)
    
    api = PolymarketAPI()
    
    print("\n📡 Fetching markets...")
    markets = api.get_markets(limit=5)
    
    print(f"✅ Found {len(markets)} markets\n")
    
    for i, m in enumerate(markets[:3]):
        print(f"Market {i+1}:")
        print(f"   Question: {m['question'][:60]}...")
        print(f"   Category: {m['category']}")
        print(f"   Price: {m['price']:.3f} ({m['price']*100:.1f}%)")
        print(f"   Volume: ${m['volume']:,.0f}")
        print(f"   Best Bid: {m['best_bid']:.3f}")
        print(f"   Best Ask: {m['best_ask']:.3f}")
        print()
    
    print("=" * 60)
    print("✅ API Wrapper siap digunakan!")
    print("=" * 60)