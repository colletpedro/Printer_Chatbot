#!/usr/bin/env python3
"""
Registra Webhook do Google Drive para ChromaDB
==============================================
Script para registrar um webhook que monitora mudanças no Google Drive
e aciona atualizações automáticas do ChromaDB.
"""

import os
import sys
import json
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path

# Adiciona paths do projeto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / "core"))

# Google API imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configurações
CREDENTIALS_PATH = PROJECT_ROOT / "core" / "key.json"
WEBHOOK_CONFIG_FILE = PROJECT_ROOT / "data" / "chromadb_webhook_config.json"
DRIVE_FOLDER_ID = "1B-Xsgvy4W392yfLP4ilrzrtl8zzmEgTl"  # Pasta dos PDFs
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'chromadb-sync-secret-2024')

# Criar diretório de dados se não existir
WEBHOOK_CONFIG_FILE.parent.mkdir(exist_ok=True)

class WebhookRegistrar:
    """Gerencia o registro de webhooks do Google Drive"""
    
    def __init__(self):
        self.drive_service = None
        self.setup_drive_service()
    
    def setup_drive_service(self):
        """Configura o serviço do Google Drive"""
        print("🔧 Configurando serviço do Google Drive...")
        
        if not CREDENTIALS_PATH.exists():
            raise FileNotFoundError(f"Credenciais não encontradas: {CREDENTIALS_PATH}")
        
        credentials = service_account.Credentials.from_service_account_file(
            str(CREDENTIALS_PATH),
            scopes=['https://www.googleapis.com/auth/drive']
        )
        
        self.drive_service = build('drive', 'v3', credentials=credentials)
        print("✅ Google Drive configurado")
    
    def list_active_webhooks(self):
        """Lista webhooks ativos"""
        config = self.load_webhook_config()
        if config and 'channels' in config:
            return config['channels']
        return []
    
    def load_webhook_config(self):
        """Carrega configuração do webhook"""
        if WEBHOOK_CONFIG_FILE.exists():
            try:
                with open(WEBHOOK_CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_webhook_config(self, config):
        """Salva configuração do webhook"""
        with open(WEBHOOK_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def stop_webhook(self, channel_id, resource_id):
        """Para um webhook existente"""
        try:
            body = {
                'id': channel_id,
                'resourceId': resource_id
            }
            self.drive_service.channels().stop(body=body).execute()
            print(f"✅ Webhook {channel_id} parado")
            return True
        except HttpError as e:
            if e.resp.status == 404:
                print(f"⚠️ Webhook {channel_id} não encontrado (pode já ter expirado)")
                return True
            print(f"❌ Erro ao parar webhook: {e}")
            return False
    
    def register_webhook(self, webhook_url):
        """Registra um novo webhook para monitorar a pasta do Drive"""
        print("\n📝 Registrando novo webhook...")
        
        # Para webhooks antigos
        self.cleanup_old_webhooks()
        
        # Gera IDs únicos
        channel_id = f"chromadb-sync-{uuid.uuid4().hex[:8]}"
        
        # Configuração do webhook
        expiration_time = int((datetime.now() + timedelta(days=7)).timestamp() * 1000)
        
        body = {
            'id': channel_id,
            'type': 'web_hook',
            'address': webhook_url,
            'token': WEBHOOK_SECRET,
            'expiration': expiration_time,
            'params': {
                'ttl': '604800'  # 7 dias em segundos
            }
        }
        
        try:
            # Registra webhook para monitorar mudanças na pasta
            print(f"📁 Monitorando pasta: {DRIVE_FOLDER_ID}")
            
            # Usa página de alterações (changes) para monitorar toda a pasta
            response = self.drive_service.files().watch(
                fileId=DRIVE_FOLDER_ID,
                body=body
            ).execute()
            
            # Salva configuração
            config = self.load_webhook_config()
            if 'channels' not in config:
                config['channels'] = []
            
            webhook_info = {
                'channel_id': channel_id,
                'resource_id': response.get('resourceId'),
                'webhook_url': webhook_url,
                'folder_id': DRIVE_FOLDER_ID,
                'created_at': datetime.now().isoformat(),
                'expires_at': datetime.fromtimestamp(expiration_time / 1000).isoformat(),
                'status': 'active'
            }
            
            config['channels'].append(webhook_info)
            config['last_registered'] = datetime.now().isoformat()
            
            self.save_webhook_config(config)
            
            print("\n✅ WEBHOOK REGISTRADO COM SUCESSO!")
            print(f"📍 URL: {webhook_url}")
            print(f"🆔 Channel ID: {channel_id}")
            print(f"📅 Expira em: {webhook_info['expires_at']}")
            print(f"📁 Pasta monitorada: {DRIVE_FOLDER_ID}")
            
            return webhook_info
            
        except HttpError as e:
            print(f"❌ Erro ao registrar webhook: {e}")
            if hasattr(e, 'content'):
                print(f"Detalhes: {e.content}")
            return None
    
    def cleanup_old_webhooks(self):
        """Remove webhooks antigos ou expirados"""
        config = self.load_webhook_config()
        
        if not config or 'channels' not in config:
            return
        
        active_channels = []
        
        for channel in config['channels']:
            # Verifica se expirou
            expires_at = datetime.fromisoformat(channel['expires_at'])
            if expires_at < datetime.now():
                print(f"🗑️ Removendo webhook expirado: {channel['channel_id']}")
                self.stop_webhook(channel['channel_id'], channel['resource_id'])
            else:
                # Tenta parar o webhook para garantir limpeza
                if channel['status'] == 'active':
                    print(f"🛑 Parando webhook ativo: {channel['channel_id']}")
                    self.stop_webhook(channel['channel_id'], channel['resource_id'])
                else:
                    active_channels.append(channel)
        
        # Atualiza configuração
        config['channels'] = []
        self.save_webhook_config(config)
    
    def test_webhook_registration(self):
        """Testa se o webhook pode ser registrado"""
        try:
            # Testa acesso à pasta
            folder = self.drive_service.files().get(fileId=DRIVE_FOLDER_ID).execute()
            print(f"✅ Acesso à pasta confirmado: {folder.get('name', 'Sem nome')}")
            return True
        except HttpError as e:
            print(f"❌ Erro ao acessar pasta: {e}")
            return False


def main():
    """Função principal"""
    print("\n" + "=" * 60)
    print("🎯 REGISTRADOR DE WEBHOOK CHROMADB")
    print("=" * 60)
    
    registrar = WebhookRegistrar()
    
    # Menu de opções
    print("\nO que você deseja fazer?")
    print("1. Registrar novo webhook")
    print("2. Listar webhooks ativos")
    print("3. Limpar webhooks antigos")
    print("4. Testar acesso ao Drive")
    
    choice = input("\nEscolha (1-4): ").strip()
    
    if choice == '1':
        # Registrar novo webhook
        print("\n📡 CONFIGURAÇÃO DO WEBHOOK")
        print("-" * 40)
        print("Digite a URL pública do seu webhook")
        print("Exemplo: https://abc123.ngrok.io/webhook")
        
        webhook_url = input("\nURL do webhook: ").strip()
        
        if not webhook_url:
            print("❌ URL não pode estar vazia")
            return
        
        if not webhook_url.startswith('https://'):
            print("⚠️ AVISO: Webhooks devem usar HTTPS para produção")
        
        # Testa acesso primeiro
        if not registrar.test_webhook_registration():
            print("❌ Não foi possível acessar o Google Drive")
            return
        
        # Registra webhook
        result = registrar.register_webhook(webhook_url)
        
        if result:
            print("\n💡 PRÓXIMOS PASSOS:")
            print("1. Certifique-se que o servidor está rodando:")
            print("   python webhook/chromadb_webhook_server.py")
            print("\n2. Se usando ngrok, mantenha-o ativo:")
            print(f"   ngrok http 8080")
            print("\n3. O webhook expira em 7 dias. Para renovar:")
            print("   python webhook/register_chromadb_webhook.py")
    
    elif choice == '2':
        # Listar webhooks
        channels = registrar.list_active_webhooks()
        
        if channels:
            print(f"\n📋 {len(channels)} webhook(s) registrado(s):")
            for ch in channels:
                print(f"\n  Channel ID: {ch['channel_id']}")
                print(f"  URL: {ch['webhook_url']}")
                print(f"  Status: {ch['status']}")
                print(f"  Criado: {ch['created_at']}")
                print(f"  Expira: {ch['expires_at']}")
        else:
            print("\n⚠️ Nenhum webhook registrado")
    
    elif choice == '3':
        # Limpar webhooks
        print("\n🧹 Limpando webhooks antigos...")
        registrar.cleanup_old_webhooks()
        print("✅ Limpeza concluída")
    
    elif choice == '4':
        # Testar acesso
        if registrar.test_webhook_registration():
            print("✅ Acesso ao Google Drive funcionando!")
        else:
            print("❌ Problemas no acesso ao Drive")
    
    else:
        print("❌ Opção inválida")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
