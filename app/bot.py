import asyncio
import subprocess
import re
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import config
from collector import collect_all, collect_ping
from db import get_connection, init_db


def auth_only(func):
    """Decorator — ignore messages not from the configured chat."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.id != config.TELEGRAM_CHAT_ID:
            return
        await func(update, context)
    return wrapper


def format_bytes(b: int) -> str:
    if b >= 1_000_000_000:
        return f"{b / 1_000_000_000:.1f} GB"
    if b >= 1_000_000:
        return f"{b / 1_000_000:.1f} MB"
    return f"{b / 1_000:.1f} KB"


# ── /usage ──────────────────────────────────────────────────────────────────

@auth_only
async def cmd_usage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        import json
        result = subprocess.run(
            ["vnstat", "-i", config.NETWORK_INTERFACE, "--json", "m", "1"],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        month = data["interfaces"][0]["traffic"]["month"]

        if not month:
            await update.message.reply_text("No data yet, wait a few minutes.")
            return

        latest = month[-1]
        rx: int = latest["rx"]
        tx: int = latest["tx"]
        total: int = rx + tx
        month_name = datetime.now().strftime("%B %Y")

        text = (
            f"📊 Usage — {month_name}\n"
            f"↓ Download : {format_bytes(rx)}\n"
            f"↑ Upload   : {format_bytes(tx)}\n"
            f"⬡ Total    : {format_bytes(total)}"
        )
        await update.message.reply_text(text)

    except Exception as e:
        await update.message.reply_text(f"Error fetching usage: {e}")


# ── /daily ───────────────────────────────────────────────────────────────────

@auth_only
async def cmd_daily(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT date(timestamp) as day, MIN(rx_bytes) as rx_min, MAX(rx_bytes) as rx_max, "
                "MIN(tx_bytes) as tx_min, MAX(tx_bytes) as tx_max "
                "FROM traffic WHERE timestamp >= ? GROUP BY day ORDER BY day DESC LIMIT 7",
                (cutoff,)
            ).fetchall()

        if not rows:
            await update.message.reply_text("No data yet, wait a few minutes.")
            return

        lines = ["📅 Daily Usage (last 7 days)"]
        for row in rows:
            rx_delta = max(0, row["rx_max"] - row["rx_min"])
            tx_delta = max(0, row["tx_max"] - row["tx_min"])
            total = rx_delta + tx_delta
            day = datetime.strptime(row["day"], "%Y-%m-%d").strftime("%b %d")
            lines.append(f"{day} — {format_bytes(total)}")

        await update.message.reply_text("\n".join(lines))

    except Exception as e:
        await update.message.reply_text(f"Error fetching daily usage: {e}")


# ── /speed ───────────────────────────────────────────────────────────────────

@auth_only
async def cmd_speed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT strftime('%H', timestamp) as hour, "
                "AVG(rx_rate_kbps) as avg_rx, AVG(tx_rate_kbps) as avg_tx "
                "FROM traffic WHERE date(timestamp) = ? "
                "GROUP BY hour ORDER BY hour",
                (today,)
            ).fetchall()

        if not rows:
            await update.message.reply_text("No data yet for today.")
            return

        lines = ["⚡ Speed Today (hourly avg)"]
        for row in rows:
            rx_mbps = row["avg_rx"] / 1000
            tx_mbps = row["avg_tx"] / 1000
            lines.append(f"{row['hour']}:00  ↓ {rx_mbps:.1f} Mbps  ↑ {tx_mbps:.1f} Mbps")

        await update.message.reply_text("\n".join(lines))

    except Exception as e:
        await update.message.reply_text(f"Error fetching speed: {e}")


# ── /slowhours ───────────────────────────────────────────────────────────────

@auth_only
async def cmd_slowhours(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT strftime('%H', timestamp) as hour, "
                "AVG(latency_ms) as avg_latency, AVG(packet_loss_pct) as avg_loss "
                "FROM ping WHERE timestamp >= ? AND latency_ms IS NOT NULL "
                "GROUP BY hour ORDER BY avg_latency DESC LIMIT 5",
                (cutoff,)
            ).fetchall()

        if not rows:
            await update.message.reply_text("No ping data yet.")
            return

        lines = ["🐢 Slowest Hours (last 7 days)"]
        for i, row in enumerate(rows, 1):
            end_hour = (int(row["hour"]) + 1) % 24
            lines.append(
                f"{i}. {row['hour']}:00–{end_hour:02d}:00  "
                f"avg {row['avg_latency']:.0f} ms  (loss {row['avg_loss']:.0f}%)"
            )

        await update.message.reply_text("\n".join(lines))

    except Exception as e:
        await update.message.reply_text(f"Error fetching slow hours: {e}")


# ── /ping ─────────────────────────────────────────────────────────────────────

@auth_only
async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        latency, packet_loss = collect_ping()

        if latency is None:
            text = (
                f"🏓 Ping — {config.PING_TARGET}\n"
                f"Latency  : timeout\n"
                f"Loss     : {packet_loss:.0f}%"
            )
        else:
            text = (
                f"🏓 Ping — {config.PING_TARGET}\n"
                f"Latency  : {latency:.1f} ms\n"
                f"Loss     : {packet_loss:.0f}%"
            )
        await update.message.reply_text(text)

    except Exception as e:
        await update.message.reply_text(f"Error running ping: {e}")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    init_db()

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("usage", cmd_usage))
    app.add_handler(CommandHandler("daily", cmd_daily))
    app.add_handler(CommandHandler("speed", cmd_speed))
    app.add_handler(CommandHandler("slowhours", cmd_slowhours))
    app.add_handler(CommandHandler("ping", cmd_ping))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(collect_all, "interval", minutes=config.COLLECT_INTERVAL_MINUTES)
    scheduler.start()

    print(f"[bot] starting — collecting every {config.COLLECT_INTERVAL_MINUTES} min")
    app.run_polling()


if __name__ == "__main__":
    main()
