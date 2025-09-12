#!/bin/bash

# Script para atualizar ChromaDB (alias para sincronização)

echo "🔄 ATUALIZAÇÃO CHROMADB"
echo "========================"
echo ""
echo "💡 Este script é um alias para run_sync_drive_chromadb.sh"
echo "   Executando sincronização Drive → ChromaDB..."

# Executa o script de sincronização
"$(dirname "$0")/run_sync_drive_chromadb.sh"

