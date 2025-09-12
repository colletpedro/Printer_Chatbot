#!/bin/bash

# Script para analisar o repositório antes da limpeza

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🔍 ANÁLISE DO REPOSITÓRIO${NC}"
echo -e "${CYAN}═══════════════════════════════════════════${NC}"
echo ""

# 1. ARQUIVOS DUPLICADOS/REDUNDANTES
echo -e "${RED}❌ ARQUIVOS PARA REMOVER:${NC}"
echo ""

echo -e "${YELLOW}Executáveis duplicados:${NC}"
[ -f "run.sh" ] && echo "   • run.sh (duplicado de start.sh)"
[ -f "chatbot.sh" ] && echo "   • chatbot.sh (versão antiga)"
[ -f "executables/run_streamlit.sh" ] && echo "   • executables/run_streamlit.sh (duplicado)"
[ -f "executables/run_chatbot.sh" ] && echo "   • executables/run_chatbot.sh (obsoleto)"
[ -f "executables/run_chatbot_chromadb.sh" ] && echo "   • executables/run_chatbot_chromadb.sh (obsoleto)"
[ -f "executables/deploy_streamlit.sh" ] && echo "   • executables/deploy_streamlit.sh (será movido)"

echo ""
echo -e "${YELLOW}Documentação duplicada:${NC}"
[ -f "README_STREAMLIT.md" ] && echo "   • README_STREAMLIT.md (consolidar no README principal)"
[ -f "executables/README.md" ] && echo "   • executables/README.md (desnecessário)"
[ -f "docs/README.md" ] && echo "   • docs/README.md (duplicado)"

echo ""
echo -e "${YELLOW}Requirements duplicados:${NC}"
[ -f "requirements_streamlit.txt" ] && echo "   • requirements_streamlit.txt"
[ -f "core/requirements.txt" ] && echo "   • core/requirements.txt"
[ -f "core/requirements_chromadb.txt" ] && echo "   • core/requirements_chromadb.txt"
[ -f "core/requirements_webhook.txt" ] && echo "   • core/requirements_webhook.txt"
[ -f "webhook/requirements_webhook.txt" ] && echo "   • webhook/requirements_webhook.txt"

echo ""
echo -e "${YELLOW}Arquivos temporários e logs:${NC}"
LOGS=$(find . -name "*.log" -o -name "*.pid" -o -name "*.out" 2>/dev/null | grep -v venv | head -10)
if [ ! -z "$LOGS" ]; then
    echo "$LOGS" | while read -r file; do
        echo "   • $file"
    done
    TOTAL_LOGS=$(find . -name "*.log" -o -name "*.pid" -o -name "*.out" 2>/dev/null | grep -v venv | wc -l)
    [ $TOTAL_LOGS -gt 10 ] && echo "   ... e mais $((TOTAL_LOGS - 10)) arquivos de log"
fi

echo ""
echo -e "${YELLOW}Cache Python:${NC}"
PYCACHE=$(find . -type d -name "__pycache__" | grep -v venv | head -5)
if [ ! -z "$PYCACHE" ]; then
    echo "$PYCACHE" | while read -r dir; do
        echo "   • $dir/"
    done
    TOTAL_PYCACHE=$(find . -type d -name "__pycache__" | grep -v venv | wc -l)
    [ $TOTAL_PYCACHE -gt 5 ] && echo "   ... e mais $((TOTAL_PYCACHE - 5)) pastas __pycache__"
fi

echo ""
echo -e "${YELLOW}Arquivos grandes (não devem ir para GitHub):${NC}"
[ -f "chromadb_minimal.tar.gz" ] && echo "   • chromadb_minimal.tar.gz ($(du -h chromadb_minimal.tar.gz 2>/dev/null | cut -f1))"
[ -d "chromadb_storage" ] && echo "   • chromadb_storage/ ($(du -sh chromadb_storage 2>/dev/null | cut -f1))"
[ -d "pdfs_downloaded" ] && echo "   • pdfs_downloaded/ ($(du -sh pdfs_downloaded 2>/dev/null | cut -f1))"
[ -d "venv" ] && echo "   • venv/ ($(du -sh venv 2>/dev/null | cut -f1))"

echo ""
echo -e "${BLUE}📁 REORGANIZAÇÃO PROPOSTA:${NC}"
echo ""

echo "ANTES:"
echo "."
echo "├── start.sh, run.sh, chatbot.sh (3 arquivos fazem a mesma coisa)"
echo "├── executables/ (12 scripts misturados)"
echo "├── themes/ (solto na raiz)"
echo "├── múltiplos READMEs espalhados"
echo "└── requirements duplicados"

echo ""
echo "DEPOIS:"
echo "."
echo "├── app_streamlit.py          # App principal"
echo "├── bin/                      # Executáveis essenciais"
echo "│   ├── start.sh             # Único script para iniciar"
echo "│   ├── kill_streamlit.sh    # Parar aplicação"
echo "│   ├── quick_share.sh       # Compartilhar"
echo "│   └── prepare_deploy.sh    # Deploy"
echo "├── config/                   # Todas as configurações"
echo "│   └── themes/              # Temas organizados"
echo "├── utils/                    # Scripts auxiliares"
echo "├── requirements.txt          # Único arquivo consolidado"
echo "└── README.md                 # Documentação unificada"

echo ""
echo -e "${GREEN}📊 ESTATÍSTICAS ATUAIS:${NC}"
echo ""

# Contar arquivos
TOTAL_FILES=$(find . -type f | wc -l)
PYTHON_FILES=$(find . -name "*.py" | wc -l)
SHELL_FILES=$(find . -name "*.sh" | wc -l)
MD_FILES=$(find . -name "*.md" | wc -l)

echo "   • Total de arquivos: $TOTAL_FILES"
echo "   • Arquivos Python: $PYTHON_FILES"
echo "   • Scripts Shell: $SHELL_FILES"
echo "   • Documentação (MD): $MD_FILES"

# Tamanho total
TOTAL_SIZE=$(du -sh . 2>/dev/null | cut -f1)
CLEAN_SIZE=$(du -sh . --exclude=venv --exclude=chromadb_storage --exclude=pdfs_downloaded --exclude="__pycache__" 2>/dev/null | cut -f1)

echo "   • Tamanho total: $TOTAL_SIZE"
echo "   • Tamanho sem venv/chromadb/pdfs: $CLEAN_SIZE"

echo ""
echo -e "${YELLOW}⚠️  AÇÕES RECOMENDADAS:${NC}"
echo ""
echo "1. Execute a limpeza:"
echo "   ${GREEN}chmod +x *.sh && ./cleanup_repo.sh${NC}"
echo ""
echo "2. Consolidar documentação:"
echo "   ${GREEN}./consolidate_docs.sh${NC}"
echo ""
echo "3. Verificar .gitignore:"
echo "   ${GREEN}cat .gitignore${NC}"
echo ""
echo "4. Commit limpo:"
echo "   ${GREEN}git add -A && git commit -m 'Clean and organize repository'${NC}"
echo ""

# Verificar se já tem .git
if [ -d ".git" ]; then
    echo -e "${BLUE}📌 Status Git atual:${NC}"
    MODIFIED=$(git status --porcelain 2>/dev/null | wc -l)
    echo "   • Arquivos modificados: $MODIFIED"
    
    # Tamanho que seria enviado
    echo "   • Estimativa para push: ~$CLEAN_SIZE"
fi
