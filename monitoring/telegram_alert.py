"""
TELEGRAM ALERT - FULL VERSION
Kirim semua informasi: sinyal, hasil trade, open positions, daily summary
"""

import requests
from datetime import datetime
from typing import Dict, List
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class TelegramAlert:
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, message: str) -> bool:
        """Kirim pesan ke Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"⚠️ Telegram error: {e}")
            return False
    
    def send_trade_signal(self, market_question: str, side: str, size: float, 
                          entry_price: float, edge: float, confidence: str, 
                          balance: float, balance_before: float):
        """Kirim alert untuk sinyal trade BARU"""
        
        emoji = "🟢" if side == "BUY" else "🔴"
        size_pct = (size / balance_before) * 100 if balance_before > 0 else 0
        
        message = f"""
{emoji} <b>🔥 NEW TRADE SIGNAL!</b>

📌 <b>Market:</b> {market_question[:60]}...
📊 <b>Action:</b> {side} YES
💰 <b>Size:</b> ${size:.2f} ({size_pct:.1f}% of balance)
📈 <b>Entry:</b> {entry_price:.3f} ({entry_price*100:.1f}%)
⚡ <b>Edge:</b> {edge:+.2f}%
🎯 <b>Confidence:</b> {confidence}

<b>Target:</b> {self._get_target_price(side, entry_price)}
<b>Stop Loss:</b> {self._get_sl_price(side, entry_price)}

💰 <b>Balance BEFORE:</b> ${balance_before:.2f}
💰 <b>Balance AFTER:</b> ${balance:.2f}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message)
    
    def _get_target_price(self, side: str, entry_price: float) -> str:
        if side == "BUY":
            target = entry_price * 1.03
            return f"{target:.3f} (+3%)"
        else:
            target = entry_price * 0.97
            return f"{target:.3f} (+3%)"
    
    def _get_sl_price(self, side: str, entry_price: float) -> str:
        if side == "BUY":
            sl = entry_price * 0.97
            return f"{sl:.3f} (-3%)"
        else:
            sl = entry_price * 1.03
            return f"{sl:.3f} (-3%)"
    
    def send_trade_result(self, market_question: str, side: str, pnl: float, 
                          pnl_pct: float, exit_reason: str, exit_price: float,
                          balance: float):
        """Kirim alert hasil trade yang sudah closed"""
        
        emoji = "✅" if pnl > 0 else "❌"
        reason_emoji = {
            "TAKE_PROFIT": "🎯",
            "STOP_LOSS": "🛑",
            "TIME_EXIT_24H": "⏰"
        }.get(exit_reason, "📊")
        
        message = f"""
{emoji} <b>TRADE CLOSED!</b> {reason_emoji}

📌 <b>Market:</b> {market_question[:50]}...
📊 <b>Action:</b> {side}
💰 <b>PnL:</b> {pnl:+.2f} ({pnl_pct:+.1f}%)
📈 <b>Exit Price:</b> {exit_price:.4f}
📋 <b>Reason:</b> {exit_reason}

💰 <b>Current Balance:</b> ${balance:.2f}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message)
    
    def send_open_positions(self, positions: List[Dict], balance: float):
        """Kirim daftar posisi yang masih terbuka"""
        
        if not positions:
            message = f"""
📭 <b>NO OPEN POSITIONS</b>
💰 <b>Balance:</b> ${balance:.2f}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            self.send_message(message)
            return
        
        total_risk = sum(p['size'] for p in positions)
        risk_pct = (total_risk / balance) * 100 if balance > 0 else 0
        
        message = f"""
📊 <b>OPEN POSITIONS ({len(positions)})</b>
💰 <b>Total Risk:</b> ${total_risk:.2f} ({risk_pct:.1f}% of balance)
"""
        for i, pos in enumerate(positions[:5], 1):
            message += f"""
{i}. {pos['market_question'][:35]}...
   {pos['side']} @ {pos['entry_price']:.3f}
   Size: ${pos['size']:.2f}
   TP: {pos.get('take_profit', 0):.3f} | SL: {pos.get('stop_loss', 0):.3f}
"""
        self.send_message(message)
    
    def send_daily_summary(self, balance: float, total_pnl: float, 
                           winrate: float, trades: int, winning_trades: int,
                           losing_trades: int, total_pnl_pct: float,
                           open_positions: int):
        """Kirim ringkasan harian"""
        
        emoji = "📈" if total_pnl > 0 else "📉"
        message = f"""
{emoji} <b>DAILY SUMMARY</b>
💰 <b>Balance:</b> ${balance:.2f}
📊 <b>Today's PnL:</b> ${total_pnl:+.2f} ({total_pnl_pct:+.1f}%)
🎯 <b>Winrate:</b> {winrate}% ({winning_trades}/{trades})
📋 <b>Trades:</b> {trades}
✅ <b>Wins:</b> {winning_trades}
❌ <b>Losses:</b> {losing_trades}
📂 <b>Open Positions:</b> {open_positions}
📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}
"""
        self.send_message(message)
    
    def send_startup(self, mode: str, paper_mode: bool, balance: float):
        message = f"""
🤖 <b>SNAP BOT STARTED!</b>
⚙️ <b>Mode:</b> {mode}
📝 <b>Paper Mode:</b> {'ON' if paper_mode else 'OFF'}
💰 <b>Initial Balance:</b> ${balance:.2f}
⏰ <b>Start Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message)
    
    def send_shutdown(self, final_balance: float, total_pnl: float, total_trades: int):
        message = f"""
🛑 <b>SNAP BOT SHUTDOWN</b>
💰 <b>Final Balance:</b> ${final_balance:.2f}
📊 <b>Total PnL:</b> ${total_pnl:+.2f}
📋 <b>Total Trades:</b> {total_trades}
⏰ <b>End Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message)


telegram = TelegramAlert()