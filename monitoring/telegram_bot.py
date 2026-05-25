import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import threading
import asyncio

class SimpleTelegramBot:
    def __init__(self, token: str, snap_bot):
        self.token = token
        self.snap_bot = snap_bot
        self.application = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 *SNAP BOT* aktif\\n\\n"
            "/status – status bot\\n"
            "/balance – saldo\\n"
            "/positions – posisi terbuka\\n"
            "/pnl – profit/loss\\n"
            "/help – bantuan",
            parse_mode="MarkdownV2"
        )

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        stats = self.snap_bot.paper_trader.get_stats()
        msg = (
            f"✅ *STATUS*\\n"
            f"Mode: {self.snap_bot.mode}\\n"
            f"Balance: ${stats['balance']:.2f}\\n"
            f"Open: {stats['open_positions']}\\n"
            f"Winrate: {stats['winrate']}%"
        )
        await update.message.reply_text(msg, parse_mode="MarkdownV2")

    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        stats = self.snap_bot.paper_trader.get_stats()
        msg = f"💰 *BALANCE*\\nSaldo: ${stats['balance']:.2f}\\nTotal PnL: ${stats['total_pnl']:+.2f}"
        await update.message.reply_text(msg, parse_mode="MarkdownV2")

    async def positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pt = self.snap_bot.paper_trader
        if not pt.open_positions:
            await update.message.reply_text("📭 Tidak ada posisi terbuka")
            return
        text = "📌 *POSISI TERBUKA*\\n"
        for i, p in enumerate(pt.open_positions, 1):
            text += f"{i}. {p['market_question'][:40]}\\n"
            text += f"   {p['side']} | ${p['size']:.2f} @ {p['entry_price']:.3f}\\n"
        await update.message.reply_text(text, parse_mode="MarkdownV2")

    async def pnl(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        stats = self.snap_bot.paper_trader.get_stats()
        msg = (
            f"📊 *PNL*\\n"
            f"Realized PnL: ${stats['total_pnl']:+.2f}\\n"
            f"Winrate: {stats['winrate']}%\\n"
            f"Wins/Losses: {stats['winning_trades']}/{stats['losing_trades']}"
        )
        await update.message.reply_text(msg, parse_mode="MarkdownV2")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.start(update, context)

    async def set_commands(self):
        if not self.application:
            return
        await self.application.bot.set_my_commands([
            BotCommand("start", "Mulai bot"),
            BotCommand("status", "Status bot & balance"),
            BotCommand("balance", "Lihat saldo"),
            BotCommand("positions", "Lihat posisi terbuka"),
            BotCommand("pnl", "Profit/loss"),
            BotCommand("help", "Bantuan"),
        ])

    def run(self):
        if not self.token or self.token == "YOUR_BOT_TOKEN_HERE":
            print("⚠️ Telegram token tidak dikonfigurasi")
            return

        self.application = Application.builder().token(self.token).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("balance", self.balance))
        self.application.add_handler(CommandHandler("positions", self.positions))
        self.application.add_handler(CommandHandler("pnl", self.pnl))
        self.application.add_handler(CommandHandler("help", self.help))

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.set_commands())
        loop.run_until_complete(self.application.initialize())
        loop.run_until_complete(self.application.start())

        print("✅ Telegram command bot polling started")
        loop.run_forever()