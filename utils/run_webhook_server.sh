#!/bin/bash

# Script para executar o servidor webhook

echo "🌐 INICIANDO SERVIDOR WEBHOOK"
echo "=============================="

# Muda para o diretório do projeto
cd "$(dirname "$0")/.."

# Ativa o ambiente virtual se existir
if [ -d "venv" ]; then
    echo "🐍 Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Verifica se as dependências estão instaladas
if ! python -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "⚠️  Dependências não encontradas!"
    echo "💡 Instale com: pip install -r webhook/requirements_webhook.txt"
    exit 1
fi

# Executa o servidor webhook
echo "🚀 Iniciando servidor webhook..."
python webhook/webhook_server.py

echo "👋 Servidor webhook encerrado."

