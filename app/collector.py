import json
import re
import subprocess
from datetime import datetime, timezone, timedelta

import requests

import config
from config import NETWORK_INTERFACE, PING_TARGET
from db import get_connection

_last_alert_time: datetime | None = None


def _send_alert(text: str) -> None:
    global _last_alert_time
    now = datetime.now(timezone.utc)
    if _last_alert_time and (now - _last_alert_time) < timedelta(minutes=config.ALERT_COOLDOWN_MINUTES):
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": config.TELEGRAM_CHAT_ID, "text": text},
            timeout=10,
        )
        _last_alert_time = now
    except Exception as e:
        print(f"[collector] alert error: {e}")


def collect_traffic() -> None:
    try:
        result = subprocess.run(
            ["vnstat", "-i", NETWORK_INTERFACE, "--json", "5"],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        five_min = data["interfaces"][0]["traffic"]["fiveminute"]

        if not five_min:
            return

        latest = five_min[-1]
        rx_bytes: int = latest["rx"]
        tx_bytes: int = latest["tx"]
        # vnstat 5-min entries are totals for that interval, convert to rate
        rx_rate_kbps: float = (rx_bytes * 8) / (5 * 60 * 1000)
        tx_rate_kbps: float = (tx_bytes * 8) / (5 * 60 * 1000)

        # cumulative totals from month entry
        month_data = data["interfaces"][0]["traffic"]["month"]
        if month_data:
            latest_month = month_data[-1]
            rx_cumulative: int = latest_month["rx"]
            tx_cumulative: int = latest_month["tx"]
        else:
            rx_cumulative = rx_bytes
            tx_cumulative = tx_bytes

        timestamp = datetime.now(timezone.utc).isoformat()
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO traffic (timestamp, rx_bytes, tx_bytes, rx_rate_kbps, tx_rate_kbps) VALUES (?, ?, ?, ?, ?)",
                (timestamp, rx_cumulative, tx_cumulative, rx_rate_kbps, tx_rate_kbps)
            )
            conn.commit()

    except Exception as e:
        print(f"[collector] traffic error: {e}")


def collect_ping() -> tuple[float | None, float]:
    try:
        result = subprocess.run(
            ["ping", "-c", "5", PING_TARGET],
            capture_output=True, text=True, timeout=15
        )
        output = result.stdout

        loss_match = re.search(r"(\d+(?:\.\d+)?)% packet loss", output)
        packet_loss: float = float(loss_match.group(1)) if loss_match else 100.0

        latency_match = re.search(r"rtt min/avg/max[^=]+=\s*[\d.]+/([\d.]+)/", output)
        latency: float | None = float(latency_match.group(1)) if latency_match else None

        timestamp = datetime.now(timezone.utc).isoformat()
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO ping (timestamp, latency_ms, packet_loss_pct) VALUES (?, ?, ?)",
                (timestamp, latency, packet_loss)
            )
            conn.commit()

        _check_and_alert(latency, packet_loss)
        return latency, packet_loss

    except Exception as e:
        print(f"[collector] ping error: {e}")
        return None, 100.0


def _check_and_alert(latency: float | None, packet_loss: float) -> None:
    issues = []
    if latency is None:
        issues.append("Internet is unreachable (ping timeout)")
    elif latency > config.ALERT_LATENCY_MS:
        issues.append(f"High latency: {latency:.0f} ms  (threshold: {config.ALERT_LATENCY_MS:.0f} ms)")
    if packet_loss > config.ALERT_LOSS_PCT:
        issues.append(f"Packet loss: {packet_loss:.0f}%  (threshold: {config.ALERT_LOSS_PCT:.0f}%)")

    if issues:
        time_str = datetime.now(timezone.utc).strftime("%H:%M UTC")
        text = "⚠️ Network Alert\n" + "\n".join(issues) + f"\nTime: {time_str}"
        _send_alert(text)


def collect_all() -> None:
    collect_traffic()
    collect_ping()
