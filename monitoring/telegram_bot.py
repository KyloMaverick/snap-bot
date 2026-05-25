import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

class TelegramMenuBot:
    def __init__(self, token: str, snap_bot):
        self.token = token
        self.snap_bot = snap_bot
        self.app = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 *SNAP BOT AKTIF*\\n\\nKirim perintah:\\n"
            "/status – kondisi bot\\n"
            "/balance – saldo & profit\\n"
            "/positions – posisi terbuka\\n"
            "/pnl – ringkasan profit\\n"
            "/help – bantuan",
            parse_mode="MarkdownV2"
        )

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        stats = self.snap_bot.paper_trader.get_stats()
        msg = (
            f"✅ *STATUS BOT*\\n"
            f"Mode: {self.snap_bot.mode}\\n"
            f"Balance: ${stats['balance']:.2f}\\n"
            f"Open positions: {stats['open_positions']}\\n"
            f"Winrate: {stats['winrate']}%"
        )
        await update.message.reply_text(msg, parse_mode="MarkdownV2")

    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        stats = self.snap_bot.paper_trader.get_stats()
        msg = (
            f"💰 *BALANCE*\\n"
            f"Saldo: ${stats['balance']:.2f}\\n"
            f"Total PnL: ${stats['total_pnl']:+.2f}"
        )
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
            f"📊 *PNL REPORT*\\n"
            f"Realized PnL: ${stats['total_pnl']:+.2f}\\n"
            f"Winrate: {stats['winrate']}%\\n"
            f"Wins/Losses: {stats['winning_trades']}/{stats['losing_trades']}"
        )
        await update.message.reply_text(msg, parse_mode="MarkdownV2")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.start(update, context)

    async def set_menu_commands(self):
        if not self.app:
            return
        commands = [
            BotCommand("start", "Mulai dan lihat status"),
            BotCommand("status", "Status bot & balance"),
            BotCommand("balance", "Lihat saldo"),
            BotCommand("positions", "Lihat posisi terbuka"),
            BotCommand("pnl", "Lihat profit/loss"),
            BotCommand("help", "Bantuan"),
        ]
        await self.app.bot.set_my_commands(commands)

    def run(self):
        if not self.token or self.token == "YOUR_BOT_TOKEN_HERE":
            print("⚠️ Telegram token tidak dikonfigurasi")
            return

        self.app = Application.builder().token(self.token).build()
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("status", self.status))
        self.app.add_handler(CommandHandler("balance", self.balance))
        self.app.add_handler(CommandHandler("positions", self.positions))
        self.app.add_handler(CommandHandler("pnl", self.pnl))
        self.app.add_handler(CommandHandler("help", self.help))

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.set_menu_commands())
        loop.run_until_complete(self.app.initialize())
        loop.run_until_complete(self.app.start())

        print("✅ Telegram menu bot aktif (polling)")
        loop.run_forever()