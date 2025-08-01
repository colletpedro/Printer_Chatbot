#!/usr/bin/env python3
"""
Google Drive Webhook Server
Receives notifications when PDFs are modified in Google Drive and automatically updates the knowledge base
"""

import os
import sys
import json
import logging
import subprocess
import time
from datetime import datetime
from flask import Flask, request, jsonify

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

# Configure logging with correct path
LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'webhook.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Configuration with correct paths
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your-secret-token-change-this')
UPDATE_SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'core', 'update_drive.py')
METADATA_GENERATOR_SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'generate_printer_metadata.py')
WEBHOOK_LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'webhook_activity.json')

def log_webhook_activity(event_type, details):
    """Log webhook activity for monitoring"""
    activity = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'details': details
    }
    
    # Load existing log
    activities = []
    if os.path.exists(WEBHOOK_LOG_FILE):
        try:
            with open(WEBHOOK_LOG_FILE, 'r') as f:
                activities = json.load(f)
        except:
            activities = []
    
    # Add new activity and keep last 100 entries
    activities.append(activity)
    activities = activities[-100:]
    
    # Save log
    with open(WEBHOOK_LOG_FILE, 'w') as f:
        json.dump(activities, f, indent=2)

def verify_google_webhook(request):
    """Verify that the webhook notification is from Google"""
    # Check for required Google headers
    channel_id = request.headers.get('X-Goog-Channel-ID')
    channel_token = request.headers.get('X-Goog-Channel-Token')
    resource_state = request.headers.get('X-Goog-Resource-State')
    
    if not all([channel_id, resource_state]):
        return False
    
    # Verify our token if set
    if channel_token and channel_token != WEBHOOK_SECRET:
        return False
    
    return True

def run_metadata_generation():
    """Run the metadata generator script after successful knowledge base update"""
    try:
        logging.info("🔧 Gerando metadados automáticos para novos modelos...")
        
        result = subprocess.run(
            ['python', METADATA_GENERATOR_SCRIPT], 
            capture_output=True, 
            text=True,
            timeout=60  # 1 minute timeout
        )
        
        if result.returncode == 0:
            logging.info("✅ Metadados atualizados automaticamente!")
            return True, result.stdout
        else:
            logging.warning(f"⚠️ Geração de metadados falhou: {result.stderr}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        logging.warning("⏰ Geração de metadados timeout")
        return False, "Timeout"
    except Exception as e:
        logging.warning(f"💥 Erro na geração de metadados: {str(e)}")
        return False, str(e)

@app.route('/drive-webhook', methods=['POST'])
def handle_drive_notification():
    """Handle incoming Google Drive webhook notifications"""
    
    try:
        # Get notification headers
        channel_id = request.headers.get('X-Goog-Channel-ID', 'unknown')
        resource_state = request.headers.get('X-Goog-Resource-State', 'unknown')
        resource_id = request.headers.get('X-Goog-Resource-ID', 'unknown')
        message_number = request.headers.get('X-Goog-Message-Number', '0')
        
        logging.info(f"📨 Webhook notification received:")
        logging.info(f"   Channel ID: {channel_id}")
        logging.info(f"   Resource State: {resource_state}")
        logging.info(f"   Message Number: {message_number}")
        
        # Verify the notification is from Google
        if not verify_google_webhook(request):
            logging.warning("⚠️ Invalid webhook notification - verification failed")
            log_webhook_activity('verification_failed', {
                'headers': dict(request.headers),
                'reason': 'verification_failed'
            })
            return jsonify({"error": "Invalid notification"}), 403
        
        # Log the activity
        log_webhook_activity('notification_received', {
            'channel_id': channel_id,
            'resource_state': resource_state,
            'message_number': message_number
        })
        
        # Handle different resource states
        if resource_state == 'sync':
            logging.info("🔄 Sync message received - webhook channel is active")
            return jsonify({"status": "sync_acknowledged"}), 200
        
        elif resource_state in ['update', 'add', 'remove', 'change']:
            logging.info(f"📁 Processing {resource_state} event...")
            
            try:
                # Run the update script
                logging.info("🔄 Starting knowledge base update...")
                result = subprocess.run(
                    ['python', UPDATE_SCRIPT], 
                    capture_output=True, 
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    logging.info("✅ Knowledge base updated successfully!")
                    
                    # Automatically generate metadata for new printer models
                    metadata_success, metadata_output = run_metadata_generation()
                    
                    # Parse the output to get update details
                    update_details = {
                        'success': True,
                        'stdout': result.stdout,
                        'timestamp': datetime.now().isoformat(),
                        'metadata_generated': metadata_success,
                        'metadata_output': metadata_output if metadata_success else None
                    }
                    
                    log_webhook_activity('update_success', update_details)
                    
                    response_msg = "Knowledge base updated"
                    if metadata_success:
                        response_msg += " and printer metadata auto-generated"
                    
                    return jsonify({
                        "status": "success",
                        "message": response_msg,
                        "details": result.stdout,
                        "metadata_generated": metadata_success
                    }), 200
                
                else:
                    error_msg = f"Update script failed: {result.stderr}"
                    logging.error(f"❌ {error_msg}")
                    
                    log_webhook_activity('update_failed', {
                        'success': False,
                        'error': result.stderr,
                        'returncode': result.returncode
                    })
                    
                    return jsonify({
                        "status": "error",
                        "message": error_msg
                    }), 500
                    
            except subprocess.TimeoutExpired:
                error_msg = "Update script timed out"
                logging.error(f"⏰ {error_msg}")
                log_webhook_activity('update_timeout', {'error': error_msg})
                return jsonify({"status": "error", "message": error_msg}), 500
                
            except Exception as e:
                error_msg = f"Error running update script: {str(e)}"
                logging.error(f"💥 {error_msg}")
                log_webhook_activity('update_error', {'error': error_msg})
                return jsonify({"status": "error", "message": error_msg}), 500
        
        else:
            logging.info(f"ℹ️ Ignoring resource state: {resource_state}")
            return jsonify({"status": "ignored"}), 200
            
    except Exception as e:
        error_msg = f"Webhook processing error: {str(e)}"
        logging.error(f"💥 {error_msg}")
        log_webhook_activity('processing_error', {'error': error_msg})
        return jsonify({"status": "error", "message": error_msg}), 500

@app.route('/webhook-status', methods=['GET'])
def webhook_status():
    """Get webhook status and recent activity"""
    
    try:
        # Load recent activity
        activities = []
        if os.path.exists(WEBHOOK_LOG_FILE):
            with open(WEBHOOK_LOG_FILE, 'r') as f:
                activities = json.load(f)
        
        # Get recent successful updates
        recent_updates = [a for a in activities if a['event_type'] == 'update_success'][-5:]
        recent_notifications = [a for a in activities if a['event_type'] == 'notification_received'][-10:]
        
        return jsonify({
            "status": "active",
            "server_time": datetime.now().isoformat(),
            "recent_updates": recent_updates,
            "recent_notifications": recent_notifications,
            "total_activities": len(activities)
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Google Drive Webhook Server"
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Basic info page"""
    return jsonify({
        "service": "Google Drive Webhook Server",
        "version": "1.0",
        "endpoints": {
            "/drive-webhook": "POST - Receive Google Drive notifications",
            "/webhook-status": "GET - Check webhook status and activity",
            "/health": "GET - Health check"
        }
    }), 200

if __name__ == '__main__':
    print("🚀 Starting Google Drive Webhook Server...")
    print(f"📁 Update script: {UPDATE_SCRIPT}")
    print(f"🔐 Webhook secret configured: {'Yes' if WEBHOOK_SECRET != 'your-secret-token-change-this' else 'No (using default)'}")
    
    # Create initial log file
    if not os.path.exists(WEBHOOK_LOG_FILE):
        with open(WEBHOOK_LOG_FILE, 'w') as f:
            json.dump([], f)
    
    # Run the server
    app.run(
        host='0.0.0.0',  # Accept connections from any IP
        port=int(os.environ.get('PORT', 8080)),
        debug=False  # Set to True for development
    ) 