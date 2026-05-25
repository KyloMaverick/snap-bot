"""
BRIER SCORE TRACKER
Mengukur akurasi kalibrasi prediksi bot
"""

from typing import Dict, List, Optional
from .database import LearningDB


class BrierTracker:
    def __init__(self, db: LearningDB):
        self.db = db
        self.predictions = []  # cache untuk predictions terbaru
    
    def add_prediction(self, market_id: str, predicted_prob: float):
        """Catat prediksi yang dibuat bot"""
        self.predictions.append({
            'market_id': market_id,
            'predicted_prob': predicted_prob,
            'timestamp': None  # akan diisi saat resolve
        })
    
    def resolve_prediction(self, market_id: str, actual_outcome: int):
        """
        Market resolved - update dengan outcome real
        
        Args:
            market_id: ID market
            actual_outcome: 1 untuk YES, 0 untuk NO
        """
        # Cari prediksi yang sesuai
        for pred in self.predictions:
            if pred['market_id'] == market_id:
                self.db.save_prediction(market_id, pred['predicted_prob'], actual_outcome)
                self.predictions.remove(pred)
                break
        
        # Hitung Brier score terbaru
        brier = self.get_brier_score()
        print(f"📊 Brier Score updated: {brier} (lower is better)")
    
    def get_brier_score(self) -> float:
        """Dapatkan Brier score saat ini"""
        return self.db.calculate_brier_score()
    
    def get_calibration_status(self) -> Dict:
        """
        Dapatkan status kalibrasi
        
        Brier score interpretation:
        - 0.00: Perfect calibration
        - 0.01-0.10: Excellent
        - 0.11-0.20: Good
        - 0.21-0.30: Acceptable
        - >0.30: Poor - perlu adjustment
        """
        brier = self.get_brier_score()
        
        if brier <= 0.10:
            status = "EXCELLENT"
            recommendation = "✅ Keep current threshold"
            adjustment = 0.95  # bisa turunin threshold
        elif brier <= 0.20:
            status = "GOOD"
            recommendation = "✅ Threshold OK"
            adjustment = 1.0
        elif brier <= 0.30:
            status = "ACCEPTABLE"
            recommendation = "⚠️ Consider increasing threshold slightly"
            adjustment = 1.1
        else:
            status = "POOR"
            recommendation = "⚠️ Increase threshold significantly"
            adjustment = 1.3
        
        return {
            'brier_score': brier,
            'status': status,
            'recommendation': recommendation,
            'threshold_adjustment': adjustment,
            'needs_calibration': brier > 0.25
        }
    
    def get_confidence_multiplier(self) -> float:
        """
        Dapatkan multiplier untuk confidence score
        
        Bot yang calibrated bagus bisa lebih agresif
        """
        status = self.get_calibration_status()
        brier = status['brier_score']
        
        if brier <= 0.10:
            return 1.2  # bonus 20%
        elif brier <= 0.20:
            return 1.0
        elif brier <= 0.30:
            return 0.9
        else:
            return 0.7  # penalty 30%