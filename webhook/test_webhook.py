#!/usr/bin/env python3
"""
Test script to verify webhook functionality
"""

import requests
import json
import time
import os
from datetime import datetime

def test_webhook_server(webhook_url):
    """Test if the webhook server is running and accessible"""
    
    print("🧪 Testing webhook server...")
    
    try:
        # Test health endpoint
        health_url = webhook_url.replace('/drive-webhook', '/health')
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Server is healthy: {response.json()}")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach webhook server: {e}")
        return False

def test_webhook_endpoint(webhook_url):
    """Test the webhook endpoint with a simulated Google notification"""
    
    print("🧪 Testing webhook endpoint...")
    
    # Simulate a Google Drive notification
    headers = {
        'X-Goog-Channel-ID': 'test-channel-' + str(int(time.time())),
        'X-Goog-Channel-Token': 'test-token',
        'X-Goog-Resource-State': 'sync',
        'X-Goog-Resource-ID': 'test-resource-id',
        'X-Goog-Message-Number': '1',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(webhook_url, headers=headers, json={}, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ Webhook endpoint responded correctly")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Webhook endpoint error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing webhook endpoint: {e}")
        return False

def check_webhook_logs():
    """Check webhook server logs for recent activity"""
    
    print("📄 Checking webhook logs...")
    
    log_files = ['webhook.log', 'webhook_activity.json']
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n📄 {log_file}:")
            
            if log_file.endswith('.json'):
                try:
                    with open(log_file, 'r') as f:
                        activities = json.load(f)
                    
                    if activities:
                        print(f"   📊 Total activities: {len(activities)}")
                        
                        # Show recent activities
                        recent = activities[-5:]
                        for activity in recent:
                            timestamp = activity.get('timestamp', 'Unknown')
                            event_type = activity.get('event_type', 'Unknown')
                            print(f"   • {timestamp}: {event_type}")
                    else:
                        print("   📭 No activities logged yet")
                        
                except Exception as e:
                    print(f"   ❌ Error reading JSON log: {e}")
            
            else:
                # Text log file
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                    
                    if lines:
                        print(f"   📊 Total log lines: {len(lines)}")
                        print("   🔍 Last 5 lines:")
                        for line in lines[-5:]:
                            print(f"     {line.strip()}")
                    else:
                        print("   📭 Log file is empty")
                        
                except Exception as e:
                    print(f"   ❌ Error reading log file: {e}")
        else:
            print(f"📭 {log_file} not found")

def check_webhook_status_endpoint(webhook_url):
    """Check the webhook status endpoint"""
    
    print("📊 Checking webhook status...")
    
    try:
        status_url = webhook_url.replace('/drive-webhook', '/webhook-status')
        response = requests.get(status_url, timeout=10)
        
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Webhook status retrieved:")
            print(f"   Server time: {status_data.get('server_time')}")
            print(f"   Total activities: {status_data.get('total_activities', 0)}")
            
            recent_updates = status_data.get('recent_updates', [])
            if recent_updates:
                print(f"   📈 Recent updates: {len(recent_updates)}")
                for update in recent_updates[-3:]:
                    timestamp = update.get('details', {}).get('timestamp', 'Unknown')
                    print(f"     • {timestamp}")
            else:
                print(f"   📭 No recent updates")
                
            return True
        else:
            print(f"❌ Status endpoint error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking status: {e}")
        return False

def main():
    """Run webhook tests"""
    
    print("🧪 Google Drive Webhook Testing Suite")
    print("=" * 50)
    
    # Get webhook URL
    webhook_url = input("Enter your webhook URL (e.g., https://abc123.ngrok.io/drive-webhook): ").strip()
    
    if not webhook_url:
        print("❌ No webhook URL provided")
        return
    
    if not webhook_url.startswith('https://'):
        print("❌ Webhook URL must use HTTPS")
        return
    
    print(f"🎯 Testing webhook: {webhook_url}")
    print("-" * 50)
    
    # Run tests
    tests = [
        ("Server Health", lambda: test_webhook_server(webhook_url)),
        ("Webhook Endpoint", lambda: test_webhook_endpoint(webhook_url)),
        ("Status Endpoint", lambda: check_webhook_status_endpoint(webhook_url)),
        ("Local Logs", check_webhook_logs)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your webhook is ready.")
    else:
        print("⚠️  Some tests failed. Check the logs and configuration.")

if __name__ == "__main__":
    main() 