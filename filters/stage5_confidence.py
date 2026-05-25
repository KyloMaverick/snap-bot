"""
STAGE 5: CONFIDENCE SCORING
Hitung skor confidence untuk menentukan position size
"""

from typing import Dict, Tuple

def calculate_confidence_score(market: Dict, edge_data: Dict, liquidity_data: Dict) -> Tuple[int, str, float]:
    """
    Hitung confidence score (0-100) berdasarkan multiple faktor
    
    Komponen:
    - Edge (max 50 pts)
    - Volume (max 20 pts)
    - Spread (max 20 pts)
    - Category (max 10 pts)
    
    Returns:
        (score, level, position_size_pct)
    """
    
    score = 0
    
    # === 1. EDGE COMPONENT (max 50 pts) ===
    edge_abs = edge_data.get('edge_abs', 0)
    if edge_abs >= 8:
        score += 50
    elif edge_abs >= 6:
        score += 45
    elif edge_abs >= 5:
        score += 40
    elif edge_abs >= 4:
        score += 30
    elif edge_abs >= 3:
        score += 20
    elif edge_abs >= 2:
        score += 10
    else:
        score += 5
    
    # === 2. VOLUME COMPONENT (max 20 pts) ===
    volume = market.get('volume', 0)
    if volume >= 1000000:  # > $1M
        score += 20
    elif volume >= 500000:  # > $500k
        score += 15
    elif volume >= 100000:  # > $100k
        score += 10
    elif volume >= 50000:   # > $50k
        score += 5
    else:
        score += 0
    
    # === 3. SPREAD COMPONENT (max 20 pts) ===
    spread = liquidity_data.get('spread_pct', 5)
    if spread <= 0.5:
        score += 20
    elif spread <= 1.0:
        score += 15
    elif spread <= 1.5:
        score += 10
    elif spread <= 2.0:
        score += 5
    elif spread <= 3.0:
        score += 2
    else:
        score += 0
    
    # === 4. CATEGORY COMPONENT (max 10 pts) ===
    category = market.get('category', 'unknown')
    question = market.get('question', '').lower()
    
    # Crypto markets (lebih volatile, lebih banyak edge)
    if 'btc' in question or 'bitcoin' in question or 'eth' in question:
        score += 10
    # Entertainment/Sports
    elif 'rihanna' in question or 'playboi' in question or 'gta' in question:
        score += 8
    # Politics
    elif 'trump' in question or 'election' in question:
        score += 5
    # Other
    else:
        score += 3
    
    # Clamp score ke range 0-100
    score = max(0, min(100, score))
    
    # === TENTUKAN LEVEL ===
    if score >= 70:
        level = "HIGH"
        position_size_pct = 0.25  # 25% dari balance
    elif score >= 50:
        level = "MEDIUM"
        position_size_pct = 0.15  # 15% dari balance
    else:
        level = "LOW"
        position_size_pct = 0.10  # 10% dari balance
    
    return score, level, position_size_pct


def confidence_check(market: Dict, edge_data: Dict, liquidity_data: Dict, mode: str = "SAFE") -> Tuple[bool, str, Dict]:
    """
    Stage 5: Final confidence check
    
    Args:
        market: data market
        edge_data: data dari stage 2
        liquidity_data: data dari stage 3
        mode: "SAFE" atau "AGGRESSIVE"
    
    Returns:
        (is_passed, reason, confidence_data)
    """
    
    score, level, position_size_pct = calculate_confidence_score(market, edge_data, liquidity_data)
    
    confidence_data = {
        'score': score,
        'level': level,
        'position_size_pct': position_size_pct,
        'edge_abs': edge_data.get('edge_abs', 0),
        'spread': liquidity_data.get('spread_pct', 0),
        'volume': market.get('volume', 0)
    }
    
    # Di SAFE mode, LOW confidence ditolak
    if mode == "SAFE" and level == "LOW":
        return False, f"❌ Confidence LOW ({score}) → SKIP in SAFE mode", confidence_data
    
    # Di AGGRESSIVE mode, semua level diterima
    reason = f"✅ Confidence {level} ({score}) → position size {position_size_pct*100:.0f}%"
    
    return True, reason, confidence_data