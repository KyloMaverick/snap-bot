"""
STAGE 4: RISK & CORRELATION CHECK
Cek risk sebelum entry
"""

from typing import Dict, Tuple, List

class RiskChecker:
    def __init__(self):
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.open_positions = []
        self.daily_trades = 0
        self.daily_loss_limit = -6.0  # -6% max daily loss
        self.max_consecutive_losses = 3
        self.max_open_positions = 2
        self.max_daily_trades = 20
    
    def update_after_trade(self, pnl_pct: float, is_win: bool):
        """Update risk state setelah trade selesai"""
        self.daily_pnl += pnl_pct
        self.daily_trades += 1
        
        if is_win:
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
    
    def add_position(self, market_id: str, market_question: str, size: float):
        """Tambah posisi ke daftar"""
        self.open_positions.append({
            'market_id': market_id,
            'market_question': market_question,
            'size': size,
            'entry_time': None  # nanti diisi
        })
    
    def remove_position(self, market_id: str):
        """Hapus posisi dari daftar"""
        self.open_positions = [p for p in self.open_positions if p['market_id'] != market_id]
    
    def check_correlation(self, new_market_id: str, new_market_question: str) -> Tuple[bool, str]:
        """
        Cek apakah market baru correlated dengan posisi yang sudah terbuka
        
        FIX 1: Mencegah double entry di market yang SAMA PERSIS
        """
        # ===== FIX 1: Cek market ID yang sama persis =====
        for pos in self.open_positions:
            if pos.get('market_id') == new_market_id:
                return False, f"❌ Already have position in THIS SAME market: {new_market_question[:40]}..."
        
        # Daftar kata kunci yang berkorelasi
        correlated_topics = {
            'btc': ['btc', 'bitcoin'],
            'eth': ['eth', 'ethereum'],
            'rihanna': ['rihanna', 'album'],
            'playboi': ['playboi', 'carti'],
            'trump': ['trump', 'donald'],
            'gta': ['gta', 'grand theft auto'],
            'harvey': ['harvey', 'weinstein'],
            'china': ['china', 'taiwan', 'invades'],
            'jesus': ['jesus', 'christ']
        }
        
        new_question_lower = new_market_question.lower()
        
        # Cek topic dari market baru
        new_topic = None
        for topic, keywords in correlated_topics.items():
            if any(kw in new_question_lower for kw in keywords):
                new_topic = topic
                break
        
        if not new_topic:
            return True, "✅ No correlation detected (no topic match)"
        
        # Cek apakah ada posisi dengan topic yang sama
        for pos in self.open_positions:
            pos_question = pos.get('market_question', '').lower()
            for topic, keywords in correlated_topics.items():
                if topic == new_topic and any(kw in pos_question for kw in keywords):
                    return False, f"❌ Correlated market detected: {pos.get('market_question', '')[:40]}..."
        
        return True, "✅ No correlation detected"
    
    def risk_check(self, market: Dict) -> Tuple[bool, str]:
        """
        Stage 4: Risk check sebelum entry
        """
        market_id = market.get('id', '')
        market_question = market.get('question', '')
        
        # 1. Cek daily loss limit
        if self.daily_pnl <= self.daily_loss_limit:
            return False, f"❌ Daily loss limit reached: {self.daily_pnl:.2f}% (limit -6.0%)"
        
        # 2. Cek consecutive losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            return False, f"❌ Max consecutive losses: {self.consecutive_losses} (limit {self.max_consecutive_losses})"
        
        # 3. Cek max open positions
        if len(self.open_positions) >= self.max_open_positions:
            return False, f"❌ Max open positions: {len(self.open_positions)} (limit {self.max_open_positions})"
        
        # 4. Cek max daily trades
        if self.daily_trades >= self.max_daily_trades:
            return False, f"❌ Max daily trades reached: {self.daily_trades} (limit {self.max_daily_trades})"
        
        # 5. Cek correlation dengan existing positions (termasuk market yang sama)
        correlated_ok, correlated_reason = self.check_correlation(market_id, market_question)
        if not correlated_ok:
            return False, correlated_reason
        
        reason = f"✅ Risk OK (daily_pnl={self.daily_pnl:.2f}%, loss_streak={self.consecutive_losses}, open={len(self.open_positions)})"
        
        return True, reason


# Buat instance global
risk_checker = RiskChecker()


def get_risk_checker() -> RiskChecker:
    """Dapatkan instance risk checker"""
    return risk_checker


def risk_check_static(market: Dict) -> Tuple[bool, str]:
    """Wrapper untuk static call"""
    return risk_checker.risk_check(market)