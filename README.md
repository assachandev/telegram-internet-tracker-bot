<div align="center">

# telegram-internet-tracker-bot

A self-hosted Telegram bot that monitors internet usage and network quality on a Linux server. Collects traffic and latency data every 5 minutes and sends automatic alerts when something goes wrong.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-v21+-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://github.com/python-telegram-bot/python-telegram-bot)
[![License](https://img.shields.io/badge/License-MIT-6B7280?style=flat-square)](LICENSE)

</div>

---

## Features

- **Traffic monitoring** — tracks download / upload via vnstat, stored in SQLite
- **Latency tracking** — pings a target every N minutes and records latency + packet loss
- **Auto alerts** — sends a Telegram message when latency or packet loss exceeds thresholds
- **Reply keyboard** — button-based interface, no need to type commands
- **Single-user auth** — only your Telegram chat ID can interact with the bot

---

## Tech Stack

| | Tool |
|-|------|
| Language | Python 3.11+ |
| Telegram | python-telegram-bot v21+ |
| Traffic data | vnstat 2.x |
| Storage | SQLite |
| Runtime | Docker |

---

## Project Structure

```
telegram-internet-tracker-bot/
├── Dockerfile
├── docker-compose.yml
├── install.sh
├── .env.example
└── app/
    ├── bot.py          # Commands, keyboard, alert routing
    ├── collector.py    # Traffic + ping collection and alert logic
    ├── db.py           # SQLite init and connection
    ├── config.py       # Env vars
    └── requirements.txt
```

---

## Setup

### 1. Clone

```bash
git clone https://github.com/assachandev/telegram-internet-tracker-bot.git
cd telegram-internet-tracker-bot
```

---

### 2. Configure

```bash
cp .env.example .env
nano .env
```

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | From [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | — | Your chat ID — from [@userinfobot](https://t.me/userinfobot) |
| `NETWORK_INTERFACE` | `wlp2s0` | Network interface to monitor |
| `PING_TARGET` | `8.8.8.8` | Target IP for latency checks |
| `COLLECT_INTERVAL_MINUTES` | `5` | How often to collect data |
| `ALERT_LATENCY_MS` | `150` | Alert threshold for latency (ms) |
| `ALERT_LOSS_PCT` | `10` | Alert threshold for packet loss (%) |
| `ALERT_COOLDOWN_MINUTES` | `30` | Minimum time between alerts |

---

### 3. Run

```bash
bash install.sh
```

The installer checks dependencies, fills in `.env`, builds and starts the container.

Logs: `docker compose logs -f`

---

## Interface

```
[ 📋 Status  ] [ 🏓 Ping      ]
[ 📊 Usage   ] [ 📅 Daily     ]
[       🐢 Slow Hours        ]
```

| Button | Description |
|---|---|
| 📋 Status | Current ping + today's and monthly traffic at a glance |
| 🏓 Ping | Real-time latency and packet loss |
| 📊 Usage | Monthly download / upload / total |
| 📅 Daily | Traffic for the last 7 days |
| 🐢 Slow Hours | Top 5 slowest hours in the last 7 days |

---

## Alerts

The bot automatically notifies you when network quality drops:

```
⚠️ Network Alert
High latency: 320 ms  (threshold: 150 ms)
Packet loss: 15%  (threshold: 10%)
Time: 21:43 UTC
```

Alerts are rate-limited by `ALERT_COOLDOWN_MINUTES` to avoid spam.

---

## License

[MIT](LICENSE)
