#!/bin/bash
set -e

echo "=== telegram-internet-tracker-bot installer ==="

# Check dependencies
for cmd in docker vnstat; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: '$cmd' is not installed. Please install it first."
        exit 1
    fi
done

if ! docker compose version &>/dev/null; then
    echo "ERROR: 'docker compose' (v2) is not available."
    exit 1
fi

# Setup .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "Fill in your credentials:"
    read -rp "TELEGRAM_BOT_TOKEN: " token
    read -rp "TELEGRAM_CHAT_ID: " chat_id
    sed -i "s/your_token_here/$token/" .env
    sed -i "s/your_chat_id_here/$chat_id/" .env
    echo ".env created."
else
    echo ".env already exists, skipping."
fi

# Start
echo ""
echo "Starting bot..."
docker compose up -d --build

echo ""
echo "Done! Bot is running."
echo ""
echo "Available commands:"
echo "  /usage      — monthly traffic"
echo "  /daily      — last 7 days usage"
echo "  /speed      — hourly speed today"
echo "  /slowhours  — slowest 5 hours (last 7 days)"
echo "  /ping       — real-time ping"
