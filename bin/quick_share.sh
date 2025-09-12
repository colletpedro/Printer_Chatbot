#!/bin/bash

# Script para compartilhar rapidamente via ngrok

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}🌐 COMPARTILHAMENTO RÁPIDO - CHATBOT EPSON${NC}"
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo ""

# Verificar se ngrok está instalado
if ! command -v ngrok &> /dev/null; then
    echo -e "${YELLOW}⚠️  Ngrok não encontrado!${NC}"
    echo ""
    echo "Instale o ngrok:"
    echo ""
    echo "  macOS:    ${GREEN}brew install ngrok${NC}"
    echo "  Linux:    ${GREEN}snap install ngrok${NC}"
    echo "  Windows:  ${GREEN}choco install ngrok${NC}"
    echo ""
    echo "Ou baixe em: ${BLUE}https://ngrok.com/download${NC}"
    exit 1
fi

# Matar processos antigos
echo -e "${YELLOW}🧹 Limpando processos...${NC}"
./kill_streamlit.sh > /dev/null 2>&1

# Iniciar Streamlit
echo -e "${YELLOW}🚀 Iniciando servidor local...${NC}"
./start.sh > /dev/null 2>&1 &
STREAMLIT_PID=$!

# Aguardar servidor iniciar
echo -n "Aguardando servidor"
for i in {1..10}; do
    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Iniciar ngrok
echo -e "${YELLOW}🌐 Criando túnel público...${NC}"
ngrok http 8501 > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Aguardar ngrok iniciar
sleep 3

# Obter URL pública
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | cut -d'"' -f4 | head -1)

if [ -z "$PUBLIC_URL" ]; then
    echo -e "${RED}❌ Erro ao criar túnel público${NC}"
    kill $STREAMLIT_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    exit 1
fi

# Exibir informações
clear
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}              ✨ CHATBOT ONLINE E COMPARTILHÁVEL!            ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}🌐 URL PÚBLICA:${NC}"
echo -e "${YELLOW}   $PUBLIC_URL${NC}"
echo ""
echo -e "${CYAN}📱 QR Code para compartilhar:${NC}"
echo ""

# Gerar QR Code (se qrencode estiver instalado)
if command -v qrencode &> /dev/null; then
    qrencode -t UTF8 "$PUBLIC_URL"
else
    echo "   [Instale qrencode para ver QR Code]"
    echo "   ${GREEN}brew install qrencode${NC}"
fi

echo ""
echo -e "${GREEN}📋 Compartilhe este link:${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "🚀 Teste nosso Chatbot Epson!"
echo ""
echo "🔗 $PUBLIC_URL"
echo ""
echo "✨ Features:"
echo "• Respostas instantâneas sobre impressoras"
echo "• Interface moderna com tema escuro"
echo "• Powered by IA (Gemini)"
echo ""
echo "📝 Seu feedback é importante!"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo -e "${YELLOW}⚠️  Este link é temporário (8 horas)${NC}"
echo -e "${YELLOW}    Para parar: Ctrl+C${NC}"
echo ""

# Função de limpeza
cleanup() {
    echo -e "\n${YELLOW}Encerrando...${NC}"
    kill $STREAMLIT_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    ./kill_streamlit.sh > /dev/null 2>&1
    echo -e "${GREEN}✓ Servidor encerrado${NC}"
    exit 0
}

# Configurar trap para Ctrl+C
trap cleanup INT TERM

# Manter rodando
while true; do
    sleep 1
    # Verificar se os processos ainda estão rodando
    if ! kill -0 $STREAMLIT_PID 2>/dev/null || ! kill -0 $NGROK_PID 2>/dev/null; then
        echo -e "${RED}❌ Servidor parou inesperadamente${NC}"
        cleanup
    fi
done
