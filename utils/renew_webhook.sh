#!/bin/bash

# Script para renovar webhook do Google Drive

echo "🔄 RENOVAÇÃO DE WEBHOOK"
echo "========================"

# Muda para o diretório do projeto
cd "$(dirname "$0")/.."

# Ativa o ambiente virtual se existir
if [ -d "venv" ]; then
    echo "🐍 Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Verifica se as dependências estão instaladas
if ! python -c "import google.auth, googleapiclient" 2>/dev/null; then
    echo "⚠️  Dependências não encontradas!"
    echo "💡 Instale com: pip install -r webhook/requirements_webhook.txt"
    exit 1
fi

# Verifica se o arquivo de credenciais existe
if [ ! -f "core/key.json" ]; then
    echo "❌ Arquivo de credenciais não encontrado!"
    echo "💡 Verifique se core/key.json existe"
    exit 1
fi

# Executa a renovação
echo "🚀 Renovando webhook..."
python webhook/renew_webhook.py

echo "✅ Renovação concluída!"

