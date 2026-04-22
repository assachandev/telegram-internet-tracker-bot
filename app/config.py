import os

TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID: int = int(os.environ["TELEGRAM_CHAT_ID"])
NETWORK_INTERFACE: str = os.getenv("NETWORK_INTERFACE", "wlp2s0")
PING_TARGET: str = os.getenv("PING_TARGET", "8.8.8.8")
COLLECT_INTERVAL_MINUTES: int = int(os.getenv("COLLECT_INTERVAL_MINUTES", "5"))
DB_PATH: str = "/app/data/tracker.db"
ALERT_LATENCY_MS: float = float(os.getenv("ALERT_LATENCY_MS", "150"))
ALERT_LOSS_PCT: float = float(os.getenv("ALERT_LOSS_PCT", "10"))
ALERT_COOLDOWN_MINUTES: int = int(os.getenv("ALERT_COOLDOWN_MINUTES", "30"))
