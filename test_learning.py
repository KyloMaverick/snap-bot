"""
TEST LEARNING LAYER
Menguji semua komponen learning: Database, Brier Score, Win Rate Analyzer, Adaptive Threshold, Kelly Optimizer
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from learning.database import LearningDB
from learning.brier_tracker import BrierTracker
from learning.winrate_analyzer import WinRateAnalyzer
from learning.threshold_tuner import AdaptiveThreshold
from learning.kelly_optimizer import KellyOptimizer


def main():
    print("=" * 60)
    print("🧠 LEARNING LAYER TEST")
    print("=" * 60)
    
    # Inisialisasi database
    print("\n📁 Initializing database...")
    db = LearningDB("test_learning.db")
    
    # Inisialisasi semua komponen
    brier = BrierTracker(db)
    winrate = WinRateAnalyzer(db)
    threshold_tuner = AdaptiveThreshold(db, brier, winrate)
    kelly = KellyOptimizer(db, winrate)
    
    print("✅ All components initialized\n")
    
    # 1. Test Brier Score (awalnya default)
    print("=" * 50)
    print("1. BRIER SCORE TRACKER")
    print("=" * 50)
    cal_status = brier.get_calibration_status()
    print(f"   Current Brier Score: {cal_status['brier_score']}")
    print(f"   Status: {cal_status['status']}")
    print(f"   Recommendation: {cal_status['recommendation']}")
    print(f"   Confidence Multiplier: {brier.get_confidence_multiplier()}")
    
    # 2. Test Win Rate Analyzer
    print("\n" + "=" * 50)
    print("2. WIN RATE ANALYZER")
    print("=" * 50)
    
    # Tambah sample trades untuk testing (simulasi)
    print("   Adding sample trades...")
    sample_trades = [
        {'market_id': '1', 'market_question': 'BTC > $70k?', 'category': 'crypto', 'side': 'BUY', 
         'entry_price': 0.42, 'exit_price': 0.46, 'predicted_prob': 0.58, 'actual_outcome': 1, 
         'pnl': 0.95, 'pnl_pct': 4.5, 'entry_hour': 14},
        {'market_id': '2', 'market_question': 'ETH > $4k?', 'category': 'crypto', 'side': 'BUY', 
         'entry_price': 0.38, 'exit_price': 0.40, 'predicted_prob': 0.52, 'actual_outcome': 1, 
         'pnl': 0.53, 'pnl_pct': 2.8, 'entry_hour': 10},
        {'market_id': '3', 'market_question': 'Trump wins?', 'category': 'politics', 'side': 'SELL', 
         'entry_price': 0.55, 'exit_price': 0.52, 'predicted_prob': 0.48, 'actual_outcome': 0, 
         'pnl': 0.55, 'pnl_pct': 2.5, 'entry_hour': 20},
        {'market_id': '4', 'market_question': 'Lakers win?', 'category': 'sports', 'side': 'BUY', 
         'entry_price': 0.60, 'exit_price': 0.58, 'predicted_prob': 0.55, 'actual_outcome': 0, 
         'pnl': -0.33, 'pnl_pct': -2.8, 'entry_hour': 19},
    ]
    
    for trade in sample_trades:
        db.save_trade(trade)
    
    # Tambah sample predictions
    db.save_prediction('1', 0.58, 1)
    db.save_prediction('2', 0.52, 1)
    db.save_prediction('3', 0.48, 0)
    db.save_prediction('4', 0.55, 0)
    
    # Tampilkan analisis
    winrate.print_summary()
    
    # 3. Test Adaptive Threshold
    print("\n" + "=" * 50)
    print("3. ADAPTIVE THRESHOLD")
    print("=" * 50)
    
    # Test dengan berbagai kondisi
    test_markets = [
        {'category': 'crypto', 'question': 'BTC > $70k?'},
        {'category': 'politics', 'question': 'Trump wins?'},
        {'category': 'sports', 'question': 'Lakers win?'},
        {'category': 'unknown', 'question': 'Random market?'},
    ]
    
    for market in test_markets:
        threshold = threshold_tuner.get_current_threshold(market, mode="SAFE")
        explanation = threshold_tuner.get_threshold_explanation(threshold, market)
        print(f"\n   Market: {market['category']}")
        print(f"   Threshold: {threshold}%")
        print(f"   {explanation}")
    
    threshold_tuner.print_status()
    
    # 4. Test Kelly Optimizer
    print("\n" + "=" * 50)
    print("4. KELLY OPTIMIZER (Position Sizing)")
    print("=" * 50)
    
    balance = 100.0
    test_configs = [
        ("HIGH", 85, "crypto", 14, "SAFE"),
        ("MEDIUM", 65, "politics", 20, "SAFE"),
        ("LOW", 45, "sports", 10, "SAFE"),
        ("HIGH", 90, "crypto", 14, "AGGRESSIVE"),
    ]
    
    for level, score, cat, hour, mode in test_configs:
        size = kelly.get_position_size(balance, level, score, cat, hour, mode)
        pct = size / balance * 100
        risk = kelly.get_risk_level(size, balance)
        print(f"\n   Confidence: {level} ({score}) | Mode: {mode} | Cat: {cat}")
        print(f"   Position Size: ${size:.2f} ({pct:.1f}%) | Risk: {risk}")
    
    max_size = kelly.get_max_position_size(balance, "crypto")
    print(f"\n   Max position size (crypto): ${max_size:.2f}")
    
    # 5. Test kombinasi dengan confidence score
    print("\n" + "=" * 50)
    print("5. INTEGRATION TEST")
    print("=" * 50)
    
    # Simulasi market yang layak trade
    test_market = {
        'id': 'test_1',
        'question': 'BTC > $70k before April?',
        'category': 'crypto',
        'price': 0.42,
        'volume': 1500000,
        'best_bid': 0.41,
        'best_ask': 0.43,
        'active': True
    }
    
    # Hitung threshold
    threshold = threshold_tuner.get_current_threshold(test_market, mode="SAFE")
    print(f"\n📊 Market: {test_market['question'][:40]}...")
    print(f"   Dynamic Threshold: {threshold}%")
    
    # Simulasi edge (misal estimated prob 0.48)
    edge = (0.48 - 0.42) * 100
    print(f"   Edge: {edge:.2f}%")
    
    if edge >= threshold:
        print("   ✅ Signal VALID - edge meets threshold")
        
        # Hitung position size
        size = kelly.get_position_size(balance, "HIGH", 85, "crypto", 14, "SAFE")
        print(f"   📈 RECOMMENDED TRADE:")
        print(f"      Side: BUY YES")
        print(f"      Size: ${size:.2f}")
        print(f"      Expected TP: +3%")
        print(f"      Stop Loss: -3%")
    else:
        print("   ❌ Signal INVALID - edge below threshold")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 LEARNING LAYER TEST SUMMARY")
    print("=" * 60)
    print(f"   Database: ✅ {db.db_path}")
    print(f"   Brier Score Tracker: ✅")
    print(f"   Win Rate Analyzer: ✅")
    print(f"   Adaptive Threshold: ✅")
    print(f"   Kelly Optimizer: ✅")
    print("\n🎉 LEARNING LAYER READY!")
    print("=" * 60)
    
    # Cleanup
    db.close()


if __name__ == "__main__":
    main()