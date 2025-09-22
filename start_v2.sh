#!/bin/bash

# Script para iniciar o Streamlit com a versão 2 (melhorada)

echo "🚀 Iniciando Chatbot Epson V2 - Sistema de Afunilamento Melhorado"
echo "=================================================="
echo ""
echo "📌 MELHORIAS IMPLEMENTADAS:"
echo "  ✅ Uma pergunta por vez"
echo "  ✅ Sem loops de perguntas repetidas"
echo "  ✅ Análise contextual inteligente"
echo "  ✅ Não responde quando não entende (após tentativas)"
echo ""
echo "=================================================="
echo ""

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    echo "🔧 Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Limpar cache do Streamlit
echo "🧹 Limpando cache do Streamlit..."
rm -rf ~/.streamlit/cache/

# Iniciar Streamlit com a versão 2
echo "🖨️ Iniciando aplicação V2..."
echo ""
echo "📍 Acesse em: http://localhost:8501"
echo ""
echo "Para parar: Pressione Ctrl+C"
echo "=================================================="
echo ""

streamlit run app_streamlit_v2.py
