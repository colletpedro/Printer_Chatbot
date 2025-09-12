#!/bin/bash

# Cores
BLUE='\033[0;34m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}🎨 SELETOR DE TEMAS - CHATBOT EPSON${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Escolha um tema:"
echo ""
echo -e "${GREEN}1)${NC} 🌙 Dark Elegant - Preto profundo com azul"
echo -e "${GREEN}2)${NC} 🌊 Dark Navy - Navy escuro com roxo"
echo -e "${GREEN}3)${NC} ⚫ Dark Carbon - Cinza carvão com ciano"
echo ""
read -p "Opção (1-3): " choice

case $choice in
    1)
        cp themes/dark_elegant.toml .streamlit/config.toml
        echo -e "\n${GREEN}✅ Tema Dark Elegant aplicado!${NC}"
        ;;
    2)
        cp themes/dark_navy.toml .streamlit/config.toml
        echo -e "\n${GREEN}✅ Tema Dark Navy aplicado!${NC}"
        ;;
    3)
        cp themes/dark_carbon.toml .streamlit/config.toml
        echo -e "\n${GREEN}✅ Tema Dark Carbon aplicado!${NC}"
        ;;
    *)
        echo -e "\n${RED}❌ Opção inválida${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}Execute ./start.sh para ver as mudanças${NC}"
