#!/bin/bash

# Vai para o diretório do script
cd "$( dirname "${BASH_SOURCE[0]}" )"

# MATA TODOS os processos Streamlit existentes com força
pkill -9 -f "streamlit run" 2>/dev/null
pkill -9 -f "app_streamlit.py" 2>/dev/null
sleep 2

# Ativa ambiente
source venv/bin/activate

# Função para limpar ao sair
cleanup() {
    echo -e "\n🛑 Encerrando servidor..."
    pkill -9 -f "streamlit run" 2>/dev/null
    pkill -9 -f "app_streamlit.py" 2>/dev/null
    echo "✅ Servidor encerrado completamente"
    exit 0
}

# Configura trap para Ctrl+C
trap cleanup INT TERM

# Roda Streamlit
streamlit run app_streamlit.py --server.port 8501 --server.address localhost --theme.base dark
