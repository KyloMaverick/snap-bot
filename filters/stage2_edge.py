"""
STAGE 2: EDGE CHECK (Dengan Data Real)
"""

from typing import Dict, Tuple
import sys
import os
import re

# Tambahkan path untuk import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.crypto_price import crypto_fetcher


def get_estimated_probability(market: Dict) -> float:
    """
    Dapatkan estimasi probabilitas real dari berbagai sumber
    """
    question = market.get('question', '').lower()
    current_price = market.get('price', 0.5)
    
    print(f"   [DEBUG] Estimating probability for: {question[:50]}...")
    
    # === CRYPTO MARKETS ===
    if 'btc' in question or 'bitcoin' in question:
        print(f"   [DEBUG] Crypto market detected (BTC)")
        prob = crypto_fetcher.get_probability_from_price(question, current_price)
        print(f"   [DEBUG] Crypto probability: {prob}")
        if prob:
            return prob
        return current_price
    
    elif 'eth' in question or 'ethereum' in question:
        print(f"   [DEBUG] Crypto market detected (ETH)")
        prob = crypto_fetcher.get_probability_from_price(question, current_price)
        if prob:
            return prob
        return current_price
    
    # === POLITICS MARKETS ===
    elif 'trump' in question:
        return current_price - 0.03
    elif 'biden' in question or 'harris' in question:
        return current_price + 0.02
    
    # === DEFAULT ===
    else:
        print(f"   [DEBUG] Using default probability: {current_price}")
        return current_price


def calculate_edge(market_price: float, estimated_prob: float) -> float:
    """Hitung edge dalam persen"""
    return (estimated_prob - market_price) * 100


def edge_check(market: Dict, threshold: float = 3.0) -> Tuple[bool, str, float, str, Dict]:
    """Stage 2: Cek edge"""
    
    market_price = market.get('price', 0.5)
    estimated_prob = get_estimated_probability(market)
    edge = calculate_edge(market_price, estimated_prob)
    edge_abs = abs(edge)
    
    print(f"   [DEBUG] market_price={market_price}, estimated={estimated_prob}, edge={edge:.2f}%")
    
    edge_data = {
        'market_price': market_price,
        'estimated_prob': estimated_prob,
        'edge': edge,
        'edge_abs': edge_abs,
        'threshold_used': threshold
    }
    
    # Tolerance untuk floating point
    if edge_abs < threshold - 0.001:
        return False, f"❌ Edge too small: {edge_abs:.2f}% (need {threshold}%)", edge, None, edge_data
    
    side = "BUY" if edge > 0 else "SELL"
    direction = "YES" if edge > 0 else "NO"
    reason = f"✅ Edge: {edge:+.2f}% (market={market_price:.3f}, real={estimated_prob:.3f}) → {side} {direction}"
    
    return True, reason, edge, side, edge_data


# Test langsung
if __name__ == "__main__":
    test_market = {
        'question': 'BTC > $70k?',
        'price': 0.42
    }
    
    print("=" * 50)
    print("Testing Edge Check dengan Crypto Real")
    print("=" * 50)
    
    passed, reason, edge, side, data = edge_check(test_market, threshold=3.0)
    print(f"\nResult: {'PASS' if passed else 'FAIL'}")
    print(f"Reason: {reason}")
    print(f"Edge: {edge:.2f}%")
    print(f"Side: {side}")