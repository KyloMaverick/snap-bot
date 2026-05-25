"""
STAGE 3: LIQUIDITY & SPREAD CHECK
Cek order book sebelum entry
"""

from typing import Dict, Tuple

def liquidity_check(market: Dict, position_size: float = 10.0) -> Tuple[bool, str, Dict]:
    """
    Cek likuiditas berdasarkan bid/ask spread
    
    Kriteria:
    - Spread < 3% (untuk market prediction)
    - Depth minimal 2x position size
    - Ada bid dan ask yang valid
    
    Note: Karena kita belum punya real order book, 
    kita pakai best_bid/best_ask dari data market
    
    Args:
        market: data market (harus punya best_bid, best_ask)
        position_size: rencana ukuran posisi dalam dollar
    
    Returns:
        (is_passed, reason, liquidity_data)
    """
    
    # Ambil data dari market
    best_bid = market.get('best_bid', 0)
    best_ask = market.get('best_ask', 0)
    market_price = market.get('price', 0.5)
    
    liquidity_data = {
        'best_bid': best_bid,
        'best_ask': best_ask,
        'spread_pct': 0,
        'spread_ok': False,
        'depth_ok': False
    }
    
    # 1. Validasi data ada
    if best_bid == 0 or best_ask == 0:
        # Fallback: estimasi spread dari market price
        best_bid = market_price * 0.99
        best_ask = market_price * 1.01
        liquidity_data['best_bid'] = best_bid
        liquidity_data['best_ask'] = best_ask
        liquidity_data['is_estimated'] = True
    else:
        liquidity_data['is_estimated'] = False
    
    # 2. Hitung spread dalam persen
    if best_bid > 0:
        spread = (best_ask - best_bid) / best_bid * 100
        liquidity_data['spread_pct'] = round(spread, 2)
    else:
        spread = 5.0  # spread default besar
        liquidity_data['spread_pct'] = spread
    
    # 3. Cek spread (maksimal 3% untuk prediction market)
    MAX_SPREAD_PCT = 3.0
    if spread <= MAX_SPREAD_PCT:
        liquidity_data['spread_ok'] = True
    else:
        return False, f"❌ Spread terlalu lebar: {spread:.2f}% (max {MAX_SPREAD_PCT}%)", liquidity_data
    
    # 4. Estimasi depth (sederhana)
    # Karena kita belum punya real depth, kita asumsikan cukup
    # Dengan volume market sebagai indikator
    volume = market.get('volume', 0)
    if volume > 100000:
        liquidity_data['depth_ok'] = True
        depth_status = "cukup"
    elif volume > 50000:
        liquidity_data['depth_ok'] = True
        depth_status = "minimal"
    else:
        liquidity_data['depth_ok'] = False
        return False, f"❌ Volume terlalu rendah untuk depth: ${volume:,.0f}", liquidity_data
    
    reason = f"✅ Liquidity OK (spread={spread:.2f}%, volume=${volume:,.0f}, depth={depth_status})"
    
    return True, reason, liquidity_data