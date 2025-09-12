#!/bin/bash

echo "🧹 Limpando TODOS os processos Streamlit..."

# Mata com força máxima
pkill -9 -f streamlit 2>/dev/null
pkill -9 -f app_streamlit.py 2>/dev/null
lsof -ti:8501 | xargs kill -9 2>/dev/null
lsof -ti:8502 | xargs kill -9 2>/dev/null
lsof -ti:8503 | xargs kill -9 2>/dev/null

echo "✅ Todos os processos Streamlit foram encerrados!"
echo ""
echo "📝 Agora você pode executar: ./start.sh"
