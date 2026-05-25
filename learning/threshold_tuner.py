"""
ADAPTIVE THRESHOLD TUNER
Menyesuaikan threshold edge berdasarkan performa historis
"""

from typing import Dict, Optional
from .database import LearningDB
from .brier_tracker import BrierTracker
from .winrate_analyzer import WinRateAnalyzer


class AdaptiveThreshold:
    def __init__(self, db: LearningDB, brier_tracker: BrierTracker, winrate_analyzer: WinRateAnalyzer):
        self.db = db
        self.brier_tracker = brier_tracker
        self.winrate_analyzer = winrate_analyzer
        
        # Base threshold (safe mode default)
        self.base_threshold = 4.0
        self.min_threshold = 2.5
        self.max_threshold = 5.5
        
        # Track perubahan
        self.adjustment_history = []
    
    def calculate_dynamic_threshold(self, category: str = None, hour: int = None, mode: str = "SAFE") -> float:
        """
        Hitung threshold dinamis berdasarkan:
        1. Brier score (kalibrasi bot)
        2. Win rate kategori
        3. Win rate jam
        4. Recent performance
        
        Returns:
            threshold dalam persen (2.5 - 5.5)
        """
        # Start dengan base threshold
        threshold = self.base_threshold
        
        # 1. Adjustment berdasarkan Brier score
        calibration_status = self.brier_tracker.get_calibration_status()
        brier_adjustment = calibration_status.get('threshold_adjustment', 1.0)
        threshold *= brier_adjustment
        
        # 2. Adjustment berdasarkan kategori (jika ada)
        if category:
            cat_threshold = self.winrate_analyzer.get_optimal_threshold_for_category(category)
            # Weighted average: 70% kategori, 30% base
            threshold = (threshold * 0.3) + (cat_threshold * 0.7)
        
        # 3. Adjustment berdasarkan jam (jika ada)
        if hour is not None:
            winrates_hour = self.db.get_winrate_by_hour()
            hour_wr = winrates_hour.get(hour, 50)
            
            if hour_wr >= 60:
                threshold *= 0.9  # turunin threshold
            elif hour_wr <= 40:
                threshold *= 1.15  # naikin threshold
        
        # 4. Mode adjustment
        if mode == "AGGRESSIVE":
            threshold *= 0.85  # 15% lebih rendah
        elif mode == "SAFE":
            threshold *= 1.0  # tetap
        
        # 5. Recent performance adjustment
        recent = self.db.get_recent_performance(limit=10)
        recent_winrate = recent.get('winrate', 50)
        
        if recent_winrate < 40:
            threshold *= 1.2  # naikin threshold (lebih hati-hati)
        elif recent_winrate > 60:
            threshold *= 0.9  # turunin threshold (bisa lebih agresif)
        
        # Clamp ke range
        threshold = max(self.min_threshold, min(self.max_threshold, threshold))
        
        # Simpan history
        self.adjustment_history.append({
            'timestamp': None,  # akan diisi
            'threshold': threshold,
            'category': category,
            'hour': hour,
            'mode': mode
        })
        
        return round(threshold, 2)
    
    def get_current_threshold(self, market: Dict = None, mode: str = "SAFE") -> float:
        """
        Dapatkan threshold untuk market tertentu
        
        Args:
            market: Data market (opsional)
            mode: "SAFE" atau "AGGRESSIVE"
        """
        category = market.get('category') if market else None
        hour = None  # bisa diisi dari timestamp
        
        return self.calculate_dynamic_threshold(category, hour, mode)
    
    def should_adjust_based_on_brier(self) -> bool:
        """Apakah perlu adjustment berdasarkan Brier score?"""
        cal_status = self.brier_tracker.get_calibration_status()
        return cal_status['needs_calibration']
    
    def get_threshold_explanation(self, threshold: float, market: Dict = None) -> str:
        """Dapatkan penjelasan kenapa threshold tertentu dipilih"""
        parts = []
        
        if self.brier_tracker.get_brier_score() > 0.25:
            parts.append("Brier score tinggi (>0.25): threshold dinaikkan")
        
        if market:
            cat = market.get('category')
            if cat:
                cat_wr = self.db.get_winrate_by_category().get(cat, 50)
                if cat_wr < 40:
                    parts.append(f"Kategori {cat} winrate rendah ({cat_wr}%): threshold dinaikkan")
                elif cat_wr > 60:
                    parts.append(f"Kategori {cat} winrate tinggi ({cat_wr}%): threshold diturunkan")
        
        if not parts:
            parts.append("Threshold standar berdasarkan base configuration")
        
        return f"Threshold {threshold}%: " + " | ".join(parts)
    
    def print_status(self):
        """Print status threshold tuner"""
        cal_status = self.brier_tracker.get_calibration_status()
        
        print("\n" + "=" * 50)
        print("🎯 ADAPTIVE THRESHOLD STATUS")
        print("=" * 50)
        print(f"   Base threshold: {self.base_threshold}%")
        print(f"   Range: {self.min_threshold}% - {self.max_threshold}%")
        print(f"   Brier Score: {cal_status['brier_score']} ({cal_status['status']})")
        print(f"   Calibration needed: {cal_status['needs_calibration']}")
        print("=" * 50)