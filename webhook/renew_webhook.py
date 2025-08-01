#!/usr/bin/env python3
"""
Script Automatizado de Renovação de Webhook
Renova automaticamente webhooks expirados do Google Drive
"""

import json
import os
import subprocess
import time
import requests
from datetime import datetime

def print_step(step, message):
    """Print formatted step message"""
    print(f"\n🔄 Passo {step}: {message}")
    print("-" * 50)

def check_webhook_status():
    """Check current webhook status"""
    try:
        # Correct path to webhook channels file
        channels_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'webhook_channels.json')
        if os.path.exists(channels_file):
            with open(channels_file, 'r') as f:
                channels = json.load(f)
            
            active_channels = [c for c in channels if c.get('status') == 'active']
            
            if active_channels:
                latest = max(active_channels, key=lambda x: x.get('created_at', ''))
                expiration = latest.get('expiration')
                
                if expiration:
                    exp_time = datetime.fromtimestamp(int(expiration)/1000)
                    now = datetime.now()
                    time_left = exp_time - now
                    
                    if time_left.total_seconds() > 0:
                        hours_left = time_left.total_seconds() / 3600
                        return True, f"Webhook ativo ({hours_left:.1f}h restantes)", hours_left
                    else:
                        return False, "Webhook expirado", 0
                
                return True, "Webhook ativo (sem expiração)", 999
            else:
                return False, "Nenhum webhook ativo", 0
        
        return False, "Nenhum webhook configurado", 0
        
    except Exception as e:
        return False, f"Erro ao verificar status: {e}", 0

def kill_processes():
    """Kill existing webhook processes"""
    try:
        # Kill webhook_server.py
        subprocess.run(['pkill', '-f', 'webhook_server.py'], capture_output=True)
        
        # Kill processes on port 8080
        result = subprocess.run(['lsof', '-ti:8080'], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                subprocess.run(['kill', pid], capture_output=True)
        
        time.sleep(2)  # Wait for processes to die
        return True, "Processos antigos terminados"
        
    except Exception as e:
        return False, f"Erro ao terminar processos: {e}"

def check_ngrok():
    """Check if ngrok is running and get URL"""
    try:
        # Try to get ngrok status
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            
            for tunnel in tunnels:
                if tunnel.get('proto') == 'https':
                    url = tunnel.get('public_url')
                    if url:
                        return True, f"ngrok ativo: {url}", url
            
            return False, "ngrok rodando mas sem tunnel HTTPS", None
        else:
            return False, "ngrok não está respondendo", None
            
    except Exception as e:
        return False, f"ngrok não encontrado: {e}", None

def start_webhook_server():
    """Start webhook server in background"""
    try:
        # Set environment and start server
        env = os.environ.copy()
        env['WEBHOOK_SECRET'] = 'webhook-secret-123'
        
        process = subprocess.Popen(
            ['python', 'webhook_server.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd='webhook'
        )
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Check if server is running
        if process.poll() is None:  # Process is still running
            return True, f"Webhook server iniciado (PID: {process.pid})"
        else:
            stdout, stderr = process.communicate()
            return False, f"Erro ao iniciar servidor: {stderr.decode()}"
        
    except Exception as e:
        return False, f"Erro ao iniciar webhook server: {e}"

def register_webhook(ngrok_url):
    """Register new webhook using setup_webhook.py"""
    try:
        import sys
        import os
        # Add parent directory to path to access modules
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(parent_dir)
        
        # Change to parent directory for relative file access
        original_dir = os.getcwd()
        os.chdir(parent_dir)
        
        from webhook.setup_webhook import setup_drive_webhook
        
        webhook_url = f"{ngrok_url}/drive-webhook"
        token = "webhook-secret-123"
        
        print(f"   Registrando webhook:")
        print(f"   URL: {webhook_url}")
        print(f"   Token: {token}")
        
        result = setup_drive_webhook(webhook_url, token)
        
        if result:
            os.chdir(original_dir)  # Restore original directory
            return True, "Webhook registrado com sucesso"
        else:
            os.chdir(original_dir)  # Restore original directory
            return False, "Erro ao registrar webhook: Falha na configuração"
        
    except Exception as e:
        # Restore original directory in case of exception
        try:
            os.chdir(original_dir)
        except:
            pass
        return False, f"Erro ao registrar webhook: {e}"

def test_webhook(ngrok_url):
    """Test webhook endpoint"""
    try:
        webhook_url = f"{ngrok_url}/drive-webhook"
        
        # Test health endpoint
        health_url = f"{ngrok_url}/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            return True, "Webhook respondendo corretamente"
        else:
            return False, f"Webhook retornou status {response.status_code}"
            
    except Exception as e:
        return False, f"Erro ao testar webhook: {e}"

def main():
    """Main renewal process"""
    # Change to parent directory for relative file access
    original_dir = os.getcwd()
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(parent_dir)
    
    print("🔄 RENOVADOR AUTOMÁTICO DE WEBHOOK")
    print("=" * 50)
    
    # Step 1: Check current status
    print_step(1, "Verificando status atual")
    is_active, status, hours_left = check_webhook_status()
    print(f"   Status: {status}")
    
    if is_active and hours_left > 24:
        print("   ✅ Webhook ainda ativo por mais de 24h. Renovação não necessária.")
        return
    
    # Step 2: Kill old processes
    print_step(2, "Terminando processos antigos")
    success, message = kill_processes()
    print(f"   {message}")
    
    # Step 3: Check ngrok
    print_step(3, "Verificando ngrok")
    ngrok_active, ngrok_message, ngrok_url = check_ngrok()
    print(f"   {ngrok_message}")
    
    if not ngrok_active:
        print("   ❌ ngrok não está rodando!")
        print("   Execute em outro terminal: ngrok http 8080")
        return
    
    # Step 4: Start webhook server
    print_step(4, "Iniciando webhook server")
    success, message = start_webhook_server()
    print(f"   {message}")
    
    if not success:
        print("   ❌ Falha ao iniciar servidor")
        return
    
    # Step 5: Register webhook
    print_step(5, "Registrando novo webhook")
    success, message = register_webhook(ngrok_url)
    print(f"   {message}")
    
    if not success:
        print("   ❌ Falha ao registrar webhook")
        return
    
    # Step 6: Test webhook
    print_step(6, "Testando webhook")
    success, message = test_webhook(ngrok_url)
    print(f"   {message}")
    
    # Final status
    print("\n" + "=" * 50)
    if success:
        print("✅ RENOVAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"   Webhook URL: {ngrok_url}/drive-webhook")
        print("   Válido por: 7 dias")
        print("   Próxima renovação: 6 dias")
    else:
        print("❌ RENOVAÇÃO FALHOU")
        print("   Verifique os logs acima e tente o processo manual")
    
    print("=" * 50)
    
    # Restore original directory
    try:
        os.chdir(original_dir)
    except:
        pass

if __name__ == "__main__":
    main() 