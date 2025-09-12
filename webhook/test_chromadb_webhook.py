#!/usr/bin/env python3
"""
Testa o Webhook ChromaDB
========================
Script para testar se o webhook está funcionando corretamente.
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

# Configurações
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_ROOT / "data" / "chromadb_webhook_config.json"
ACTIVITY_FILE = PROJECT_ROOT / "data" / "chromadb_webhook_activity.json"
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'chromadb-sync-secret-2024')

def load_webhook_config():
    """Carrega configuração do webhook"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def load_recent_activity():
    """Carrega atividade recente do webhook"""
    if ACTIVITY_FILE.exists():
        try:
            with open(ACTIVITY_FILE, 'r') as f:
                activities = json.load(f)
                # Retorna últimas 10 atividades
                return activities[-10:] if activities else []
        except:
            return []
    return []

def test_health_check(webhook_url):
    """Testa o endpoint de health check"""
    try:
        # Remove /webhook do final se existir
        base_url = webhook_url.replace('/webhook', '')
        health_url = f"{base_url}/health"
        
        print(f"🔍 Testando health check: {health_url}")
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Servidor está funcionando!")
            print(f"   Status: {data.get('status')}")
            print(f"   Script existe: {data.get('script_exists')}")
            return True
        else:
            print(f"❌ Health check falhou: Status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao conectar: {e}")
        return False

def test_update_endpoint(webhook_url):
    """Testa o endpoint de atualização manual"""
    try:
        # Remove /webhook do final se existir
        base_url = webhook_url.replace('/webhook', '')
        test_url = f"{base_url}/test-update"
        
        print(f"\n🔧 Testando execução do script de atualização...")
        print(f"   URL: {test_url}")
        
        headers = {
            'Authorization': f'Bearer {WEBHOOK_SECRET}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            test_url,
            headers=headers,
            json={'test': True},
            timeout=120  # 2 minutos de timeout para a atualização
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Script executado com sucesso!")
            
            # Mostra parte da saída
            if 'output' in data:
                output_lines = data['output'].strip().split('\n')
                if output_lines:
                    print("\n📝 Últimas linhas da saída:")
                    for line in output_lines[-5:]:
                        print(f"   {line}")
            
            return True
        elif response.status_code == 401:
            print("❌ Erro de autenticação (token inválido)")
            return False
        else:
            print(f"❌ Teste falhou: Status {response.status_code}")
            if response.text:
                print(f"   Resposta: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️ Timeout - a atualização pode estar demorando mais que o esperado")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def simulate_webhook_notification(webhook_url):
    """Simula uma notificação do Google Drive"""
    try:
        print(f"\n📨 Simulando notificação do Google Drive...")
        
        headers = {
            'X-Goog-Channel-Token': WEBHOOK_SECRET,
            'X-Goog-Resource-State': 'update',
            'X-Goog-Resource-Id': 'test-resource-123',
            'X-Goog-Channel-Id': 'test-channel-456',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'kind': 'drive#changes',
            'test': True
        }
        
        response = requests.post(
            webhook_url,
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            print("✅ Notificação processada com sucesso!")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Mensagem: {data.get('message')}")
            return True
        else:
            print(f"❌ Falha ao processar notificação: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao simular notificação: {e}")
        return False

def check_webhook_status():
    """Verifica status geral do webhook"""
    print("\n" + "=" * 60)
    print("📊 STATUS DO WEBHOOK CHROMADB")
    print("=" * 60)
    
    # Carrega configuração
    config = load_webhook_config()
    
    if not config or 'channels' not in config:
        print("⚠️ Nenhum webhook registrado")
        print("\n💡 Para registrar um webhook:")
        print("   1. Inicie o servidor: python webhook/chromadb_webhook_server.py")
        print("   2. Exponha com ngrok: ngrok http 8080")
        print("   3. Registre: python webhook/register_chromadb_webhook.py")
        return
    
    # Mostra webhooks registrados
    channels = config.get('channels', [])
    print(f"\n📋 Webhooks registrados: {len(channels)}")
    
    for ch in channels:
        print(f"\n  🆔 Channel: {ch['channel_id']}")
        print(f"  📍 URL: {ch['webhook_url']}")
        print(f"  📁 Pasta: {ch['folder_id']}")
        print(f"  ⏰ Status: {ch['status']}")
        
        # Verifica expiração
        expires_at = datetime.fromisoformat(ch['expires_at'])
        days_left = (expires_at - datetime.now()).days
        
        if days_left < 0:
            print(f"  ❌ EXPIRADO há {abs(days_left)} dias")
        elif days_left == 0:
            print(f"  ⚠️ EXPIRA HOJE!")
        elif days_left <= 2:
            print(f"  ⚠️ Expira em {days_left} dias")
        else:
            print(f"  ✅ Expira em {days_left} dias")
    
    # Mostra atividade recente
    activities = load_recent_activity()
    
    if activities:
        print(f"\n📅 Atividade recente ({len(activities)} eventos):")
        for act in activities[-5:]:
            timestamp = act.get('timestamp', 'N/A')
            event = act.get('event_type', 'unknown')
            
            # Formata timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime('%d/%m %H:%M')
            except:
                time_str = timestamp
            
            # Ícone por tipo de evento
            icons = {
                'server_started': '🚀',
                'webhook_received': '📨',
                'change_detected': '🔍',
                'update_started': '🔧',
                'update_success': '✅',
                'update_failed': '❌',
                'webhook_synced': '🔄'
            }
            
            icon = icons.get(event, '•')
            print(f"   {icon} {time_str} - {event}")
    else:
        print("\n⚠️ Nenhuma atividade registrada ainda")

def main():
    """Função principal"""
    print("\n" + "=" * 60)
    print("🧪 TESTE DO WEBHOOK CHROMADB")
    print("=" * 60)
    
    # Verifica status geral
    check_webhook_status()
    
    # Carrega configuração
    config = load_webhook_config()
    
    if not config or 'channels' not in config or not config['channels']:
        print("\n❌ Nenhum webhook configurado para testar")
        return
    
    # Pega o webhook mais recente
    latest_channel = config['channels'][-1]
    webhook_url = latest_channel['webhook_url']
    
    print(f"\n🎯 Testando webhook: {webhook_url}")
    print("-" * 40)
    
    # Menu de testes
    print("\nQual teste deseja executar?")
    print("1. Health check (verifica se servidor está rodando)")
    print("2. Teste de atualização (executa update_chromadb.sh)")
    print("3. Simular notificação (simula mudança no Drive)")
    print("4. Todos os testes")
    
    choice = input("\nEscolha (1-4): ").strip()
    
    results = {}
    
    if choice in ['1', '4']:
        results['health'] = test_health_check(webhook_url)
    
    if choice in ['2', '4']:
        if input("\n⚠️ Isso executará o script de atualização. Continuar? (s/n): ").lower() == 's':
            results['update'] = test_update_endpoint(webhook_url)
    
    if choice in ['3', '4']:
        results['notification'] = simulate_webhook_notification(webhook_url)
    
    # Resumo dos resultados
    if results:
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        
        for test_name, success in results.items():
            status = "✅ Passou" if success else "❌ Falhou"
            print(f"{test_name.capitalize()}: {status}")
        
        if all(results.values()):
            print("\n🎉 Todos os testes passaram! O webhook está funcionando!")
        elif any(results.values()):
            print("\n⚠️ Alguns testes falharam. Verifique os logs.")
        else:
            print("\n❌ Todos os testes falharam. Verifique:")
            print("   1. Se o servidor está rodando")
            print("   2. Se a URL do webhook está correta")
            print("   3. Se o ngrok está ativo (se aplicável)")

if __name__ == '__main__':
    main()
