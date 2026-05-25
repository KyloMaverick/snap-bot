"""
PAPER TRADING SIMULATOR
Simulasi trade tanpa uang real, track profit/loss
"""

from datetime import datetime
from typing import Dict, Optional, List
import random


class PaperTrader:
    def __init__(self, initial_balance: float = 20.0):
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.open_positions = []
        self.closed_positions = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # Parameter simulasi
        self.take_profit_pct = 3.0   # +3% exit
        self.stop_loss_pct = -3.0    # -3% exit
        self.max_hold_hours = 6     # FIX 3: Max 6 jam hold
    
    def execute_trade(self, market: Dict, side: str, size: float, entry_price: float) -> Dict:
        """Eksekusi trade (simulasi)"""
        
        # Cek apakah sudah punya posisi di market yang sama
        for pos in self.open_positions:
            if pos['market_id'] == market.get('id'):
                return {'success': False, 'reason': f'Already have position in this market'}
        
        if size > self.balance:
            return {'success': False, 'reason': f'Insufficient balance: ${self.balance:.2f}'}
        
        # Hitung TP dan SL berdasarkan side
        if side == "BUY":
            take_profit = entry_price * (1 + self.take_profit_pct / 100)
            stop_loss = entry_price * (1 + self.stop_loss_pct / 100)
        else:  # SELL
            take_profit = entry_price * (1 - self.take_profit_pct / 100)
            stop_loss = entry_price * (1 - self.stop_loss_pct / 100)
        
        position = {
            'id': len(self.open_positions) + len(self.closed_positions) + 1,
            'market_id': market.get('id'),
            'market_question': market.get('question'),
            'side': side,
            'size': size,
            'entry_price': entry_price,
            'entry_time': datetime.now(),
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'status': 'OPEN'
        }
        
        self.open_positions.append(position)
        self.balance -= size
        
        print(f"   📈 PAPER TRADE: {side} ${size:.2f} @ {entry_price:.3f}")
        if side == "BUY":
            print(f"      TP: {take_profit:.3f} (+{self.take_profit_pct}%)")
            print(f"      SL: {stop_loss:.3f} ({self.stop_loss_pct}%)")
        else:
            print(f"      TP: {take_profit:.3f} (+{self.take_profit_pct}%)")
            print(f"      SL: {stop_loss:.3f} ({self.stop_loss_pct}%)")
        
        return {'success': True, 'position': position}
    
    def update_positions(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Update semua posisi berdasarkan harga terbaru
        
        FIX 3: Menambahkan time-based exit (max 24 jam)
        """
        closed_positions = []
        
        for pos in self.open_positions[:]:
            market_id = pos['market_id']
            current_price = current_prices.get(market_id, pos['entry_price'])
            
            # ===== FIX 3: Time-based exit (max 24 jam) =====
            hours_held = (datetime.now() - pos['entry_time']).total_seconds() / 3600
            
            # Time-based exit: paksa close setelah 24 jam
            if hours_held >= self.max_hold_hours:
                pos['exit_price'] = current_price
                pos['exit_reason'] = f'TIME_EXIT_{self.max_hold_hours}H'
                pos = self._close_position(pos, current_price)
                closed_positions.append(pos)
                print(f"   ⏰ TIME EXIT: {pos['market_question'][:40]}... held for {hours_held:.1f}h")
                continue
            
            # Cek take profit (berdasarkan side)
            if pos['side'] == 'BUY':
                if current_price >= pos['take_profit']:
                    pos['exit_price'] = pos['take_profit']
                    pos['exit_reason'] = 'TAKE_PROFIT'
                    pos = self._close_position(pos, current_price)
                    closed_positions.append(pos)
                elif current_price <= pos['stop_loss']:
                    pos['exit_price'] = pos['stop_loss']
                    pos['exit_reason'] = 'STOP_LOSS'
                    pos = self._close_position(pos, current_price)
                    closed_positions.append(pos)
            else:  # SELL
                if current_price <= pos['take_profit']:
                    pos['exit_price'] = pos['take_profit']
                    pos['exit_reason'] = 'TAKE_PROFIT'
                    pos = self._close_position(pos, current_price)
                    closed_positions.append(pos)
                elif current_price >= pos['stop_loss']:
                    pos['exit_price'] = pos['stop_loss']
                    pos['exit_reason'] = 'STOP_LOSS'
                    pos = self._close_position(pos, current_price)
                    closed_positions.append(pos)
        
        return closed_positions
    
    def _close_position(self, position: Dict, current_price: float) -> Dict:
        """Tutup posisi dan update balance"""
        
        # Hitung PnL berdasarkan side
        if position['side'] == 'BUY':
            pnl = position['size'] * (current_price - position['entry_price']) / position['entry_price']
        else:  # SELL
            pnl = position['size'] * (position['entry_price'] - current_price) / position['entry_price']
        
        position['exit_price'] = current_price
        position['exit_time'] = datetime.now()
        position['pnl'] = pnl
        position['pnl_pct'] = (pnl / position['size']) * 100 if position['size'] > 0 else 0
        position['status'] = 'CLOSED'
        
        # Update balance (kembalikan size + profit/loss)
        self.balance += position['size'] + pnl
        
        # Update stats
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # Pindahkan dari open ke closed
        self.open_positions.remove(position)
        self.closed_positions.append(position)
        
        return position
    
    def get_open_positions_count(self) -> int:
        """Dapatkan jumlah posisi yang masih terbuka"""
        return len(self.open_positions)
    
    def get_stats(self) -> Dict:
        """Dapatkan statistik trading"""
        winrate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        # Hitung total realized PnL (dari closed positions)
        total_realized_pnl = sum(p['pnl'] for p in self.closed_positions)
        
        # Hitung unrealized PnL (dari open positions)
        # Note: Ini hanya estimasi, karena current_price tidak tersedia di sini
        unrealized_pnl = 0
        
        return {
            'balance': round(self.balance, 2),
            'total_pnl': round(total_realized_pnl, 2),
            'total_pnl_pct': round((self.balance + unrealized_pnl - self.initial_balance) / self.initial_balance * 100, 2),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'winrate': round(winrate, 1),
            'open_positions': len(self.open_positions),
            'closed_positions': len(self.closed_positions)
        }
    
    def print_summary(self):
        """Print ringkasan performa"""
        stats = self.get_stats()
        
        print("\n" + "=" * 50)
        print("📊 PAPER TRADING SUMMARY")
        print("=" * 50)
        print(f"   Balance:        ${stats['balance']:.2f}")
        print(f"   Realized PnL:   ${stats['total_pnl']:+.2f}")
        print(f"   Total Trades:   {stats['total_trades']} (Closed: {stats['closed_positions']}, Open: {stats['open_positions']})")
        print(f"   Wins/Losses:    {stats['winning_trades']}/{stats['losing_trades']}")
        print(f"   Winrate:        {stats['winrate']}%")
        print("=" * 50)