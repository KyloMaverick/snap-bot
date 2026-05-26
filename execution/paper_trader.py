"""
PAPER TRADING SIMULATOR
Simulasi trade tanpa uang real, track profit/loss

FIX 1: TP/SL berbasis PnL dollar (% dari size), bukan persentase harga
FIX 4: Persistence posisi ke SQLite, tahan Railway restart
"""

from datetime import datetime
from typing import Dict, Optional, List
import sqlite3


class PaperTrader:
    def __init__(self, initial_balance: float = 20.0, db_path: str = "snap_bot_data.db"):
        self.db_path         = db_path
        self.initial_balance = initial_balance
        self.balance         = initial_balance
        self.open_positions  = []
        self.closed_positions= []
        self.total_trades    = 0
        self.winning_trades  = 0
        self.losing_trades   = 0

        self.take_profit_pct = 3.0
        self.stop_loss_pct   = -3.0
        self.max_hold_hours  = 24

        self._init_positions_table()
        self._load_open_positions()

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _init_positions_table(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS open_positions (
                    market_id       TEXT PRIMARY KEY,
                    market_question TEXT,
                    side            TEXT,
                    size            REAL,
                    entry_price     REAL,
                    entry_time      TEXT,
                    tp_dollar       REAL,
                    sl_dollar       REAL
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ DB init error: {e}")

    def _load_open_positions(self):
        try:
            conn   = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT market_id, market_question, side, size,
                       entry_price, entry_time, tp_dollar, sl_dollar
                FROM open_positions
            """)
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                pos = {
                    'market_id':       row[0],
                    'market_question': row[1],
                    'side':            row[2],
                    'size':            row[3],
                    'entry_price':     row[4],
                    'entry_time':      datetime.fromisoformat(row[5]),
                    'tp_dollar':       row[6],
                    'sl_dollar':       row[7],
                    'status':          'OPEN',
                }
                self.open_positions.append(pos)
                self.balance -= row[3]

            if self.open_positions:
                print(f"   ♻️  Loaded {len(self.open_positions)} open position(s) from DB")

        except Exception as e:
            print(f"⚠️ Load positions error: {e}")

    def _save_open_position(self, position: Dict):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT OR REPLACE INTO open_positions
                (market_id, market_question, side, size,
                 entry_price, entry_time, tp_dollar, sl_dollar)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                position['market_id'],
                position['market_question'],
                position['side'],
                position['size'],
                position['entry_price'],
                position['entry_time'].isoformat(),
                position['tp_dollar'],
                position['sl_dollar'],
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Save position error: {e}")

    def _delete_open_position(self, market_id: str):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM open_positions WHERE market_id = ?", (market_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Delete position error: {e}")

    # ------------------------------------------------------------------
    # PnL helpers
    # ------------------------------------------------------------------

    def _calc_pnl(self, position: Dict, current_price: float) -> float:
        entry = position['entry_price']
        size  = position['size']
        if entry == 0:
            return 0.0
        if position['side'] == 'BUY':
            return size * (current_price - entry) / entry
        else:
            return size * (entry - current_price) / entry

    def _pnl_pct_of_size(self, pnl: float, size: float) -> float:
        return (pnl / size * 100) if size > 0 else 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute_trade(self, market: Dict, side: str, size: float,
                      entry_price: float) -> Dict:

        for pos in self.open_positions:
            if pos['market_id'] == market.get('id'):
                return {'success': False, 'reason': 'Already have position in this market'}

        if size > self.balance:
            return {'success': False, 'reason': f'Insufficient balance: ${self.balance:.2f}'}

        position = {
            'id':              len(self.open_positions) + len(self.closed_positions) + 1,
            'market_id':       market.get('id'),
            'market_question': market.get('question'),
            'side':            side,
            'size':            size,
            'entry_price':     entry_price,
            'entry_time':      datetime.now(),
            'tp_dollar':       size * self.take_profit_pct / 100,
            'sl_dollar':       size * self.stop_loss_pct   / 100,
            'status':          'OPEN',
        }

        self.open_positions.append(position)
        self._save_open_position(position)
        self.balance -= size

        print(f"   📈 PAPER TRADE: {side} ${size:.2f} @ {entry_price:.3f}")
        print(f"      TP: pnl ≥ +${position['tp_dollar']:.3f} (+{self.take_profit_pct}% of size)")
        print(f"      SL: pnl ≤  ${position['sl_dollar']:.3f} ({self.stop_loss_pct}% of size)")
        print(f"      Time exit: {self.max_hold_hours}h")

        return {'success': True, 'position': position}

    def update_positions(self, current_prices: Dict[str, float]) -> List[Dict]:
        closed_positions = []

        for pos in self.open_positions[:]:
            market_id     = pos['market_id']
            current_price = current_prices.get(market_id, pos['entry_price'])
            hours_held    = (datetime.now() - pos['entry_time']).total_seconds() / 3600

            if hours_held >= self.max_hold_hours:
                pos['exit_reason'] = f'TIME_EXIT_{self.max_hold_hours}H'
                closed = self._close_position(pos, current_price)
                closed_positions.append(closed)
                print(f"   ⏰ TIME EXIT: {pos['market_question'][:40]}... "
                      f"held {hours_held:.1f}h | PnL: {closed['pnl']:+.4f}")
                continue

            unrealized_pnl = self._calc_pnl(pos, current_price)
            pnl_pct        = self._pnl_pct_of_size(unrealized_pnl, pos['size'])

            if unrealized_pnl >= pos['tp_dollar']:
                pos['exit_reason'] = 'TAKE_PROFIT'
                closed = self._close_position(pos, current_price)
                closed_positions.append(closed)
                print(f"   ✅ TAKE PROFIT: {pos['market_question'][:40]}... "
                      f"pnl={unrealized_pnl:+.4f} ({pnl_pct:+.1f}%)")

            elif unrealized_pnl <= pos['sl_dollar']:
                pos['exit_reason'] = 'STOP_LOSS'
                closed = self._close_position(pos, current_price)
                closed_positions.append(closed)
                print(f"   ❌ STOP LOSS:   {pos['market_question'][:40]}... "
                      f"pnl={unrealized_pnl:+.4f} ({pnl_pct:+.1f}%)")

        return closed_positions

    def _close_position(self, position: Dict, current_price: float) -> Dict:
        pnl     = self._calc_pnl(position, current_price)
        pnl_pct = self._pnl_pct_of_size(pnl, position['size'])

        position['exit_price'] = current_price
        position['exit_time']  = datetime.now()
        position['pnl']        = pnl
        position['pnl_pct']    = pnl_pct
        position['status']     = 'CLOSED'

        self.balance += position['size'] + pnl

        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        self.open_positions.remove(position)
        self._delete_open_position(position['market_id'])
        self.closed_positions.append(position)

        return position

    def get_open_positions_count(self) -> int:
        return len(self.open_positions)

    def get_stats(self) -> Dict:
        winrate        = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        total_realized = sum(p['pnl'] for p in self.closed_positions)
        total_pnl_pct  = ((self.balance - self.initial_balance) / self.initial_balance * 100)

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