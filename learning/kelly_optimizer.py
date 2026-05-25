"""
KELLY OPTIMIZER
Menentukan position sizing optimal berdasarkan performa historis
"""

from typing import Dict, Optional
from .database import LearningDB
from .winrate_analyzer import WinRateAnalyzer


class KellyOptimizer:
    def __init__(self, db: LearningDB, winrate_analyzer: WinRateAnalyzer):
        self.db = db
        self.winrate_analyzer = winrate_analyzer
        
        # Batasan position sizing
        self.max_position_pct = 0.30  # maksimal 30% balance
        self.min_position_pct = 0.05  # minimal 5% balance
    
    def calculate_kelly_fraction(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Hitung Kelly fraction
        Formula: f = (p * b - q) / b
        dimana:
        - p = win rate
        - q = loss rate (1 - p)
        - b = average win / average loss
        """
        if avg_loss == 0:
            return 0.1
        
        b = avg_win / abs(avg_loss) if avg_win > 0 else 1
        q = 1 - win_rate
        
        kelly = (win_rate * b - q) / b
        
        # Batasi ke range yang aman
        return max(0.05, min(0.25, kelly))
    
    def get_position_size(self, 
                          balance: float, 
                          confidence_level: str,
                          confidence_score: int,
                          category: str = None,
                          hour: int = None,
                          mode: str = "SAFE") -> float:
        """
        Hitung position size berdasarkan multiple faktor
        
        Args:
            balance: Saldo saat ini
            confidence_level: HIGH, MEDIUM, LOW
            confidence_score: Score 0-100
            category: Kategori market
            hour: Jam entry
            mode: SAFE atau AGGRESSIVE
        
        Returns:
            Position size dalam dollar
        """
        # 1. Base size dari confidence level
        if confidence_level == "HIGH":
            base_pct = 0.25  # 25%
        elif confidence_level == "MEDIUM":
            base_pct = 0.15  # 15%
        else:
            base_pct = 0.10  # 10%
        
        # 2. Adjustment berdasarkan win rate kategori
        if category:
            multiplier = self.winrate_analyzer.get_position_size_multiplier(category, hour or 12)
            base_pct *= multiplier
        
        # 3. Adjustment berdasarkan mode
        if mode == "SAFE":
            base_pct *= 0.7
        elif mode == "AGGRESSIVE":
            base_pct *= 1.0
        
        # 4. Adjustment berdasarkan confidence score
        # Score 100 -> +20% size, Score 50 -> 0%, Score 0 -> -20%
        score_factor = 0.8 + (confidence_score / 100) * 0.4
        base_pct *= score_factor
        
        # 5. Kelly-based adjustment (jika ada cukup data)
        recent = self.db.get_recent_performance(limit=20)
        winrate = recent.get('winrate', 50) / 100
        
        if recent.get('total_trades', 0) >= 10:
            avg_pnl = recent.get('avg_pnl', 1)
            kelly = self.calculate_kelly_fraction(winrate, avg_pnl, -2.0)
            base_pct = min(base_pct, kelly)
        
        # Clamp ke range aman
        final_pct = max(self.min_position_pct, min(self.max_position_pct, base_pct))
        
        # Hitung dalam dollar
        position_size = balance * final_pct
        
        return round(position_size, 2)
    
    def get_max_position_size(self, balance: float, category: str = None) -> float:
        """
        Dapatkan maksimal position size berdasarkan risk profile
        """
        max_pct = self.max_position_pct
        
        # Kategori dengan volatilitas tinggi → size lebih kecil
        if category == 'crypto':
            max_pct = min(max_pct, 0.20)
        elif category == 'politics':
            max_pct = min(max_pct, 0.25)
        
        return round(balance * max_pct, 2)
    
    def get_risk_level(self, position_size: float, balance: float) -> str:
        """Tentukan level risk berdasarkan size"""
        pct = position_size / balance if balance > 0 else 0
        
        if pct <= 0.10:
            return "LOW"
        elif pct <= 0.20:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def print_recommendation(self, balance: float, confidence_level: str, confidence_score: int):
        """Print rekomendasi position sizing"""
        size = self.get_position_size(balance, confidence_level, confidence_score)
        pct = size / balance * 100 if balance > 0 else 0
        
        print(f"\n📊 POSITION SIZING RECOMMENDATION")
        print(f"   Balance: ${balance:.2f}")
        print(f"   Confidence: {confidence_level} ({confidence_score})")
        print(f"   Recommended size: ${size:.2f} ({pct:.1f}%)")
        print(f"   Risk level: {self.get_risk_level(size, balance)}")