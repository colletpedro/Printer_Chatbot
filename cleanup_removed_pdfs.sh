#!/bin/bash

# Script para executar a limpeza da base de conhecimento
# Remove seções de PDFs que não existem mais no Google Drive

echo "🧹 Iniciando limpeza da base de conhecimento..."
echo "================================================"

# Navegar para o diretório do projeto
cd "$(dirname "$0")"

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    echo "🔄 Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Executar o script de limpeza
echo "🚀 Executando script de limpeza..."
python3 scripts/cleanup_removed_pdfs.py

echo ""
echo "✅ Script de limpeza finalizado!" 