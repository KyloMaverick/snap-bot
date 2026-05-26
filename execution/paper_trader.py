"""
PAPER TRADING SIMULATOR
Simulasi trade tanpa uang real, track profit/loss
 
FIX 1: TP/SL sekarang berbasis PnL dollar (% dari size),
        bukan persentase pergerakan harga entry.
        
        Contoh lama (SALAH untuk Polymarket):
          entry=0.50, TP+3% → target harga 0.515
          → harga Polymarket jarang bergerak sebanyak itu
        
        Contoh baru (BENAR):
          size=$2.00, TP+3% → exit kalau unrealized PnL ≥ +$0.06
          → jauh lebih realistis untuk prediction market
"""
 
from datetime import datetime
from typing import Dict, Optional, List
 
 
class PaperTrader:
    def __init__(self, initial_balance: float = 20.0):
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.open_positions = []
        self.closed_positions = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
 
        # FIX 1: Parameter TP/SL dalam persen dari SIZE (bukan dari harga)
        self.take_profit_pct = 3.0   # exit kalau pnl >= +3% dari size
        self.stop_loss_pct   = -3.0  # exit kalau pnl <= -3% dari size
        self.max_hold_hours  = 24    # time exit maksimal 24 jam
 
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
 
    def _calc_pnl(self, position: Dict, current_price: float) -> float:
        """
        Hitung unrealized PnL dalam dollar berdasarkan pergerakan harga.
 
        Untuk prediction market, kita membeli/menjual kontrak biner.
        BUY  → profit kalau harga naik  (market makin yakin event terjadi)
        SELL → profit kalau harga turun (market makin yakin event tidak terjadi)
        """
        entry  = position['entry_price']
        size   = position['size']
 
        if entry == 0:
            return 0.0
 
        if position['side'] == 'BUY':
            # kontrak naik nilai → profit
            pnl = size * (current_price - entry) / entry
        else:  # SELL
            # kontrak turun nilai → profit
            pnl = size * (entry - current_price) / entry
 
        return pnl
 
    def _pnl_pct_of_size(self, pnl: float, size: float) -> float:
        """PnL sebagai persentase dari size yang diinvestasikan."""
        return (pnl / size * 100) if size > 0 else 0.0
 
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
 
    def execute_trade(self, market: Dict, side: str, size: float,
                      entry_price: float) -> Dict:
        """Eksekusi trade (simulasi)."""
 
        # Cek duplikat posisi di market yang sama
        for pos in self.open_positions:
            if pos['market_id'] == market.get('id'):
                return {'success': False,
                        'reason': 'Already have position in this market'}
 
        if size > self.balance:
            return {'success': False,
                    'reason': f'Insufficient balance: ${self.balance:.2f}'}
 
        position = {
            'id':               len(self.open_positions) + len(self.closed_positions) + 1,
            'market_id':        market.get('id'),
            'market_question':  market.get('question'),
            'side':             side,
            'size':             size,
            'entry_price':      entry_price,
            'entry_time':       datetime.now(),
            'status':           'OPEN',
            # TP/SL disimpan sebagai ambang PnL dollar, bukan sebagai harga
            'tp_dollar':        size * self.take_profit_pct / 100,   # e.g. +$0.06
            'sl_dollar':        size * self.stop_loss_pct  / 100,    # e.g. -$0.06
        }
 
        self.open_positions.append(position)
        self.balance -= size
 
        tp_pct = self.take_profit_pct
        sl_pct = self.stop_loss_pct
 
        print(f"   📈 PAPER TRADE: {side} ${size:.2f} @ {entry_price:.3f}")
        print(f"      TP: pnl ≥ +${position['tp_dollar']:.3f} (+{tp_pct}% of size)")
        print(f"      SL: pnl ≤ ${position['sl_dollar']:.3f} ({sl_pct}% of size)")
        print(f"      Time exit: {self.max_hold_hours}h")
 
        return {'success': True, 'position': position}
 
    def update_positions(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Update semua posisi berdasarkan harga terbaru.
 
        FIX 1: cek TP/SL berdasarkan unrealized PnL dollar vs size,
               bukan perbandingan harga langsung.
        """
        closed_positions = []
 
        for pos in self.open_positions[:]:
            market_id     = pos['market_id']
            current_price = current_prices.get(market_id, pos['entry_price'])
            hours_held    = (datetime.now() - pos['entry_time']).total_seconds() / 3600
 
            # --- Time exit ---
            if hours_held >= self.max_hold_hours:
                pos['exit_reason'] = f'TIME_EXIT_{self.max_hold_hours}H'
                closed = self._close_position(pos, current_price)
                closed_positions.append(closed)
                print(f"   ⏰ TIME EXIT: {pos['market_question'][:40]}... "
                      f"held {hours_held:.1f}h | PnL: {closed['pnl']:+.3f}")
                continue
 
            # --- FIX 1: PnL-based TP/SL ---
            unrealized_pnl = self._calc_pnl(pos, current_price)
            pnl_pct        = self._pnl_pct_of_size(unrealized_pnl, pos['size'])
 
            if unrealized_pnl >= pos['tp_dollar']:
                pos['exit_reason'] = 'TAKE_PROFIT'
                closed = self._close_position(pos, current_price)
                closed_positions.append(closed)
                print(f"   ✅ TAKE PROFIT: {pos['market_question'][:40]}... "
                      f"pnl={unrealized_pnl:+.3f} ({pnl_pct:+.1f}%)")
 
            elif unrealized_pnl <= pos['sl_dollar']:
                pos['exit_reason'] = 'STOP_LOSS'
                closed = self._close_position(pos, current_price)
                closed_positions.append(closed)
                print(f"   ❌ STOP LOSS:   {pos['market_question'][:40]}... "
                      f"pnl={unrealized_pnl:+.3f} ({pnl_pct:+.1f}%)")
 
        return closed_positions
 
    def _close_position(self, position: Dict, current_price: float) -> Dict:
        """Tutup posisi, update balance dan stats."""
 
        pnl     = self._calc_pnl(position, current_price)
        pnl_pct = self._pnl_pct_of_size(pnl, position['size'])
 
        position['exit_price'] = current_price
        position['exit_time']  = datetime.now()
        position['pnl']        = pnl
        position['pnl_pct']    = pnl_pct
        position['status']     = 'CLOSED'
 
        # Kembalikan modal + profit/loss
        self.balance += position['size'] + pnl
 
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
 
        self.open_positions.remove(position)
        self.closed_positions.append(position)
 
        return position
 
    def get_open_positions_count(self) -> int:
        return len(self.open_positions)
 
    def get_stats(self) -> Dict:
        winrate           = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        total_realized    = sum(p['pnl'] for p in self.closed_positions)
        total_pnl_pct     = ((self.balance - self.initial_balance) / self.initial_balance * 100)
 
        return {
            'balance':          round(self.balance, 4),
            'total_pnl':        round(total_realized, 4),
            'total_pnl_pct':    round(total_pnl_pct, 2),
            'total_trades':     self.total_trades,
            'winning_trades':   self.winning_trades,
            'losing_trades':    self.losing_trades,
            'winrate':          round(winrate, 1),
            'open_positions':   len(self.open_positions),
            'closed_positions': len(self.closed_positions),
        }
 
    def print_summary(self):
        stats = self.get_stats()
        print("\n" + "=" * 50)
        print("📊 PAPER TRADING SUMMARY")
        print("=" * 50)
        print(f"   Balance:        ${stats['balance']:.4f}")
        print(f"   Realized PnL:   ${stats['total_pnl']:+.4f}  ({stats['total_pnl_pct']:+.2f}%)")
        print(f"   Total Trades:   {stats['total_trades']} "
              f"(Open: {stats['open_positions']}, Closed: {stats['closed_positions']})")
        print(f"   Wins/Losses:    {stats['winning_trades']}/{stats['losing_trades']}")
        print(f"   Winrate:        {stats['winrate']}%")
        print("=" * 50)
 
