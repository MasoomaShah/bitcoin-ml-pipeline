"""
Helper function to send Discord notifications from any script
"""

import os
import requests
from datetime import datetime


def send_discord_notification(message, title="ML Pipeline Notification", color="green", fields=None):
    """
    Send a notification to Discord
    
    Args:
        message: Main message text
        title: Title of the notification
        color: "green" (success), "red" (error), "orange" (warning), or hex code
        fields: List of {'name': 'Field Name', 'value': 'Field Value'} dicts
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("⚠️  DISCORD_WEBHOOK_URL not set, skipping notification")
        return False
    
    # Color mapping
    colors = {
        'green': 0x00ff00,
        'red': 0xff0000,
        'orange': 0xffa500,
        'blue': 0x0000ff
    }
    
    color_code = colors.get(color.lower(), color if isinstance(color, int) else 0x00ff00)
    
    # Build embed
    embed = {
        'title': title,
        'description': message,
        'color': color_code,
        'timestamp': datetime.utcnow().isoformat(),
        'footer': {'text': 'Bitcoin ML Pipeline'}
    }
    
    if fields:
        embed['fields'] = fields
    
    try:
        response = requests.post(
            webhook_url,
            json={'embeds': [embed]},
            timeout=10
        )
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"⚠️  Failed to send Discord notification: {e}")
        return False


# Example usage
if __name__ == "__main__":
    # Success notification
    send_discord_notification(
        message="Model training completed successfully!",
        title="✅ Training Complete",
        color="green",
        fields=[
            {'name': 'Accuracy', 'value': '72.34%', 'inline': True},
            {'name': 'R² Score', 'value': '0.4504', 'inline': True},
            {'name': 'Duration', 'value': '45.2s', 'inline': True}
        ]
    )
    
    # Error notification
    send_discord_notification(
        message="Model training failed with error",
        title="❌ Training Failed",
        color="red",
        fields=[
            {'name': 'Error', 'value': 'Connection timeout', 'inline': False}
        ]
    )
    
    # Warning notification
    send_discord_notification(
        message="Data drift detected in recent samples",
        title="⚠️ Warning",
        color="orange",
        fields=[
            {'name': 'Severity', 'value': 'Medium', 'inline': True},
            {'name': 'Affected Features', 'value': '3', 'inline': True}
        ]
    )
