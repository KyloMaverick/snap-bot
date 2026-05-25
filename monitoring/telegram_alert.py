"""
TELEGRAM ALERT
Kirim notifikasi ke Telegram saat ada sinyal trade
"""

import requests
from datetime import datetime

class TelegramAlert:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        # Ganti dengan token dan chat ID lo
        self.bot_token = bot_token or "8967861560:AAEGe_Y4Jqn7BB0WIpgYnvlm8eIFjQcPVu8"
        self.chat_id = chat_id or "5121494147"
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, message: str) -> bool:
        """Kirim pesan ke Telegram"""
        if self.bot_token == "YOUR_BOT_TOKEN_HERE":
            print("⚠️ Telegram not configured. Set bot_token and chat_id")
            return False
        
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
            print(f"⚠️ Failed to send Telegram alert: {e}")
            return False
    
    def send_trade_signal(self, market_question: str, side: str, size: float, 
                          entry_price: float, edge: float, confidence: str):
        """Kirim alert untuk sinyal trade"""
        
        emoji = "🟢" if side == "BUY" else "🔴"
        message = f"""
{emoji} <b>NEW TRADE SIGNAL!</b>

<b>Market:</b> {market_question[:60]}...
<b>Action:</b> {side} YES
<b>Size:</b> ${size:.2f}
<b>Entry:</b> {entry_price:.3f} ({entry_price*100:.1f}%)
<b>Edge:</b> {edge:+.2f}%
<b>Confidence:</b> {confidence}

<b>TP:</b> +3% | <b>SL:</b> -3%
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message)
    
    def send_trade_result(self, market_question: str, side: str, pnl: float, 
                          pnl_pct: float, exit_reason: str):
        """Kirim alert hasil trade"""
        
        emoji = "✅" if pnl > 0 else "❌"
        message = f"""
{emoji} <b>TRADE CLOSED!</b>

<b>Market:</b> {market_question[:50]}...
<b>Action:</b> {side}
<b>PnL:</b> {pnl:+.2f} ({pnl_pct:+.1f}%)
<b>Reason:</b> {exit_reason}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message)
    
    def send_daily_summary(self, balance: float, total_pnl: float, 
                           winrate: float, trades: int):
        """Kirim ringkasan harian"""
        
        emoji = "📈" if total_pnl > 0 else "📉"
        message = f"""
{emoji} <b>DAILY SUMMARY</b>

<b>Balance:</b> ${balance:.2f}
<b>Total PnL:</b> ${total_pnl:+.2f}
<b>Winrate:</b> {winrate}%
<b>Total Trades:</b> {trades}
<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}
"""
        self.send_message(message)


# Instance global
telegram = TelegramAlert()