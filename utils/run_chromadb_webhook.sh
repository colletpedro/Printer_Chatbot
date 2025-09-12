#!/bin/bash

# Script para iniciar o servidor de webhook ChromaDB

echo "🚀 INICIANDO SERVIDOR WEBHOOK CHROMADB"
echo "======================================"

# Muda para o diretório do projeto
cd "$(dirname "$0")/.."

# Ativa o ambiente virtual se existir
if [ -d "venv" ]; then
    echo "🐍 Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Verifica se as dependências estão instaladas
if ! python -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask não encontrado!"
    echo "💡 Instale com: pip install flask"
    exit 1
fi

# Verifica se o arquivo de credenciais existe
if [ ! -f "core/key.json" ]; then
    echo "❌ Arquivo de credenciais não encontrado!"
    echo "💡 Verifique se core/key.json existe"
    exit 1
fi

# Define variáveis de ambiente opcionais
export WEBHOOK_PORT=${WEBHOOK_PORT:-8080}
export WEBHOOK_SECRET=${WEBHOOK_SECRET:-chromadb-sync-secret-2024}

echo ""
echo "📋 Configurações:"
echo "   Porta: $WEBHOOK_PORT"
echo "   Secret: [CONFIGURADO]"
echo ""

# Inicia o servidor
echo "🌐 Iniciando servidor na porta $WEBHOOK_PORT..."
echo "💡 Para expor publicamente, use ngrok em outro terminal:"
echo "   ngrok http $WEBHOOK_PORT"
echo ""
echo "Pressione Ctrl+C para parar o servidor"
echo "======================================"
echo ""

python webhook/chromadb_webhook_server.py
