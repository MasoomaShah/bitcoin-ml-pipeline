"""
Simple Discord Webhook Test - No Dependencies Required
"""

import os
import json

def test_discord_webhook():
    """Test Discord webhook with simple requests"""
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL not set")
        print("\nTo set it:")
        print('$env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"')
        return False
    
    print(f"✓ Webhook URL found: {webhook_url[:50]}...")
    
    try:
        import requests
        
        # Simple message
        print("\n[1] Sending simple test message...")
        response = requests.post(
            webhook_url,
            json={'content': '✅ Test message from Bitcoin ML Pipeline!'}
        )
        
        if response.status_code in [200, 204]:
            print("✓ Simple message sent successfully!")
        else:
            print(f"✗ Failed: {response.status_code}")
            return False
        
        # Rich embedded message
        print("\n[2] Sending rich embedded message...")
        response = requests.post(
            webhook_url,
            json={
                'embeds': [{
                    'title': '🤖 Bitcoin ML Pipeline',
                    'description': 'Testing Discord notifications',
                    'color': 0x00ff00,  # Green
                    'fields': [
                        {'name': 'Status', 'value': '✅ Working', 'inline': True},
                        {'name': 'Model', 'value': 'Prophet', 'inline': True},
                        {'name': 'Accuracy', 'value': 'R² = 0.4504', 'inline': True}
                    ],
                    'footer': {'text': 'ML Pipeline Bot'}
                }]
            }
        )
        
        if response.status_code in [200, 204]:
            print("✓ Rich message sent successfully!")
        else:
            print(f"✗ Failed: {response.status_code}")
            return False
        
        print("\n✅ Discord webhook is working perfectly!")
        print("Check your Discord channel for the messages!")
        return True
        
    except ImportError:
        print("✗ requests library not installed")
        print("Install with: pip install requests")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("="*70)
    print("DISCORD WEBHOOK TEST")
    print("="*70)
    print("\nThis tests if Discord notifications are working")
    print("\nMake sure you've set your webhook URL:")
    print('  $env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."')
    print("\n" + "="*70 + "\n")
    
    test_discord_webhook()
