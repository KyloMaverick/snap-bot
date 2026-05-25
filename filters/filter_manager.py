"""
FILTER MANAGER
Menjalankan semua 5 stage filtering secara berurutan
"""

from typing import Dict, List, Tuple
from .stage1_prefilter import prefilter
from .stage2_edge import edge_check
from .stage3_liquidity import liquidity_check
from .stage4_risk import risk_check_static, get_risk_checker
from .stage5_confidence import confidence_check


class FilterManager:
    def __init__(self, mode: str = "SAFE"):
        """
        Args:
            mode: "SAFE" atau "AGGRESSIVE"
        """
        self.mode = mode
        self.threshold = 4.0 if mode == "SAFE" else 3.0  # edge threshold
        self.passed_markets = []
        self.rejected_markets = []
    
    def set_mode(self, mode: str):
        """Ubah mode trading"""
        self.mode = mode
        self.threshold = 4.0 if mode == "SAFE" else 3.0
        print(f"📊 Filter Manager mode changed to: {mode} (threshold={self.threshold}%)")
    
    def process_market(self, market: Dict) -> Tuple[bool, Dict]:
        """
        Proses satu market melalui semua 5 stage
        
        Returns:
            (is_eligible, result_data)
        """
        result = {
            'market': market,
            'stage1': {},
            'stage2': {},
            'stage3': {},
            'stage4': {},
            'stage5': {},
            'eligible': False,
            'final_reason': '',
            'position_size': 0,
            'side': None
        }
        
        # === STAGE 1: PRE-FILTER ===
        passed, reason, filtered_data = prefilter(market)
        result['stage1'] = {'passed': passed, 'reason': reason}
        
        if not passed:
            result['final_reason'] = f"Stage 1 failed: {reason}"
            self.rejected_markets.append(result)
            return False, result
        
        # === STAGE 2: EDGE CHECK ===
        passed, reason, edge, side, edge_data = edge_check(filtered_data, self.threshold)
        result['stage2'] = {'passed': passed, 'reason': reason, 'edge': edge, 'side': side}
        
        if not passed:
            result['final_reason'] = f"Stage 2 failed: {reason}"
            self.rejected_markets.append(result)
            return False, result
        
        # === STAGE 3: LIQUIDITY CHECK ===
        position_size_estimate = 10.0  # default kecil
        passed, reason, liquidity_data = liquidity_check(filtered_data, position_size_estimate)
        result['stage3'] = {'passed': passed, 'reason': reason, 'liquidity_data': liquidity_data}
        
        if not passed:
            result['final_reason'] = f"Stage 3 failed: {reason}"
            self.rejected_markets.append(result)
            return False, result
        
        # === STAGE 4: RISK CHECK ===
        passed, reason = risk_check_static(filtered_data)
        result['stage4'] = {'passed': passed, 'reason': reason}
        
        if not passed:
            result['final_reason'] = f"Stage 4 failed: {reason}"
            self.rejected_markets.append(result)
            return False, result
        
        # === STAGE 5: CONFIDENCE CHECK ===
        passed, reason, confidence_data = confidence_check(filtered_data, edge_data, liquidity_data, self.mode)
        result['stage5'] = {'passed': passed, 'reason': reason, 'confidence_data': confidence_data}
        
        if not passed:
            result['final_reason'] = f"Stage 5 failed: {reason}"
            self.rejected_markets.append(result)
            return False, result
        
        # === SEMUA STAGE LOLOS ===
        position_size_pct = confidence_data.get('position_size_pct', 0.15)
        result['eligible'] = True
        result['final_reason'] = f"✅ ALL STAGES PASSED! Confidence: {confidence_data['level']} ({confidence_data['score']})"
        result['position_size_pct'] = position_size_pct
        result['side'] = side
        
        self.passed_markets.append(result)
        return True, result
    
    def process_markets(self, markets: List[Dict]) -> List[Dict]:
        """Proses multiple markets"""
        results = []
        for market in markets:
            eligible, result = self.process_market(market)
            results.append(result)
        
        # Print summary
        passed_count = len([r for r in results if r['eligible']])
        print(f"\n{'='*60}")
        print(f"FILTERING SUMMARY")
        print(f"   Total markets: {len(markets)}")
        print(f"   Passed: {passed_count}")
        print(f"   Rejected: {len(markets) - passed_count}")
        print(f"   Mode: {self.mode} (threshold={self.threshold}%)")
        print(f"{'='*60}")
        
        return results
    
    def reset(self):
        """Reset daftar passed dan rejected markets"""
        self.passed_markets = []
        self.rejected_markets = []
    
    def get_passed_markets(self) -> List[Dict]:
        """Dapatkan daftar market yang lolos"""
        return self.passed_markets
    
    def get_top_signals(self, limit: int = 3) -> List[Dict]:
        """Dapatkan signal terbaik berdasarkan confidence score"""
        sorted_markets = sorted(
            self.passed_markets, 
            key=lambda x: x.get('stage5', {}).get('confidence_data', {}).get('score', 0),
            reverse=True
        )
        return sorted_markets[:limit]


# ============ TEST ============
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from data.polymarket_api import PolymarketAPI
    
    print("=" * 60)
    print("TESTING FILTER MANAGER")
    print("=" * 60)
    
    # Ambil data real dari Polymarket
    api = PolymarketAPI()
    markets = api.get_markets(limit=10)
    
    if not markets:
        print("⚠️ No markets fetched. Using mock data...")
        # Mock data jika API gagal
        markets = [
            {'id': '1', 'question': 'BTC > $70k?', 'category': 'crypto', 'volume': 500000, 'price': 0.42, 'best_bid': 0.41, 'best_ask': 0.43, 'active': True},
            {'id': '2', 'question': 'ETH > $4k?', 'category': 'crypto', 'volume': 300000, 'price': 0.38, 'best_bid': 0.37, 'best_ask': 0.39, 'active': True},
        ]
    
    # Jalankan filter
    filter_manager = FilterManager(mode="SAFE")
    results = filter_manager.process_markets(markets)
    
    # Tampilkan hasil
    print("\n" + "=" * 60)
    print("DETAILED RESULTS")
    print("=" * 60)
    
    for result in results:
        if result['eligible']:
            market = result['market']
            print(f"\n🎯 SIGNAL: {market.get('question', 'Unknown')[:50]}...")
            print(f"   Stage 1: {result['stage1']['reason']}")
            print(f"   Stage 2: {result['stage2']['reason']}")
            print(f"   Stage 3: {result['stage3']['reason']}")
            print(f"   Stage 4: {result['stage4']['reason']}")
            print(f"   Stage 5: {result['stage5']['reason']}")
            print(f"   📊 VERDICT: ELIGIBLE - {result['final_reason']}")
            print(f"   💰 Position Size: {result['position_size_pct']*100:.0f}%")
            print(f"   🔄 Side: {result['side']}")
        else:
            if result.get('stage1', {}).get('passed', False) == False:
                # Skip print untuk yang gagal di stage 1 (terlalu banyak)
                pass
            else:
                market = result['market']
                print(f"\n❌ REJECTED: {market.get('question', 'Unknown')[:40]}...")
                print(f"   Reason: {result['final_reason']}")
    
    # Tampilkan top signals
    top_signals = filter_manager.get_top_signals(limit=3)
    if top_signals:
        print("\n" + "=" * 60)
        print("🏆 TOP 3 SIGNALS")
        print("=" * 60)
        for i, signal in enumerate(top_signals, 1):
            market = signal['market']
            conf_data = signal.get('stage5', {}).get('confidence_data', {})
            print(f"{i}. {market.get('question', 'Unknown')[:50]}...")
            print(f"   Confidence: {conf_data.get('level', 'N/A')} ({conf_data.get('score', 0)})")
            print(f"   Side: {signal.get('side', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ FILTER MANAGER TEST COMPLETE")
    print("=" * 60)