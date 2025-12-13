#!/bin/bash
# Test Discord webhook notification
# Secret should be named DISCORD_WEBHOOK in GitHub

WEBHOOK_URL="${DISCORD_WEBHOOK}"

if [ -z "$WEBHOOK_URL" ]; then
    echo "❌ DISCORD_WEBHOOK_URL not set!"
    echo "Set it in GitHub Settings → Secrets and variables → Actions"
    exit 1
fi

echo "🔔 Testing Discord webhook..."

curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Bitcoin ML Pipeline",
    "avatar_url": "https://bitcoin.org/img/icons/logo.png",
    "embeds": [
      {
        "title": "✅ Test Discord Notification",
        "description": "If you see this, Discord notifications are working!",
        "color": 3066993,
        "fields": [
          {
            "name": "Status",
            "value": "✅ Webhook Connected",
            "inline": true
          }
        ],
        "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
      }
    ]
  }'

echo ""
echo "✅ Test message sent!"
