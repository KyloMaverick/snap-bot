"""
STAGE 2: EDGE CHECK
FIX 3: Edge detection untuk semua kategori market, bukan cuma crypto
FIX 6: Filter edge negatif ekstrim (false signal)
"""
from typing import Dict, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.crypto_price import crypto_fetcher


def _mean_reversion(price: float, strength: float = 0.5) -> float:
    return price + (0.5 - price) * strength


def get_estimated_probability(market: Dict) -> float:
    question      = market.get('question', '').lower()
    current_price = market.get('price', 0.5)

    print(f"   [DEBUG] Estimating: {question[:50]}...")

    # === CRYPTO ===
    if any(kw in question for kw in ['btc', 'bitcoin']):
        print(f"   [DEBUG] Category: crypto (BTC)")
        prob = crypto_fetcher.get_probability_from_price(question, current_price)
        return prob if prob else current_price

    if any(kw in question.split() for kw in ['eth', 'ethereum']):
        print(f"   [DEBUG] Category: crypto (ETH)")
        prob = crypto_fetcher.get_probability_from_price(question, current_price)
        return prob if prob else current_price

    # === POLITICS ===
    if any(kw in question for kw in ['trump', 'republican']):
        print(f"   [DEBUG] Category: politics (right)")
        return current_price * 0.97

    if any(kw in question for kw in ['democrat', 'biden', 'harris', 'kamala']):
        print(f"   [DEBUG] Category: politics (left)")
        return current_price * 1.02

    if any(kw in question for kw in ['election', 'vote', 'president', 'senate',
                                      'congress', 'poll', 'approve']):
        print(f"   [DEBUG] Category: politics (general)")
        return _mean_reversion(current_price, strength=0.35)

    # === SPORTS ===
    if any(kw in question for kw in ['win', 'beat', 'champion', 'title',
                                      'nba', 'nfl', 'nhl', 'mlb', 'ufc', 'mma',
                                      'soccer', 'football', 'basketball', 'tennis',
                                      'league', 'playoff', 'tournament', 'superbowl',
                                      'world cup', 'final']):
        print(f"   [DEBUG] Category: sports")
        return _mean_reversion(current_price, strength=0.25)

    # === ENTERTAINMENT / CULTURE ===
    if any(kw in question for kw in ['release', 'album', 'movie', 'film', 'song',
                                      'award', 'oscar', 'grammy', 'emmy', 'gta',
                                      'rihanna', 'taylor', 'beyonce', 'kanye',
                                      'netflix', 'box office', 'season']):
        print(f"   [DEBUG] Category: entertainment")
        return _mean_reversion(current_price, strength=0.45)

    # === CRYPTO (non-BTC/ETH) ===
    if any(kw in question for kw in ['crypto', 'solana', 'sol', 'bnb', 'xrp',
                                      'doge', 'coin', 'token', 'defi', 'nft',
                                      'blockchain', 'web3']):
        print(f"   [DEBUG] Category: crypto (alt)")
        return _mean_reversion(current_price, strength=0.55)

    # === GEOPOLITICS ===
    if any(kw in question for kw in ['war', 'invasion', 'nato', 'china', 'russia',
                                      'taiwan', 'sanction', 'nuclear', 'ceasefire',
                                      'peace', 'treaty']):
        print(f"   [DEBUG] Category: geopolitics")
        return _mean_reversion(current_price, strength=0.40)

    # === ECONOMICS / FINANCE ===
    if any(kw in question for kw in ['fed', 'rate', 'inflation', 'gdp', 'recession',
                                      'unemployment', 'cpi', 'interest', 'federal reserve',
                                      'stock', 'market', 'nasdaq', 's&p']):
        print(f"   [DEBUG] Category: economics")
        return _mean_reversion(current_price, strength=0.30)

    # === DEFAULT ===
    print(f"   [DEBUG] Category: default (mean reversion 0.40)")
    return _mean_reversion(current_price, strength=0.40)


def calculate_edge(market_price: float, estimated_prob: float) -> float:
    return (estimated_prob - market_price) * 100


def edge_check(market: Dict, threshold: float = 3.0) -> Tuple[bool, str, float, str, Dict]:
    """Stage 2: Cek edge."""

    market_price   = market.get('price', 0.5)
    estimated_prob = get_estimated_probability(market)
    edge           = calculate_edge(market_price, estimated_prob)
    edge_abs       = abs(edge)

    print(f"   [DEBUG] price={market_price:.3f}, estimated={estimated_prob:.3f}, "
          f"edge={edge:+.2f}%")

    edge_data = {
        'market_price':   market_price,
        'estimated_prob': estimated_prob,
        'edge':           edge,
        'edge_abs':       edge_abs,
        'threshold_used': threshold,
    }

    # FIX 6: Tolak edge negatif ekstrim — hampir pasti false signal
    if edge < -20:
        return (False,
                f"❌ Edge negatif ekstrim: {edge:.2f}% (false signal)",
                edge, None, edge_data)

    # Tolak edge terlalu kecil
    if edge_abs < threshold - 0.001:
        return (False,
                f"❌ Edge too small: {edge_abs:.2f}% (need {threshold}%)",
                edge, None, edge_data)

    side      = "BUY" if edge > 0 else "SELL"
    direction = "YES" if edge > 0 else "NO"
    reason    = (f"✅ Edge: {edge:+.2f}% "
                 f"(market={market_price:.3f}, real={estimated_prob:.3f}) "
                 f"→ {side} {direction}")

    return True, reason, edge, side, edge_data


# ============ TEST ============
if __name__ == "__main__":
    tests = [
        {'question': 'BTC > $70k by end of month?',        'price': 0.42},
        {'question': 'Trump wins 2026 election?',           'price': 0.60},
        {'question': 'Chiefs win the Super Bowl?',          'price': 0.25},
        {'question': 'GTA 6 releases before July 2025?',   'price': 0.70},
        {'question': 'Fed cuts rates in September?',        'price': 0.35},
        {'question': 'Will Russia invade another country?', 'price': 0.20},
        {'question': 'Will bitcoin hit $1m before GTA VI?','price': 0.49},
    ]

    print("=" * 60)
    print("Testing Edge Check - All Categories")
    print("=" * 60)

    for t in tests:
        passed, reason, edge, side, data = edge_check(t, threshold=3.0)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status} | {t['question'][:45]}")
        print(f"       edge={edge:+.2f}% | side={side}")