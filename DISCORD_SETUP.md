# Discord Webhook Setup Guide

## Quick Setup (3 steps)

### Step 1: Create Discord Webhook

1. Open Discord Desktop or Web App
2. Go to your server
3. Click on Server Name → Server Settings
4. Go to **Integrations** → **Webhooks**
5. Click **"New Webhook"** or **"Create Webhook"**
6. Give it a name (e.g., "ML Pipeline Bot")
7. Select the channel where you want notifications
8. Click **"Copy Webhook URL"**

### Step 2: Set Environment Variable

**In PowerShell:**
```powershell
$env:DISCORD_WEBHOOK_URL = "PASTE_YOUR_WEBHOOK_URL_HERE"
```

**Example:**
```powershell
$env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/123456789/abcdefghijklmnopqrstuvwxyz"
```

### Step 3: Verify

```powershell
# Check it's set
echo $env:DISCORD_WEBHOOK_URL

# Should output your webhook URL
```

## Test Notification

Run this to test your webhook:

```powershell
python -c "import requests; requests.post('$env:DISCORD_WEBHOOK_URL', json={'content': '✅ Test notification from ML Pipeline!'})"
```

You should see a message in your Discord channel!

## Run Pipeline with Notifications

```powershell
# Set webhook (if not already set)
$env:DISCORD_WEBHOOK_URL = "your-webhook-url"

# Run pipeline
python test_prefect_pipeline.py
```

## What You'll Receive

### Success Notification 🎉
```
✅ ML Pipeline Completed Successfully! 🎉

Version: v20251203T120000Z
Duration: 45.23s

Regression Metrics:
- RMSE: 0.0234
- R²: 0.8956

Classification Metrics:
- Accuracy: 0.9123
- F1 Score: 0.9045

Models saved to: models/
```

### Failure Notification ❌
```
❌ ML Pipeline Failed!

Error: FileNotFoundError: Data file not found
Duration: 2.15s
Time: 2025-12-03T12:00:00

Traceback:
[Error details]
```

## Troubleshooting

### "Webhook not configured" message
- Make sure you set `$env:DISCORD_WEBHOOK_URL`
- Check the URL is valid (starts with `https://discord.com/api/webhooks/`)

### No message in Discord
- Verify the channel permissions
- Check webhook hasn't been deleted
- Try the test command above

### Want to use Slack or Email instead?
Set `$env:SLACK_WEBHOOK_URL` or `$env:EMAIL_WEBHOOK_URL` and change the notification type in the code.

## Permanent Setup (Optional)

To make the webhook persist across terminal sessions:

**Windows (System Environment Variable):**
1. Right-click "This PC" → Properties
2. Advanced System Settings → Environment Variables
3. Under "User variables", click "New"
4. Variable name: `DISCORD_WEBHOOK_URL`
5. Variable value: your webhook URL
6. Click OK, restart terminal
