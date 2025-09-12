#!/bin/bash

# Script para preparar o projeto para deploy

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 PREPARANDO PARA DEPLOY${NC}"
echo -e "${BLUE}═══════════════════════════${NC}"
echo ""

# 1. Criar .gitignore apropriado
echo -e "${YELLOW}📝 Criando .gitignore...${NC}"
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

# Streamlit
.streamlit/secrets.toml

# ChromaDB (muito grande para deploy)
chromadb_storage/

# PDFs (muito grandes)
pdfs_downloaded/

# Logs e dados locais
data/*.log
data/*.pid
data/*.out
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Env files
.env
.env.local

# Temp files
tmp/
temp/
EOF

echo -e "${GREEN}✓ .gitignore criado${NC}"

# 2. Criar README para GitHub
echo -e "${YELLOW}📝 Criando README.md...${NC}"
cat > README.md << 'EOF'
# 🖨️ Chatbot Epson - Suporte Inteligente

Sistema de suporte automatizado para impressoras Epson com IA.

## ✨ Features

- 🤖 Respostas inteligentes powered by Gemini AI
- 🔍 Busca semântica com ChromaDB
- 💬 Interface conversacional moderna
- 📚 Base de conhecimento de 12+ modelos Epson
- ⚡ Respostas instantâneas
- 🎨 Tema escuro elegante

## 🚀 Demo

[Acesse a demo online →](https://seu-app.streamlit.app)

## 🛠️ Tecnologias

- **Frontend**: Streamlit
- **IA**: Google Gemini API
- **Busca**: ChromaDB (embeddings)
- **Backend**: Python 3.9+

## 📦 Instalação Local

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/chatbot-epson.git
cd chatbot-epson

# Instale dependências
pip install -r requirements.txt

# Execute
streamlit run app_streamlit.py
```

## 🔧 Configuração

1. Obtenha uma API key do Google Gemini
2. Configure em `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "sua_chave_aqui"
```

## 📝 Feedback

Sua opinião é importante! Teste o sistema e envie sugestões.

## 📄 Licença

Proprietário - Epson © 2024
EOF

echo -e "${GREEN}✓ README.md criado${NC}"

# 3. Verificar requirements.txt
echo -e "${YELLOW}🔍 Verificando requirements.txt...${NC}"
if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}✓ requirements.txt existe${NC}"
else
    echo -e "${YELLOW}Criando requirements.txt...${NC}"
    pip freeze | grep -E "streamlit|chromadb|sentence-transformers|google-generativeai|python-dotenv|pandas|numpy" > requirements.txt
    echo -e "${GREEN}✓ requirements.txt criado${NC}"
fi

# 4. Criar arquivo de exemplo para ChromaDB
echo -e "${YELLOW}📦 Preparando dados mínimos...${NC}"
if [ ! -f "chromadb_minimal.tar.gz" ]; then
    if [ -d "chromadb_storage" ]; then
        # Compactar apenas arquivos essenciais
        tar -czf chromadb_minimal.tar.gz chromadb_storage/*.sqlite3 2>/dev/null || true
        echo -e "${GREEN}✓ ChromaDB compactado${NC}"
    fi
fi

# 5. Inicializar Git se necessário
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}🔧 Inicializando Git...${NC}"
    git init
    git add .
    git commit -m "Initial commit - Chatbot Epson"
    echo -e "${GREEN}✓ Git inicializado${NC}"
else
    echo -e "${GREEN}✓ Git já inicializado${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✅ PROJETO PRONTO PARA DEPLOY!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Próximos passos:${NC}"
echo ""
echo "1. Crie um repositório no GitHub:"
echo "   ${YELLOW}https://github.com/new${NC}"
echo ""
echo "2. Conecte ao GitHub:"
echo "   ${YELLOW}git remote add origin https://github.com/SEU_USUARIO/chatbot-epson.git${NC}"
echo "   ${YELLOW}git push -u origin main${NC}"
echo ""
echo "3. Deploy no Streamlit Cloud:"
echo "   ${YELLOW}https://share.streamlit.io${NC}"
echo ""
echo "4. Configure secrets no Streamlit Cloud:"
echo "   Settings > Secrets > Adicione:"
echo "   ${YELLOW}GEMINI_API_KEY = \"sua_chave\"${NC}"
echo ""
echo -e "${GREEN}📚 Veja DEPLOY_GUIDE.md para mais opções!${NC}"
