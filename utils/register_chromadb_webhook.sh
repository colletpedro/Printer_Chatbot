#!/bin/bash

# Script para registrar webhook no Google Drive

echo "📝 REGISTRADOR DE WEBHOOK CHROMADB"
echo "===================================="

# Muda para o diretório do projeto
cd "$(dirname "$0")/.."

# Ativa o ambiente virtual se existir
if [ -d "venv" ]; then
    echo "🐍 Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Verifica se as dependências estão instaladas
if ! python -c "import googleapiclient" 2>/dev/null; then
    echo "⚠️  Google API Client não encontrado!"
    echo "💡 Instale com: pip install google-api-python-client"
    exit 1
fi

# Verifica se o arquivo de credenciais existe
if [ ! -f "core/key.json" ]; then
    echo "❌ Arquivo de credenciais não encontrado!"
    echo "💡 Verifique se core/key.json existe"
    exit 1
fi

# Define secret se configurado
export WEBHOOK_SECRET=${WEBHOOK_SECRET:-chromadb-sync-secret-2024}

echo ""
python webhook/register_chromadb_webhook.py
