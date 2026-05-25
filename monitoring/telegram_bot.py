"""
TELEGRAM BOT COMMANDS
Menerima perintah dari user dan membalas dengan info bot
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import threading
from datetime import datetime

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    TELEGRAM_LIB_AVAILABLE = True
except ImportError:
    TELEGRAM_LIB_AVAILABLE = False
    print("⚠️ python-telegram-bot not installed. Run: pip install python-telegram-bot")

# Import komponen bot
from main import SnapBot
from monitoring.telegram_alert import telegram
from filters.stage4_risk import get_risk_checker


class TelegramCommandBot:
    def __init__(self, bot_token: str, snap_bot: SnapBot):
        self.bot_token = bot_token
        self.snap_bot = snap_bot
        self.application = None
        self.running = False
    
    def start_bot(self):
        """Mulai Telegram bot di thread terpisah"""
        if not TELEGRAM_LIB_AVAILABLE:
            print("⚠️ Cannot start Telegram bot: library not installed")
            return
        
        self.application = Application.builder().token(self.bot_token).build()
        
        # Register command handlers
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("status", self.cmd_status))
        self.application.add_handler(CommandHandler("balance", self.cmd_balance))
        self.application.add_handler(CommandHandler("positions", self.cmd_positions))
        self.application.add_handler(CommandHandler("pnl", self.cmd_pnl))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("refresh", self.cmd_refresh))
        
        # Start polling di background
        self.running = True
        thread = threading.Thread(target=self._run_polling, daemon=True)
        thread.start()
        print("✅ Telegram command bot started")
    
    def _run_polling(self):
        """Jalankan polling di background"""
        try:
            self.application.run_polling(allowed_updates=["message"])
        except Exception as e:
            print(f"⚠️ Telegram polling error: {e}")
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/start - Menampilkan pesan selamat datang"""
        welcome_msg = """
🤖 <b>SNAP BOT - Telegram Controller</b>

Bot ini untuk monitoring dan kontrol bot trading Polymarket.

<b>Commands yang tersedia:</b>
/status - Status bot (running/offline)
/balance - Lihat balance saat ini
/positions - Lihat open positions
/pnl - Lihat profit/loss hari ini
/refresh - Refresh data terbaru
/help - Bantuan

<b>Status:</b> 🟢 ONLINE
"""
        await update.message.reply_text(welcome_msg, parse_mode='HTML')
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/status - Cek status bot"""
        risk_checker = get_risk_checker()
        
        # Cek apakah bot jalan (selalu true karena di Railway)
        status = "🟢 ONLINE"
        
        # Dapatkan stats dari paper trader
        stats = self.snap_bot.paper_trader.get_stats() if self.snap_bot.paper_trader else {}
        
        msg = f"""
<b>🤖 SNAP BOT STATUS</b>

Status: {status}
Mode: {self.snap_bot.mode}
Paper Mode: {'ON' if self.snap_bot.paper_mode else 'OFF'}

<b>Balance:</b> ${stats.get('balance', 0):.2f}
<b>Open Positions:</b> {stats.get('open_positions', 0)}
<b>Total Trades:</b> {stats.get('total_trades', 0)}
<b>Winrate:</b> {stats.get('winrate', 0)}%

⏰ Last update: {datetime.now().strftime('%H:%M:%S')}
"""
        await update.message.reply_text(msg, parse_mode='HTML')
    
    async def cmd_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/balance - Lihat balance"""
        stats = self.snap_bot.paper_trader.get_stats() if self.snap_bot.paper_trader else {}
        
        msg = f"""
💰 <b>BALANCE INFO</b>

<b>Current Balance:</b> ${stats.get('balance', 0):.2f}
<b>Total PnL:</b> ${stats.get('total_pnl', 0):+.2f}
<b>PnL %:</b> {stats.get('total_pnl_pct', 0):+.1f}%
<b>Open Positions:</b> {stats.get('open_positions', 0)}
<b>Total Trades:</b> {stats.get('total_trades', 0)}
"""
        await update.message.reply_text(msg, parse_mode='HTML')
    
    async def cmd_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/positions - Lihat open positions"""
        if self.snap_bot.paper_trader and self.snap_bot.paper_trader.open_positions:
            msg = "📊 <b>OPEN POSITIONS</b>\n\n"
            for i, pos in enumerate(self.snap_bot.paper_trader.open_positions, 1):
                msg += f"""
{i}. {pos['market_question'][:40]}...
   <b>Side:</b> {pos['side']}
   <b>Size:</b> ${pos['size']:.2f}
   <b>Entry:</b> {pos['entry_price']:.3f}
   <b>TP:</b> {pos['take_profit']:.3f}
   <b>SL:</b> {pos['stop_loss']:.3f}
   <b>Open since:</b> {pos['entry_time'].strftime('%H:%M')}
"""
        else:
            msg = "📭 <b>No open positions</b>"
        
        await update.message.reply_text(msg, parse_mode='HTML')
    
    async def cmd_pnl(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/pnl - Lihat profit/loss"""
        stats = self.snap_bot.paper_trader.get_stats() if self.snap_bot.paper_trader else {}
        
        # Hitung performa hari ini
        daily_pnl = self.snap_bot.risk_checker.daily_pnl if hasattr(self.snap_bot, 'risk_checker') else 0
        
        msg = f"""
📈 <b>PROFIT / LOSS REPORT</b>

<b>Total PnL:</b> ${stats.get('total_pnl', 0):+.2f}
<b>Total PnL %:</b> {stats.get('total_pnl_pct', 0):+.1f}%
<b>Today's PnL:</b> {daily_pnl:+.2f}%

<b>Winrate:</b> {stats.get('winrate', 0)}%
<b>Wins/Losses:</b> {stats.get('winning_trades', 0)}/{stats.get('losing_trades', 0)}
<b>Total Trades:</b> {stats.get('total_trades', 0)}
"""
        await update.message.reply_text(msg, parse_mode='HTML')
    
    async def cmd_refresh(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/refresh - Refresh data"""
        await update.message.reply_text("🔄 Refreshing data...")
        # Force one scan cycle
        self.snap_bot.scan_and_trade()
        await update.message.reply_text("✅ Data refreshed! Use /status to see updates.")
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/help - Bantuan"""
        help_msg = """
🤖 <b>SNAP BOT - Command Help</b>

/start - Welcome message
/status - Bot status (online, mode, balance)
/balance - Current balance
/positions - Open positions list
/pnl - Profit/Loss report
/refresh - Force refresh data
/help - This message

<b>Tips:</b>
• Bot auto-scan setiap 30 detik
• Notifikasi trade akan otomatis terkirim
• Gunakan /refresh untuk update manual
"""
        await update.message.reply_text(help_msg, parse_mode='HTML')


def start_telegram_bot(snap_bot: SnapBot):
    """Start Telegram command bot"""
    if telegram.bot_token and telegram.bot_token != "YOUR_BOT_TOKEN_HERE":
        cmd_bot = TelegramCommandBot(telegram.bot_token, snap_bot)
        cmd_bot.start_bot()
        return cmd_bot
    else:
        print("⚠️ Telegram token not configured, command bot disabled")
        return None