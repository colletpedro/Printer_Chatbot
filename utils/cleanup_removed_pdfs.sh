#!/bin/bash

# Script para limpeza de PDFs removidos do ChromaDB

echo "🧹 LIMPEZA DE PDFS REMOVIDOS - CHROMADB"
echo "========================================"
echo "⚠️  ATENÇÃO: Este script remove dados PERMANENTEMENTE do ChromaDB!"
echo ""

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

# Verifica se o ChromaDB existe
if [ ! -d "chromadb_storage" ] || [ ! -f "chromadb_storage/chroma.sqlite3" ]; then
    echo "❌ ChromaDB não encontrado!"
    echo "💡 Execute primeiro: ./executables/run_sync_drive_chromadb.sh"
    exit 1
fi

# Executa a limpeza do ChromaDB
echo "🚀 Iniciando limpeza do ChromaDB..."
python scripts/cleanup_chromadb.py

echo "✅ Limpeza concluída!"

