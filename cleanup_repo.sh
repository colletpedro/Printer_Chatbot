#!/bin/bash

# Script para limpar e organizar o repositório

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧹 LIMPEZA E ORGANIZAÇÃO DO REPOSITÓRIO${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

# 1. REMOVER ARQUIVOS DESNECESSÁRIOS
echo -e "${YELLOW}1. Removendo arquivos desnecessários...${NC}"

# Remover __pycache__ em todo o projeto
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Remover logs e arquivos temporários
rm -f data/*.log data/*.pid data/*.out 2>/dev/null
rm -f data/logs/*.log 2>/dev/null
rm -f data/*.json.bak 2>/dev/null
rm -f chromadb_minimal.tar.gz 2>/dev/null
rm -f *.log 2>/dev/null

# Remover executáveis duplicados/desnecessários
rm -f run.sh 2>/dev/null  # Duplicado do start.sh
rm -f chatbot.sh 2>/dev/null  # Versão antiga
rm -f executables/run_streamlit.sh 2>/dev/null  # Duplicado
rm -f executables/run_chatbot.sh 2>/dev/null  # Versão antiga
rm -f executables/run_chatbot_chromadb.sh 2>/dev/null  # Versão antiga
rm -f executables/deploy_streamlit.sh 2>/dev/null  # Movido para raiz

# Remover documentação duplicada/antiga
rm -f README_STREAMLIT.md 2>/dev/null  # Será consolidado no README principal
rm -f executables/README.md 2>/dev/null  # Desnecessário
rm -f docs/README.md 2>/dev/null  # Duplicado

echo -e "${GREEN}✓ Arquivos desnecessários removidos${NC}"

# 2. ORGANIZAR ESTRUTURA DE PASTAS
echo -e "${YELLOW}2. Organizando estrutura de pastas...${NC}"

# Criar estrutura organizada
mkdir -p bin  # Para executáveis principais
mkdir -p utils  # Para scripts utilitários
mkdir -p config  # Para configurações

# Mover executáveis principais para bin/
mv start.sh bin/ 2>/dev/null
mv kill_streamlit.sh bin/ 2>/dev/null
mv quick_share.sh bin/ 2>/dev/null
mv prepare_deploy.sh bin/ 2>/dev/null
mv change_theme.sh bin/ 2>/dev/null

# Mover scripts de webhook e ChromaDB para utils/
mv executables/update_chromadb.sh utils/ 2>/dev/null
mv executables/atualizar_chromadb.sh utils/ 2>/dev/null
mv executables/cleanup_removed_pdfs.sh utils/ 2>/dev/null
mv executables/register_chromadb_webhook.sh utils/ 2>/dev/null
mv executables/renew_webhook.sh utils/ 2>/dev/null
mv executables/run_chromadb_webhook.sh utils/ 2>/dev/null
mv executables/run_webhook_server.sh utils/ 2>/dev/null
mv executables/test_chromadb_webhook.sh utils/ 2>/dev/null

# Remover pasta executables vazia
rmdir executables 2>/dev/null

# Mover temas para config/
mv themes config/ 2>/dev/null

echo -e "${GREEN}✓ Estrutura reorganizada${NC}"

# 3. CONSOLIDAR REQUIREMENTS
echo -e "${YELLOW}3. Consolidando requirements...${NC}"

cat > requirements.txt << 'EOF'
# Chatbot Epson - Dependencies

# Core
streamlit==1.29.0
google-generativeai==0.3.2
python-dotenv==1.0.0

# Database & Search
chromadb==0.4.18
sentence-transformers==2.2.2

# Data Processing
pandas==2.1.4
numpy==1.24.3

# PDF Processing (optional)
PyPDF2==3.0.1
pdfplumber==0.9.0

# Google Drive Integration (optional)
google-api-python-client==2.108.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.1.0
EOF

# Remover requirements duplicados
rm -f requirements_streamlit.txt 2>/dev/null
rm -f core/requirements*.txt 2>/dev/null
rm -f webhook/requirements*.txt 2>/dev/null

echo -e "${GREEN}✓ Requirements consolidado${NC}"

# 4. CRIAR .GITIGNORE APROPRIADO
echo -e "${YELLOW}4. Criando .gitignore...${NC}"

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Streamlit
.streamlit/secrets.toml
.streamlit/*.toml.bak

# Data files (too large)
chromadb_storage/
pdfs_downloaded/
*.pdf

# Logs and temporary files
*.log
*.pid
*.out
data/*.log
data/*.pid
data/*.out
data/logs/

# Backups
*.bak
*.backup
*.tmp

# Environment
.env
.env.local

# Archives
*.tar.gz
*.zip

# Google Drive credentials
core/key.json
credentials.json
token.json
EOF

echo -e "${GREEN}✓ .gitignore criado${NC}"

# 5. LIMPAR PASTA DATA
echo -e "${YELLOW}5. Limpando pasta data...${NC}"

# Manter apenas arquivos essenciais
mkdir -p data_backup
mv data/manual_complete.json data_backup/ 2>/dev/null
mv data/printer_metadata_generated.json data_backup/ 2>/dev/null
rm -rf data/*
mv data_backup/* data/ 2>/dev/null
rmdir data_backup

echo -e "${GREEN}✓ Pasta data limpa${NC}"

# 6. CRIAR LINKS SIMBÓLICOS PARA COMPATIBILIDADE
echo -e "${YELLOW}6. Criando links para compatibilidade...${NC}"

ln -sf bin/start.sh start.sh 2>/dev/null
ln -sf bin/kill_streamlit.sh kill.sh 2>/dev/null

echo -e "${GREEN}✓ Links criados${NC}"

# 7. ESTATÍSTICAS
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ LIMPEZA CONCLUÍDA!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""

# Contar arquivos e tamanho
FILES_COUNT=$(find . -type f -not -path "./venv/*" -not -path "./.git/*" -not -path "./chromadb_storage/*" -not -path "./pdfs_downloaded/*" | wc -l)
DIR_SIZE=$(du -sh . --exclude=venv --exclude=.git --exclude=chromadb_storage --exclude=pdfs_downloaded 2>/dev/null | cut -f1)

echo -e "📊 Estatísticas:"
echo -e "   • Arquivos no projeto: ${FILES_COUNT}"
echo -e "   • Tamanho (sem venv/chromadb/pdfs): ${DIR_SIZE}"
echo ""

echo -e "${BLUE}📁 Nova estrutura:${NC}"
echo "."
echo "├── app_streamlit.py       # Aplicação principal"
echo "├── bin/                   # Executáveis principais"
echo "│   ├── start.sh          # Iniciar aplicação"
echo "│   ├── kill_streamlit.sh # Parar aplicação"
echo "│   ├── quick_share.sh    # Compartilhar via ngrok"
echo "│   └── prepare_deploy.sh # Preparar para deploy"
echo "├── config/               # Configurações"
echo "│   └── themes/          # Temas do Streamlit"
echo "├── core/                # Código principal"
echo "├── scripts/             # Scripts auxiliares"
echo "├── utils/               # Utilitários"
echo "├── webhook/             # Sistema de webhook"
echo "└── docs/                # Documentação"
echo ""

echo -e "${YELLOW}⚠️  Próximos passos:${NC}"
echo "1. Revise e execute: ./consolidate_docs.sh"
echo "2. Commit: git add -A && git commit -m 'Clean and organize repository'"
echo "3. Push: git push origin main"
