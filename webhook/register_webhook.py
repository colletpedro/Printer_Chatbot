#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.services import drive_service
from googleapiclient.discovery import build
import json

async def register_webhook():
    """Registra webhook no Google Drive"""
    
    # Pede URL do ngrok
    ngrok_url = input("Digite a URL do ngrok (ex: https://abc123.ngrok.io): ").strip()
    if not ngrok_url.startswith('https://'):
        print("❌ URL deve começar com https://")
        return
    
    # Inicializa Google Drive
    await drive_service.initialize()
    
    # Cria canal de notificação
    service = drive_service.service
    
    channel = {
        'id': f'webhook-{int(time.time())}',
        'type': 'web_hook',
        'address': f'{ngrok_url}/webhook/google-drive',
        'token': settings.webhook_secret,
        'expiration': int((datetime.now() + timedelta(days=7)).timestamp() * 1000)
    }
    
    try:
        result = service.changes().watch(
            pageToken='1',  # Monitora mudanças a partir de agora
            body=channel
        ).execute()
        
        print("✅ Webhook registrado com sucesso!")
        print(f"   Channel ID: {result['id']}")
        print(f"   Resource ID: {result['resourceId']}")
        
        # Salva informações do canal
        channel_info = {
            'channel_id': result['id'],
            'resource_id': result['resourceId'],
            'webhook_url': f'{ngrok_url}/webhook/google-drive',
            'token': settings.webhook_secret,
            'expiration': result.get('expiration'),
            'created_at': datetime.now().isoformat()
        }
        
        with open('data/webhook_channels.json', 'w') as f:
            json.dump(channel_info, f, indent=2)
        
        print(f"   Informações salvas em data/webhook_channels.json")
        print(f"   Webhook expira em: {datetime.fromtimestamp(int(result['expiration'])/1000)}")
        
    except Exception as e:
        print(f"❌ Erro ao registrar webhook: {e}")

if __name__ == "__main__":
    import time
    from datetime import datetime, timedelta
    from src.core import settings
    
    asyncio.run(register_webhook())
