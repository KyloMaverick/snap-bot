"""
TEST FILTER MANAGER
Menjalankan semua stage filtering dengan data real/mock
"""

import sys
import os

# Tambahkan path project ke sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.polymarket_api import PolymarketAPI
from filters.stage1_prefilter import prefilter
from filters.stage2_edge import edge_check
from filters.stage3_liquidity import liquidity_check
from filters.stage4_risk import risk_check_static, get_risk_checker
from filters.stage5_confidence import confidence_check


def test_single_market(market, mode="SAFE"):
    """Test semua stage untuk satu market"""
    
    print(f"\n{'='*60}")
    print(f"TESTING MARKET: {market.get('question', 'Unknown')[:60]}")
    print(f"{'='*60}")
    
    # Reset risk checker
    risk_checker = get_risk_checker()
    risk_checker.daily_pnl = 0.0
    risk_checker.consecutive_losses = 0
    risk_checker.open_positions = []
    
    threshold = 4.0 if mode == "SAFE" else 3.0
    
    # === STAGE 1: PRE-FILTER ===
    passed, reason, filtered_data = prefilter(market)
    print(f"\n📌 STAGE 1 (Pre-filter):")
    print(f"   Result: {'✅ PASS' if passed else '❌ FAIL'}")
    print(f"   Reason: {reason}")
    
    if not passed:
        print(f"\n❌ Market REJECTED at Stage 1")
        return False
    
    # === STAGE 2: EDGE CHECK ===
    passed, reason, edge, side, edge_data = edge_check(filtered_data, threshold)
    print(f"\n📌 STAGE 2 (Edge Check):")
    print(f"   Result: {'✅ PASS' if passed else '❌ FAIL'}")
    print(f"   Reason: {reason}")
    if edge_data:
        print(f"   Edge: {edge_data.get('edge', 0):+.2f}%")
        print(f"   Side: {side}")
    
    if not passed:
        print(f"\n❌ Market REJECTED at Stage 2")
        return False
    
    # === STAGE 3: LIQUIDITY CHECK ===
    passed, reason, liquidity_data = liquidity_check(filtered_data, position_size=10.0)
    print(f"\n📌 STAGE 3 (Liquidity Check):")
    print(f"   Result: {'✅ PASS' if passed else '❌ FAIL'}")
    print(f"   Reason: {reason}")
    if liquidity_data:
        print(f"   Spread: {liquidity_data.get('spread_pct', 0):.2f}%")
    
    if not passed:
        print(f"\n❌ Market REJECTED at Stage 3")
        return False
    
    # === STAGE 4: RISK CHECK ===
    passed, reason = risk_check_static(filtered_data)
    print(f"\n📌 STAGE 4 (Risk Check):")
    print(f"   Result: {'✅ PASS' if passed else '❌ FAIL'}")
    print(f"   Reason: {reason}")
    
    if not passed:
        print(f"\n❌ Market REJECTED at Stage 4")
        return False
    
    # === STAGE 5: CONFIDENCE CHECK ===
    passed, reason, confidence_data = confidence_check(filtered_data, edge_data, liquidity_data, mode)
    print(f"\n📌 STAGE 5 (Confidence Check):")
    print(f"   Result: {'✅ PASS' if passed else '❌ FAIL'}")
    print(f"   Reason: {reason}")
    if confidence_data:
        print(f"   Confidence Score: {confidence_data.get('score', 0)}")
        print(f"   Confidence Level: {confidence_data.get('level', 'N/A')}")
        print(f"   Position Size: {confidence_data.get('position_size_pct', 0)*100:.0f}%")
    
    if not passed:
        print(f"\n❌ Market REJECTED at Stage 5")
        return False
    
    # === ALL PASSED ===
    print(f"\n{'='*60}")
    print(f"🎯 VERDICT: ELIGIBLE FOR TRADE!")
    print(f"   Side: {side}")
    print(f"   Position Size: {confidence_data.get('position_size_pct', 0)*100:.0f}% of balance")
    print(f"   Confidence: {confidence_data.get('level', 'N/A')} ({confidence_data.get('score', 0)})")
    print(f"{'='*60}")
    
    return True


def main():
    print("=" * 60)
    print("FILTER MANAGER TEST")
    print("=" * 60)
    
    # Ambil data dari Polymarket API
    print("\n📡 Fetching markets from Polymarket...")
    api = PolymarketAPI()
    markets = api.get_markets(limit=10)
    
    if not markets:
        print("⚠️ API returned no data. Using MOCK data for testing...")
        # Mock data untuk testing
        markets = [
            {
                'id': '1',
                'question': 'BTC > $70k before April 30?',
                'category': 'crypto',
                'volume': 1500000,
                'price': 0.42,
                'best_bid': 0.41,
                'best_ask': 0.43,
                'active': True,
                'end_date': '2026-04-30T12:00:00Z'
            },
            {
                'id': '2',
                'question': 'ETH > $4k before April 30?',
                'category': 'crypto',
                'volume': 800000,
                'price': 0.38,
                'best_bid': 0.37,
                'best_ask': 0.39,
                'active': True,
                'end_date': '2026-04-30T12:00:00Z'
            },
            {
                'id': '3',
                'question': 'Will Rihanna release new album before GTA VI?',
                'category': 'entertainment',
                'volume': 750000,
                'price': 0.61,
                'best_bid': 0.60,
                'best_ask': 0.62,
                'active': True,
                'end_date': '2026-07-31T12:00:00Z'
            }
        ]
    
    print(f"✅ Got {len(markets)} markets\n")
    
    # Test dengan mode SAFE
    print("\n" + "🛡️" * 30)
    print("TESTING WITH SAFE MODE (threshold 4%)")
    print("🛡️" * 30)
    
    eligible_count = 0
    for market in markets:
        if test_single_market(market, mode="SAFE"):
            eligible_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"   Total markets tested: {len(markets)}")
    print(f"   Eligible for trade: {eligible_count}")
    print(f"   Rejected: {len(markets) - eligible_count}")
    print("=" * 60)
    
    print("\n✅ Filter Manager test complete!")


if __name__ == "__main__":
    main()