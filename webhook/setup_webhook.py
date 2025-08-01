#!/usr/bin/env python3
"""
Google Drive Webhook Setup
Registers webhook notifications with Google Drive API to monitor folder changes
"""

import uuid
import json
import os
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
import time

# Configuration
DRIVE_FOLDER_ID = '1B-Xsgvy4W392yfLP4ilrzrtl8zzmEgTl'
CREDENTIALS_FILE = 'core/key.json' 
WEBHOOK_CHANNELS_FILE = 'data/webhook_channels.json'

def get_drive_service():
    """Initialize Google Drive API service"""
    try:
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ Error initializing Drive service: {e}")
        print(f"🔍 Make sure {CREDENTIALS_FILE} exists and is valid")
        return None

def save_channel_info(channel_info):
    """Save webhook channel information for management"""
    channels = load_channel_info()
    channels.append({
        **channel_info,
        'created_at': datetime.now().isoformat(),
        'status': 'active'
    })
    
    with open(WEBHOOK_CHANNELS_FILE, 'w') as f:
        json.dump(channels, f, indent=2)

def load_channel_info():
    """Load existing webhook channel information"""
    if os.path.exists(WEBHOOK_CHANNELS_FILE):
        try:
            with open(WEBHOOK_CHANNELS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def setup_drive_webhook(webhook_url, secret_token=None):
    """
    Set up Google Drive push notifications for the specified folder
    
    Args:
        webhook_url (str): Public HTTPS URL where notifications will be sent
        secret_token (str): Optional token for verification
    
    Returns:
        dict: Channel information if successful, None if failed
    """
    
    print("🔧 Setting up Google Drive webhook...")
    
    service = get_drive_service()
    if not service:
        return None
    
    try:
        # Generate unique channel ID
        channel_id = str(uuid.uuid4())
        
        # Prepare webhook channel body
        body = {
            'id': channel_id,
            'type': 'web_hook',
            'address': webhook_url,
            'payload': True  # Include resource data in notifications
        }
        
        # Add secret token if provided
        if secret_token:
            body['token'] = secret_token
        
        # Set expiration to 7 days (maximum for Drive API)
        expiration_time = int((datetime.now() + timedelta(days=7)).timestamp() * 1000)
        body['expiration'] = expiration_time
        
        print(f"📡 Registering webhook channel...")
        print(f"   Channel ID: {channel_id}")
        print(f"   Webhook URL: {webhook_url}")
        print(f"   Folder ID: {DRIVE_FOLDER_ID}")
        print(f"   Expiration: {datetime.fromtimestamp(expiration_time/1000)}")
        
        # Register the webhook with Google Drive
        response = service.files().watch(
            fileId=DRIVE_FOLDER_ID,
            body=body
        ).execute()
        
        print(f"✅ Webhook registered successfully!")
        print(f"   Resource ID: {response.get('resourceId')}")
        print(f"   Resource URI: {response.get('resourceUri')}")
        
        # Save channel information for later management
        channel_info = {
            'channel_id': response['id'],
            'resource_id': response['resourceId'],
            'resource_uri': response.get('resourceUri'),
            'webhook_url': webhook_url,
            'expiration': response.get('expiration'),
            'folder_id': DRIVE_FOLDER_ID
        }
        
        save_channel_info(channel_info)
        
        return channel_info
        
    except Exception as e:
        print(f"❌ Error setting up webhook: {e}")
        return None

def stop_webhook(channel_id, resource_id):
    """
    Stop a specific webhook channel
    
    Args:
        channel_id (str): Channel ID to stop
        resource_id (str): Resource ID from the channel
    
    Returns:
        bool: True if successful, False if failed
    """
    
    print(f"🛑 Stopping webhook channel: {channel_id}")
    
    service = get_drive_service()
    if not service:
        return False
    
    try:
        service.channels().stop(body={
            'id': channel_id,
            'resourceId': resource_id
        }).execute()
        
        print(f"✅ Webhook channel stopped successfully")
        
        # Update channel info
        channels = load_channel_info()
        for channel in channels:
            if channel['channel_id'] == channel_id:
                channel['status'] = 'stopped'
                channel['stopped_at'] = datetime.now().isoformat()
        
        with open(WEBHOOK_CHANNELS_FILE, 'w') as f:
            json.dump(channels, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"❌ Error stopping webhook: {e}")
        return False

def list_active_webhooks():
    """List all active webhook channels"""
    
    channels = load_channel_info()
    active_channels = [c for c in channels if c.get('status') == 'active']
    
    if not active_channels:
        print("📭 No active webhook channels found")
        return []
    
    print(f"📡 Active webhook channels ({len(active_channels)}):")
    for i, channel in enumerate(active_channels, 1):
        expiration = channel.get('expiration')
        if expiration:
            exp_date = datetime.fromtimestamp(int(expiration)/1000)
            exp_str = exp_date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            exp_str = "No expiration"
        
        print(f"   {i}. Channel: {channel['channel_id'][:8]}...")
        print(f"      URL: {channel['webhook_url']}")
        print(f"      Created: {channel.get('created_at', 'Unknown')}")
        print(f"      Expires: {exp_str}")
        print()
    
    return active_channels

def stop_all_webhooks():
    """Stop all active webhook channels"""
    
    channels = load_channel_info()
    active_channels = [c for c in channels if c.get('status') == 'active']
    
    if not active_channels:
        print("📭 No active webhooks to stop")
        return True
    
    print(f"🛑 Stopping {len(active_channels)} active webhook(s)...")
    
    success_count = 0
    for channel in active_channels:
        if stop_webhook(channel['channel_id'], channel['resource_id']):
            success_count += 1
    
    print(f"✅ Stopped {success_count}/{len(active_channels)} webhooks")
    return success_count == len(active_channels)

def webhook_status():
    """Show comprehensive webhook status"""
    
    print("🔍 Webhook Status Report")
    print("=" * 50)
    
    channels = load_channel_info()
    if not channels:
        print("📭 No webhook channels configured")
        return
    
    active_count = len([c for c in channels if c.get('status') == 'active'])
    stopped_count = len([c for c in channels if c.get('status') == 'stopped'])
    
    print(f"📊 Total channels: {len(channels)}")
    print(f"🟢 Active: {active_count}")
    print(f"🔴 Stopped: {stopped_count}")
    print()
    
    # Check for expiring webhooks
    now = datetime.now()
    expiring_soon = []
    
    for channel in channels:
        if channel.get('status') == 'active' and channel.get('expiration'):
            exp_time = datetime.fromtimestamp(int(channel['expiration'])/1000)
            time_left = exp_time - now
            
            if time_left.total_seconds() < 24 * 3600:  # Less than 24 hours
                expiring_soon.append((channel, time_left))
    
    if expiring_soon:
        print("⚠️ Webhooks expiring soon:")
        for channel, time_left in expiring_soon:
            hours_left = time_left.total_seconds() / 3600
            print(f"   • {channel['channel_id'][:8]}... expires in {hours_left:.1f} hours")
        print()
    
    list_active_webhooks()

def main():
    """Interactive webhook management"""
    
    print("🎯 Google Drive Webhook Manager")
    print("=" * 40)
    
    while True:
        print("\nChoose an option:")
        print("1. 🔧 Setup new webhook")
        print("2. 📡 List active webhooks")
        print("3. 🛑 Stop specific webhook")
        print("4. 🚫 Stop all webhooks")
        print("5. 📊 Show webhook status")
        print("6. 🚪 Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            print("\n🔧 Setting up new webhook...")
            webhook_url = input("Enter your webhook URL (must be HTTPS): ").strip()
            
            if not webhook_url.startswith('https://'):
                print("❌ URL must use HTTPS")
                continue
            
            secret_token = input("Enter secret token (optional, press Enter to skip): ").strip()
            if not secret_token:
                secret_token = None
            
            result = setup_drive_webhook(webhook_url, secret_token)
            if result:
                print(f"\n🎉 Webhook setup complete!")
                print(f"Your webhook will receive notifications at: {webhook_url}")
            
        elif choice == '2':
            print()
            list_active_webhooks()
            
        elif choice == '3':
            print()
            channels = list_active_webhooks()
            if channels:
                try:
                    idx = int(input("Enter webhook number to stop: ")) - 1
                    if 0 <= idx < len(channels):
                        channel = channels[idx]
                        stop_webhook(channel['channel_id'], channel['resource_id'])
                    else:
                        print("❌ Invalid webhook number")
                except ValueError:
                    print("❌ Please enter a valid number")
            
        elif choice == '4':
            confirm = input("⚠️  Stop ALL webhooks? (yes/no): ").strip().lower()
            if confirm == 'yes':
                stop_all_webhooks()
            else:
                print("❌ Cancelled")
            
        elif choice == '5':
            print()
            webhook_status()
            
        elif choice == '6':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    main() 