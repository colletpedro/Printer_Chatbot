#!/bin/bash

# Script para testar o webhook ChromaDB

echo "🧪 TESTE DO WEBHOOK CHROMADB"
echo "============================="

# Muda para o diretório do projeto
cd "$(dirname "$0")/.."

# Ativa o ambiente virtual se existir
if [ -d "venv" ]; then
    echo "🐍 Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Verifica se as dependências estão instaladas
if ! python -c "import requests" 2>/dev/null; then
    echo "⚠️  Requests não encontrado!"
    echo "💡 Instale com: pip install requests"
    exit 1
fi

# Define secret se configurado
export WEBHOOK_SECRET=${WEBHOOK_SECRET:-chromadb-sync-secret-2024}

echo ""
python webhook/test_chromadb_webhook.py
