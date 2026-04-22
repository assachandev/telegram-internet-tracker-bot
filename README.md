# telegram-internet-tracker-bot

A Telegram bot that monitors internet usage and network quality on a Linux server. Data is collected every 5 minutes and stored in SQLite.

## Requirements

- Docker + Docker Compose v2
- [vnstat](https://humdi.net/vnstat/) installed and running on the host
- A Telegram bot token ([create one via @BotFather](https://t.me/BotFather))

## Installation

```bash
git clone https://github.com/assachandev/telegram-internet-tracker-bot.git
cd telegram-internet-tracker-bot
bash install.sh
```

The installer will:
1. Check that `docker`, `docker compose`, and `vnstat` are available
2. Create `.env` from `.env.example` and prompt for your credentials
3. Build and start the bot container

## Configuration

Edit `.env` to change defaults:

| Variable | Default | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | — | Your bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | — | Your Telegram chat/user ID |
| `NETWORK_INTERFACE` | `wlp2s0` | Network interface to monitor |
| `PING_TARGET` | `8.8.8.8` | Target IP for latency checks |
| `COLLECT_INTERVAL_MINUTES` | `5` | How often to collect data |

## Commands

| Command | Description |
|---|---|
| `/usage` | Monthly download / upload / total |
| `/daily` | Traffic for the last 7 days |
| `/speed` | Hourly average speed for today |
| `/slowhours` | Top 5 slowest hours in the last 7 days |
| `/ping` | Real-time latency and packet loss |

## Notes

- The bot only responds to the configured `TELEGRAM_CHAT_ID`
- vnstat must be installed on the **host** and monitoring the correct interface
- SQLite data is persisted in `./data/` on the host
