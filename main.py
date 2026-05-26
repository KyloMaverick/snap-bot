"""
SNAP v1.0 - FULL TRADING BOT
Integrasi semua komponen + Telegram Alert + Fix 1,2,3,4
"""

import time
import sys
import os
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.polymarket_api import PolymarketAPI
from filters.stage1_prefilter import prefilter
from filters.stage2_edge import edge_check
from filters.stage3_liquidity import liquidity_check
from filters.stage4_risk import risk_check_static, get_risk_checker
from filters.stage5_confidence import confidence_check
from learning.database import LearningDB
from learning.brier_tracker import BrierTracker
from learning.winrate_analyzer import WinRateAnalyzer
from learning.threshold_tuner import AdaptiveThreshold
from learning.kelly_optimizer import KellyOptimizer
from execution.paper_trader import PaperTrader
from monitoring.telegram_alert import telegram

# ── shared state (dibaca cmd_handler) ──────────────────────────────
bot_state = {
    'status':       'starting',
    'mode':         'AGGRESSIVE',
    'balance':      20.0,
    'total_pnl':    0.0,
    'winrate':      0.0,
    'total_trades': 0,
    'open_positions': 0,
    'last_cycle':   None,
}


def reset_stale_positions(db_path: str = "snap_bot_data.db"):
    risk_checker = get_risk_checker()
    risk_checker.daily_pnl          = 0.0
    risk_checker.consecutive_losses = 0
    risk_checker.daily_trades       = 0
    risk_checker.open_positions     = []
    print("✅ Risk checker reset")

    try:
        if os.path.exists(db_path):
            conn   = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM trades WHERE exit_price IS NULL")
            cursor.execute("DELETE FROM open_positions")
            conn.commit()
            conn.close()
            print("✅ Database cleaned")
    except Exception as e:
        print(f"⚠️ Database clean skipped: {e}")


class SnapBot:
    def __init__(self, mode: str = "AGGRESSIVE", paper_mode: bool = True):
        self.mode         = mode
        self.paper_mode   = paper_mode
        self.db_path      = "snap_bot_data.db"
        self.api          = PolymarketAPI()
        self.db           = LearningDB(self.db_path)
        self.brier        = BrierTracker(self.db)
        self.winrate      = WinRateAnalyzer(self.db)
        self.threshold_tuner = AdaptiveThreshold(self.db, self.brier, self.winrate)
        self.kelly        = KellyOptimizer(self.db, self.winrate)
        self.risk_checker = get_risk_checker()

        if paper_mode:
            self.paper_trader = PaperTrader(
                initial_balance=20.0,
                db_path=self.db_path
            )
            self.balance = self.paper_trader.balance
        else:
            self.paper_trader = None
            self.balance      = 20.0

        self.cycle_count  = 0
        self.running      = True
        self.last_markets = []

        # Update shared state
        bot_state['mode']    = self.mode
        bot_state['balance'] = self.balance
        bot_state['status']  = 'running'

        print("=" * 60)
        print("🤖 SNAP v1.0 TRADING BOT")
        print("=" * 60)
        print(f"   Mode:            {self.mode}")
        print(f"   Paper Mode:      {'ON' if paper_mode else 'OFF'}")
        print(f"   Initial Balance: ${self.balance:.2f}")
        print(f"   Start Time:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        if telegram.bot_token != "YOUR_BOT_TOKEN_HERE":
            telegram.send_message(
                f"🤖 SNAP Bot Started!\nMode: {self.mode}\nBalance: ${self.balance:.2f}"
            )

    def _update_bot_state(self):
        """Sync bot_state supaya cmd_handler bisa baca data terbaru."""
        if self.paper_trader:
            stats = self.paper_trader.get_stats()
            bot_state['balance']       = stats['balance']
            bot_state['total_pnl']     = stats['total_pnl']
            bot_state['winrate']       = stats['winrate']
            bot_state['total_trades']  = stats['total_trades']
            bot_state['open_positions']= stats['open_positions']
        bot_state['last_cycle'] = datetime.now().strftime('%H:%M:%S')
        bot_state['status']     = 'running'

    def process_market(self, market):
        result = {
            'market':        market,
            'eligible':      False,
            'reason':        '',
            'side':          None,
            'position_size': 0,
            'confidence':    None,
        }

        passed, reason, filtered_data = prefilter(market)
        if not passed:
            result['reason'] = f"Stage1: {reason}"
            return result

        threshold = self.threshold_tuner.get_current_threshold(market, self.mode)

        passed, reason, edge, side, edge_data = edge_check(filtered_data, threshold)
        if not passed:
            result['reason'] = f"Stage2: {reason}"
            return result

        passed, reason, liquidity_data = liquidity_check(filtered_data, 10.0)
        if not passed:
            result['reason'] = f"Stage3: {reason}"
            return result

        passed, reason = risk_check_static(filtered_data)
        if not passed:
            result['reason'] = f"Stage4: {reason}"
            return result

        passed, reason, confidence_data = confidence_check(
            filtered_data, edge_data, liquidity_data, self.mode
        )
        if not passed:
            result['reason'] = f"Stage5: {reason}"
            return result

        confidence_level = confidence_data.get('level', 'MEDIUM')
        confidence_score = confidence_data.get('score', 50)

        position_size = self.kelly.get_position_size(
            self.balance, confidence_level, confidence_score,
            market.get('category'), datetime.now().hour, self.mode
        )

        result['eligible']       = True
        result['side']           = side
        result['position_size']  = position_size
        result['confidence']     = confidence_data
        result['edge']           = edge_data.get('edge', 0)
        result['edge_data']      = edge_data
        result['threshold_used'] = threshold
        result['reason']         = f"✅ ALL PASSED: {side} ${position_size:.2f}"

        return result

    def scan_and_trade(self):
        print(f"\n{'='*60}")
        print(f"🔄 SCAN CYCLE {self.cycle_count + 1}")
        if self.paper_trader:
            stats = self.paper_trader.get_stats()
            print(f"   Balance:  ${stats['balance']:.4f}")
            print(f"   Total PnL:${stats['total_pnl']:+.4f}")
            print(f"   Winrate:  {stats['winrate']}%")
        print(f"   Mode: {self.mode} | Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")

        markets = self.api.get_markets(limit=50)
        self.last_markets = markets

        if not markets:
            print("⚠️ No markets fetched")
            return

        print(f"📡 Scanning {len(markets)} markets...")

        signals = []
        for market in markets:
            result = self.process_market(market)
            if result['eligible']:
                signals.append(result)
                print(f"\n🎯 SIGNAL: {market.get('question', '')[:50]}...")
                print(f"   Side:       {result['side']}")
                print(f"   Size:       ${result['position_size']:.2f}")
                print(f"   Confidence: {result['confidence'].get('level', 'N/A')}")
                print(f"   Edge:       {result.get('edge', 0):+.2f}%")

        if not signals:
            print("\n📭 No valid signals this cycle")
        else:
            print(f"\n{'='*60}")
            print("💼 EXECUTING TRADES")
            print(f"{'='*60}")

            for signal in signals[:3]:
                market           = signal['market']
                side             = signal['side']
                size             = signal['position_size']
                entry_price      = market.get('price', 0.5)
                edge             = signal.get('edge', 0)
                confidence_level = signal['confidence'].get('level', 'MEDIUM')
                market_question  = market.get('question', 'Unknown')
                market_id        = market.get('id')

                if self.paper_mode and self.paper_trader:
                    result = self.paper_trader.execute_trade(market, side, size, entry_price)
                    if result['success']:
                        self.risk_checker.add_position(market_id, market_question, size)
                        edge_data  = signal.get('edge_data', {})
                        trade_data = {
                            'market_id':       market_id,
                            'market_question': market_question,
                            'category':        market.get('category'),
                            'side':            side,
                            'entry_price':     entry_price,
                            'predicted_prob':  edge_data.get('estimated_prob', 0.5),
                            'entry_hour':      datetime.now().hour,
                            'pnl':     0,
                            'pnl_pct': 0,
                        }
                        self.db.save_trade(trade_data)
                        if telegram.bot_token != "YOUR_BOT_TOKEN_HERE":
                            telegram.send_trade_signal(
                                market_question, side, size,
                                entry_price, edge, confidence_level
                            )

        # Update open positions
        if self.paper_mode and self.paper_trader and self.paper_trader.open_positions:
            current_prices = {}
            for pos in self.paper_trader.open_positions:
                market_data = next(
                    (m for m in markets if m.get('id') == pos['market_id']), None
                )
                current_prices[pos['market_id']] = (
                    market_data.get('price', pos['entry_price'])
                    if market_data else pos['entry_price']
                )

            closed = self.paper_trader.update_positions(current_prices)
            for pos in closed:
                print(f"\n   🏁 CLOSED: {pos['market_question'][:40]}... "
                      f"| {pos['exit_reason']} | PnL: {pos['pnl']:+.4f}")
                self.risk_checker.remove_position(pos['market_id'])
                if telegram.bot_token != "YOUR_BOT_TOKEN_HERE":
                    telegram.send_trade_result(
                        pos['market_question'], pos['side'],
                        pos['pnl'], pos['pnl_pct'], pos['exit_reason']
                    )

        if self.paper_mode and self.paper_trader:
            self.paper_trader.print_summary()

        # Sync shared state untuk cmd_handler
        self._update_bot_state()

        self.cycle_count += 1
        print(f"\n✅ Cycle {self.cycle_count} complete. {len(signals)} signal(s)")

    def run(self, cycles: int = 10):
        try:
            for _ in range(cycles):
                self.scan_and_trade()
                if self.cycle_count % 6 == 0:
                    self.threshold_tuner.print_status()
                    self.winrate.print_summary()
                    if self.paper_trader and telegram.bot_token != "YOUR_BOT_TOKEN_HERE":
                        stats = self.paper_trader.get_stats()
                        telegram.send_daily_summary(
                            stats['balance'], stats['total_pnl'],
                            stats['winrate'], stats['total_trades']
                        )
                if self.cycle_count < cycles:
                    print(f"\n⏳ Waiting 30 seconds...")
                    time.sleep(30)
        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped")
            if telegram.bot_token != "YOUR_BOT_TOKEN_HERE":
                telegram.send_message("🛑 SNAP Bot stopped")
        finally:
            self.shutdown()

    def shutdown(self):
        bot_state['status'] = 'stopped'
        print("\n" + "=" * 60)
        print("📊 FINAL SUMMARY")
        print("=" * 60)
        print(f"   Total Cycles: {self.cycle_count}")
        if self.paper_mode and self.paper_trader:
            stats = self.paper_trader.get_stats()
            print(f"   Final Balance: ${stats['balance']:.4f}")
            print(f"   Total PnL:     ${stats['total_pnl']:+.4f}")
            print(f"   Total Trades:  {stats['total_trades']}")
            print(f"   Winrate:       {stats['winrate']}%")
            if telegram.bot_token != "YOUR_BOT_TOKEN_HERE":
                telegram.send_message(
                    f"📊 SNAP Bot Stopped\n"
                    f"Balance: ${stats['balance']:.4f}\n"
                    f"PnL: ${stats['total_pnl']:+.4f}"
                )
        print("=" * 60)
        self.db.close()


def main():
    print("=" * 60)
    print("SNAP v1.0 - Polymarket Trading Bot")
    print("=" * 60)

    choice = input("\nMode (1=SAFE / 2=AGGRESSIVE, default 2): ").strip()
    mode   = "SAFE" if choice == "1" else "AGGRESSIVE"

    try:
        cycles = int(input("Jumlah scan cycle (default 3): ").strip() or "3")
    except:
        cycles = 3

    reset = input("Reset stale positions? (y/n, default y): ").strip().lower()
    if reset != 'n':
        reset_stale_positions("snap_bot_data.db")

    bot = SnapBot(mode=mode, paper_mode=True)
    bot.run(cycles=cycles)


if __name__ == "__main__":
    main()