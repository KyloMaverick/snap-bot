"""
WIN RATE ANALYZER
Menganalisis pattern kemenangan berdasarkan berbagai kondisi
"""

from typing import Dict, List, Optional
from .database import LearningDB


class WinRateAnalyzer:
    def __init__(self, db: LearningDB):
        self.db = db
    
    def get_best_categories(self, min_trades: int = 5) -> Dict:
        """Dapatkan kategori dengan win rate tertinggi"""
        winrates = self.db.get_winrate_by_category()
        
        # Filter minimal trades
        filtered = {}
        for cat, wr in winrates.items():
            # Ambil dari database langsung
            filtered[cat] = wr
        
        if not filtered:
            return {'default': 50}
        
        # Sort by winrate descending
        sorted_cats = sorted(filtered.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_cats)
    
    def get_best_hours(self, min_trades: int = 3) -> Dict:
        """Dapatkan jam dengan win rate tertinggi"""
        winrates = self.db.get_winrate_by_hour()
        
        if not winrates:
            return {12: 50}  # default noon
        
        sorted_hours = sorted(winrates.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_hours)
    
    def should_skip_category(self, category: str, threshold: float = 45.0) -> bool:
        """
        Apakah kategori ini harus di-skip?
        
        Args:
            category: Nama kategori
            threshold: Minimal win rate (%) untuk tetap trade
        """
        winrates = self.db.get_winrate_by_category()
        winrate = winrates.get(category, 50)
        
        if winrate < threshold:
            return True, f"Skip {category}: winrate {winrate}% < {threshold}%"
        return False, f"OK {category}: winrate {winrate}%"
    
    def get_optimal_threshold_for_category(self, category: str) -> float:
        """
        Dapatkan threshold optimal untuk kategori tertentu
        
        Kategori dengan win rate tinggi bisa pakai threshold lebih rendah
        """
        winrates = self.db.get_winrate_by_category()
        winrate = winrates.get(category, 50)
        
        if winrate >= 60:
            return 2.5  # agresif
        elif winrate >= 50:
            return 3.0  # normal
        elif winrate >= 40:
            return 4.0  # konservatif
        else:
            return 5.0  # sangat konservatif
    
    def get_position_size_multiplier(self, category: str, hour: int) -> float:
        """
        Dapatkan multiplier untuk position size berdasarkan kondisi
        
        Kategori dan jam yang profitable → size lebih besar
        """
        winrates_cat = self.db.get_winrate_by_category()
        winrates_hour = self.db.get_winrate_by_hour()
        
        cat_wr = winrates_cat.get(category, 50)
        hour_wr = winrates_hour.get(hour, 50)
        
        multiplier = 1.0
        
        # Bonus untuk kategori profitable
        if cat_wr >= 60:
            multiplier *= 1.2
        elif cat_wr <= 40:
            multiplier *= 0.8
        
        # Bonus untuk jam profitable
        if hour_wr >= 60:
            multiplier *= 1.15
        elif hour_wr <= 40:
            multiplier *= 0.85
        
        return round(multiplier, 2)
    
    def get_summary(self) -> Dict:
        """Dapatkan ringkasan lengkap"""
        return {
            'best_categories': self.get_best_categories(),
            'best_hours': self.get_best_hours(),
            'brier_score': self.db.calculate_brier_score(),
            'recent_performance': self.db.get_recent_performance()
        }
    
    def print_summary(self):
        """Print ringkasan ke console"""
        summary = self.get_summary()
        
        print("\n" + "=" * 50)
        print("📊 WIN RATE ANALYSIS SUMMARY")
        print("=" * 50)
        
        print("\n🏆 Best Categories:")
        for cat, wr in list(summary['best_categories'].items())[:5]:
            bar = "█" * int(wr / 5)
            print(f"   {cat:15} : {wr:5.1f}% {bar}")
        
        print("\n🕐 Best Hours (UTC):")
        for hour, wr in list(summary['best_hours'].items())[:5]:
            bar = "█" * int(wr / 5)
            print(f"   {hour:2}:00          : {wr:5.1f}% {bar}")
        
        print(f"\n📈 Recent Performance (last 20 trades):")
        perf = summary['recent_performance']
        print(f"   Winrate: {perf.get('winrate', 0)}%")
        print(f"   Avg PnL: {perf.get('avg_pnl', 0):+.2f}%")
        
        print(f"\n🎯 Brier Score: {summary['brier_score']}")
        
        print("=" * 50)