import json
import re
import subprocess
from datetime import datetime, timezone

from config import NETWORK_INTERFACE, PING_TARGET
from db import get_connection


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

        return latency, packet_loss

    except Exception as e:
        print(f"[collector] ping error: {e}")
        return None, 100.0


def collect_all() -> None:
    collect_traffic()
    collect_ping()
