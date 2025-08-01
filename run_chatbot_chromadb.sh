#!/bin/bash
# Script para executar o chatbot com ChromaDB

echo "🚀 Iniciando Chatbot Epson com ChromaDB"
echo "========================================"

# Ativa ambiente virtual se existir
if [ -d "venv" ]; then
    echo "📦 Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Verifica se ChromaDB existe
if [ -d "chromadb_storage" ]; then
    echo "✅ ChromaDB encontrado - usando busca semântica"
else
    echo "⚠️  ChromaDB não encontrado - executando migração primeiro..."
    echo "💡 Execute: python3 scripts/migrate_to_chromadb.py"
    read -p "Deseja executar a migração agora? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 scripts/migrate_to_chromadb.py
        if [ $? -eq 0 ]; then
            echo "✅ Migração concluída!"
        else
            echo "❌ Erro na migração - usando sistema JSON"
        fi
    fi
fi

echo ""
echo "🤖 Iniciando chatbot..."
python3 core/chatbot_chromadb.py