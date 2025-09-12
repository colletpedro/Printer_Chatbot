#!/bin/bash

# Script para sincronizar Google Drive com ChromaDB

echo "🔄 SINCRONIZAÇÃO DRIVE → CHROMADB"
echo "=================================="

# Muda para o diretório do projeto
cd "$(dirname "$0")/.."

# Ativa o ambiente virtual se existir
if [ -d "venv" ]; then
    echo "🐍 Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Verifica se as dependências estão instaladas
if ! python -c "import chromadb, sentence_transformers" 2>/dev/null; then
    echo "⚠️  Dependências não encontradas!"
    echo "💡 Instale com: pip install -r core/requirements.txt"
    exit 1
fi

# Verifica se o arquivo de credenciais existe
if [ ! -f "core/key.json" ]; then
    echo "❌ Arquivo de credenciais não encontrado!"
    echo "💡 Verifique se core/key.json existe"
    exit 1
fi

# Executa a sincronização
echo "🚀 Iniciando sincronização..."
python scripts/sync_drive_chromadb.py

echo "✅ Sincronização concluída!"

