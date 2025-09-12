#!/usr/bin/env python3
"""
ChromaDB Webhook Server
======================
Servidor webhook simplificado que executa update_chromadb.sh
quando recebe notificações de alterações no Google Drive.
"""

import os
import sys
import json
import logging
import subprocess
import hashlib
import hmac
from datetime import datetime
from flask import Flask, request, jsonify
from pathlib import Path

# Configuração de caminhos
PROJECT_ROOT = Path(__file__).parent.parent
UPDATE_SCRIPT = PROJECT_ROOT / "executables" / "update_chromadb.sh"
LOG_FILE = PROJECT_ROOT / "data" / "chromadb_webhook.log"
ACTIVITY_FILE = PROJECT_ROOT / "data" / "chromadb_webhook_activity.json"

# Criar diretório de logs se não existir
LOG_FILE.parent.mkdir(exist_ok=True)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Configuração
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'chromadb-sync-secret-2024')
PORT = int(os.environ.get('WEBHOOK_PORT', 8080))

def log_activity(event_type, details=None):
    """Registra atividade do webhook"""
    activity = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'details': details or {}
    }
    
    # Carrega histórico existente
    activities = []
    if ACTIVITY_FILE.exists():
        try:
            with open(ACTIVITY_FILE, 'r') as f:
                activities = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            activities = []
    
    # Adiciona nova atividade
    activities.append(activity)
    
    # Mantém apenas as últimas 100 atividades
    if len(activities) > 100:
        activities = activities[-100:]
    
    # Salva
    with open(ACTIVITY_FILE, 'w') as f:
        json.dump(activities, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Activity logged: {event_type}")

def execute_update_script():
    """Executa o script de atualização do ChromaDB"""
    try:
        logging.info("Iniciando atualização do ChromaDB...")
        log_activity("update_started")
        
        # Torna o script executável
        UPDATE_SCRIPT.chmod(0o755)
        
        # Executa o script
        result = subprocess.run(
            [str(UPDATE_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        if result.returncode == 0:
            logging.info("Atualização concluída com sucesso!")
            log_activity("update_success", {
                "stdout": result.stdout[-500:] if result.stdout else "",
                "return_code": 0
            })
            return True, result.stdout
        else:
            logging.error(f"Erro na atualização: {result.stderr}")
            log_activity("update_failed", {
                "stderr": result.stderr[-500:] if result.stderr else "",
                "return_code": result.returncode
            })
            return False, result.stderr
            
    except Exception as e:
        error_msg = f"Erro ao executar script: {str(e)}"
        logging.error(error_msg)
        log_activity("update_error", {"error": str(e)})
        return False, error_msg

def verify_webhook_token(request_data, token):
    """Verifica o token de autenticação do webhook"""
    # Google Drive webhooks usam o header X-Goog-Channel-Token
    request_token = request.headers.get('X-Goog-Channel-Token', '')
    
    if request_token == token:
        return True
    
    # Verificação alternativa via HMAC (mais segura)
    signature = request.headers.get('X-Hub-Signature-256', '')
    if signature:
        expected = 'sha256=' + hmac.new(
            token.encode(),
            request_data,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)
    
    return False

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """Handler principal do webhook"""
    try:
        # Log da requisição
        headers = dict(request.headers)
        logging.info(f"Webhook recebido: {request.method}")
        
        # Google Drive envia notificações com headers específicos
        resource_state = request.headers.get('X-Goog-Resource-State')
        resource_id = request.headers.get('X-Goog-Resource-Id')
        channel_id = request.headers.get('X-Goog-Channel-Id')
        
        log_activity("webhook_received", {
            "resource_state": resource_state,
            "resource_id": resource_id,
            "channel_id": channel_id,
            "headers": {k: v for k, v in headers.items() if not k.startswith('X-')}
        })
        
        # Verifica autenticação
        if not verify_webhook_token(request.data, WEBHOOK_SECRET):
            logging.warning("Token de autenticação inválido")
            log_activity("auth_failed")
            return jsonify({"error": "Unauthorized"}), 401
        
        # Se é uma notificação de mudança (não sync)
        if resource_state and resource_state != "sync":
            logging.info(f"Mudança detectada: {resource_state}")
            log_activity("change_detected", {"state": resource_state})
            
            # Executa atualização
            success, output = execute_update_script()
            
            if success:
                return jsonify({
                    "status": "success",
                    "message": "ChromaDB atualizado com sucesso",
                    "timestamp": datetime.now().isoformat()
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": "Erro ao atualizar ChromaDB",
                    "error": output
                }), 500
        
        # Mensagem de sincronização inicial (sync)
        elif resource_state == "sync":
            logging.info("Webhook sincronizado com sucesso")
            log_activity("webhook_synced")
            return jsonify({
                "status": "synced",
                "message": "Webhook sincronizado",
                "timestamp": datetime.now().isoformat()
            }), 200
        
        # Outros casos
        return jsonify({
            "status": "received",
            "message": "Notificação recebida",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"Erro no webhook: {str(e)}")
        log_activity("webhook_error", {"error": str(e)})
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    return jsonify({
        "status": "healthy",
        "service": "ChromaDB Webhook Server",
        "timestamp": datetime.now().isoformat(),
        "update_script": str(UPDATE_SCRIPT),
        "script_exists": UPDATE_SCRIPT.exists()
    }), 200

@app.route('/test-update', methods=['POST'])
def test_update():
    """Endpoint para testar a execução do script de atualização"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer ') or auth_header[7:] != WEBHOOK_SECRET:
            return jsonify({"error": "Unauthorized"}), 401
        
        logging.info("Teste de atualização iniciado")
        log_activity("test_update_requested")
        
        success, output = execute_update_script()
        
        return jsonify({
            "success": success,
            "output": output[-1000:] if output else "",  # Últimos 1000 chars
            "timestamp": datetime.now().isoformat()
        }), 200 if success else 500
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/', methods=['GET'])
def index():
    """Página inicial com informações do servidor"""
    return jsonify({
        "service": "ChromaDB Webhook Server",
        "status": "running",
        "endpoints": {
            "/webhook": "POST - Recebe notificações do Google Drive",
            "/health": "GET - Health check",
            "/test-update": "POST - Testa execução do script (requer autenticação)"
        },
        "timestamp": datetime.now().isoformat()
    }), 200

def main():
    """Função principal"""
    print("\n" + "=" * 60)
    print("🚀 CHROMADB WEBHOOK SERVER")
    print("=" * 60)
    print(f"📍 Porta: {PORT}")
    print(f"🔧 Script de atualização: {UPDATE_SCRIPT}")
    print(f"📝 Log: {LOG_FILE}")
    print(f"🔐 Secret configurado: {'Sim' if WEBHOOK_SECRET != 'chromadb-sync-secret-2024' else 'Não (usando padrão)'}")
    print("\n📡 Endpoints disponíveis:")
    print("   POST /webhook - Recebe notificações do Google Drive")
    print("   GET  /health - Health check")
    print("   POST /test-update - Testa execução (requer auth)")
    print("\n⚠️  Para usar em produção, exponha com ngrok:")
    print(f"   ngrok http {PORT}")
    print("=" * 60 + "\n")
    
    log_activity("server_started", {"port": PORT})
    
    # Inicia servidor
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    main()
