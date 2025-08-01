# Google Drive Webhook Setup Guide

This guide will help you set up real-time webhook notifications for your Google Drive folder, so your chatbot is automatically updated when PDFs change.

## 📋 Prerequisites

1. **Python environment with venv activated**
2. **Google Drive API credentials** (`key.json` file)
3. **ngrok account** (for testing) or **production server** with HTTPS

## 🛠️ Installation Steps

### Step 1: Install Dependencies

```bash
# Install webhook dependencies
pip install -r requirements_webhook.txt
```

### Step 2: Set Up ngrok (for testing)

1. **Download ngrok** from https://ngrok.com/
2. **Create free account** and get auth token
3. **Configure ngrok**:
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

### Step 3: Start the Webhook Server

1. **Open first terminal** and start the webhook server:
   ```bash
   python webhook_server.py
   ```
   
   You should see:
   ```
   🚀 Starting Google Drive Webhook Server...
   📁 Update script: update_drive.py
   🔐 Webhook secret configured: No (using default)
   * Running on all addresses (0.0.0.0)
   * Running on http://127.0.0.1:8080
   * Running on http://[YOUR_IP]:8080
   ```

2. **Open second terminal** and expose server with ngrok:
   ```bash
   ngrok http 8080
   ```
   
   You should see something like:
   ```
   Session Status    online
   Account           your@email.com
   Version           3.x.x
   Region            United States (us)
   Latency           -
   Web Interface     http://127.0.0.1:4040
   Forwarding        https://abc123.ngrok.io -> http://localhost:8080
   ```

3. **Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

### Step 4: Register the Webhook

1. **Run the setup script**:
   ```bash
   python setup_webhook.py
   ```

2. **Choose option 1** (Setup new webhook)

3. **Enter your webhook URL**:
   ```
   Enter your webhook URL (must be HTTPS): https://abc123.ngrok.io/drive-webhook
   ```

4. **Enter secret token** (optional but recommended):
   ```
   Enter secret token (optional, press Enter to skip): my-secret-token-123
   ```

5. **You should see**:
   ```
   ✅ Webhook registered successfully!
      Resource ID: ABC123DEF456
      Resource URI: https://www.googleapis.com/drive/v3/files/1B-Xsgvy4W392yfLP4ilrzrtl8zzmEgTl
   
   🎉 Webhook setup complete!
   Your webhook will receive notifications at: https://abc123.ngrok.io/drive-webhook
   ```

### Step 5: Test the Webhook

1. **Run the test script**:
   ```bash
   python test_webhook.py
   ```

2. **Enter your webhook URL** when prompted

3. **Check all tests pass**:
   ```
   📋 Test Results Summary:
      Server Health: ✅ PASS
      Webhook Endpoint: ✅ PASS
      Status Endpoint: ✅ PASS
      Local Logs: ✅ PASS
   
   🎉 All tests passed! Your webhook is ready.
   ```

### Step 6: Test with Real Google Drive Changes

1. **Upload a new PDF** to your Google Drive folder
2. **Check webhook server logs** - you should see:
   ```
   📨 Webhook notification received:
      Channel ID: your-channel-id
      Resource State: update
      Message Number: 2
   📁 Processing update event...
   🔄 Starting knowledge base update...
   ✅ Knowledge base updated successfully!
   ```

3. **Verify chatbot** has the new information by running:
   ```bash
   python chatbot.py
   ```

## 🔧 Configuration Options

### Set Custom Secret Token

For production, set a custom secret token:

```bash
# Linux/Mac
export WEBHOOK_SECRET="your-super-secret-token"

# Windows
set WEBHOOK_SECRET=your-super-secret-token

# Or create a .env file
echo "WEBHOOK_SECRET=your-super-secret-token" > .env
```

### Change Server Port

```bash
# Set custom port
export PORT=9000
python webhook_server.py
```

## 📊 Monitoring and Management

### Check Webhook Status

```bash
python setup_webhook.py
# Choose option 5: Show webhook status
```

### View Recent Activity

Visit in browser: `https://your-webhook-url/webhook-status`

### Stop All Webhooks

```bash
python setup_webhook.py
# Choose option 4: Stop all webhooks
```

## 🚨 Troubleshooting

### Common Issues

1. **"Cannot reach webhook server"**
   - Make sure webhook server is running
   - Check ngrok is active and forwarding correctly
   - Verify HTTPS URL is correct

2. **"Invalid webhook notification"**
   - Check secret token matches
   - Verify Google Drive API credentials
   - Make sure webhook URL is publicly accessible

3. **"Update script failed"**
   - Check `update_drive.py` runs manually
   - Verify Google Drive API permissions
   - Check `key.json` file exists

4. **Webhook expires after 7 days**
   - Run setup script again to renew
   - Consider setting up automatic renewal

### Debug Commands

```bash
# Check webhook server logs
cat webhook.log

# Check webhook activity
cat webhook_activity.json

# Test manual update
python update_drive.py

# Check active webhooks
python setup_webhook.py
```

## 🔄 Production Deployment

For production use:

1. **Deploy to cloud service** (AWS, Google Cloud, Heroku, etc.)
2. **Get proper domain** with SSL certificate
3. **Set up monitoring** and error alerts
4. **Configure automatic webhook renewal**
5. **Add authentication** and rate limiting

### Example Production Setup

```bash
# Set production environment variables
export WEBHOOK_SECRET="production-secret-token"
export PORT=443
export FLASK_ENV=production

# Run with gunicorn for better performance
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 webhook_server:app
```

## 📈 Benefits of Webhook Setup

✅ **Instant Updates**: Manual updates automatically within seconds of PDF upload  
✅ **No Manual Work**: Zero intervention required  
✅ **Always Current**: Chatbot always has latest information  
✅ **Efficient**: Only processes when files actually change  
✅ **Scalable**: Handles multiple PDFs and frequent updates  

## 🎯 Next Steps

Once your webhook is working:

1. **Monitor for a few days** to ensure stability
2. **Set up webhook renewal** before 7-day expiration
3. **Consider production deployment** for 24/7 operation
4. **Add error monitoring** and alerts
5. **Test failover scenarios**

Your Google Drive webhook system is now ready! 🚀 