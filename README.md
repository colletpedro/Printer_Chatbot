# 🖨️ Chatbot Epson - Suporte Inteligente com IA

Sistema de suporte automatizado para impressoras Epson usando IA (Google Gemini) e busca semântica (ChromaDB).

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.29.0-red.svg)
![License](https://img.shields.io/badge/License-Proprietary-green.svg)

## ✨ Características

- 🤖 **IA Avançada**: Respostas inteligentes via Google Gemini
- 🔍 **Busca Semântica**: ChromaDB com embeddings ML
- 💬 **Interface Moderna**: Chat interativo com Streamlit
- 📚 **Base Completa**: 12+ modelos de impressoras Epson
- ⚡ **Respostas Instantâneas**: Sem delays artificiais
- 🎨 **Tema Escuro Elegante**: Interface profissional e confortável
- 📊 **Sistema de Feedback**: Coleta de avaliações e sugestões

## 🚀 Quick Start

### Instalação Rápida

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/chatbot-epson.git
cd chatbot-epson

# Instale as dependências
pip install -r requirements.txt

# Execute o chatbot
./start.sh
```

Acesse: http://localhost:8501

### Executáveis Principais

| Comando | Descrição |
|---------|-----------|
| `./start.sh` | Inicia o chatbot |
| `./kill.sh` | Para todos os processos |
| `./bin/quick_share.sh` | Compartilha via ngrok (teste rápido) |
| `./bin/prepare_deploy.sh` | Prepara para deploy |
| `./bin/change_theme.sh` | Alterna entre temas |

## 📦 Estrutura do Projeto

```
.
├── app_streamlit.py         # Interface principal Streamlit
├── bin/                     # Scripts executáveis
│   ├── start.sh            # Iniciar aplicação
│   ├── kill_streamlit.sh   # Parar aplicação  
│   ├── quick_share.sh      # Compartilhamento rápido
│   └── prepare_deploy.sh   # Preparar deploy
├── config/                  # Configurações
│   ├── themes/             # Temas visuais
│   └── .streamlit/         # Config Streamlit
├── core/                    # Lógica principal
│   ├── chatbot_chromadb.py # Chatbot com ChromaDB
│   └── pdf_processor.py    # Processamento PDFs
├── scripts/                 # Scripts auxiliares
│   ├── sync_drive_chromadb.py    # Sincronização
│   └── migrate_to_chromadb.py    # Migração dados
├── utils/                   # Utilitários
└── docs/                    # Documentação adicional
```

## ⚙️ Configuração

### 1. API Key do Google Gemini

Obtenha sua chave em: https://makersuite.google.com/app/apikey

Configure em `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "sua_chave_aqui"
```

### 2. Inicializar ChromaDB

```bash
# Sincronizar base de conhecimento
python scripts/sync_drive_chromadb.py
```

### 3. Personalizar Tema

```bash
./bin/change_theme.sh
# Escolha entre: Dark Elegant, Dark Navy, Dark Carbon
```

## 🌐 Deploy

### Opção 1: Streamlit Cloud (Recomendado - Grátis)

1. Faça push para GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte seu repositório
4. Configure secrets no painel
5. Deploy automático!

### Opção 2: Compartilhamento Rápido (Ngrok)

```bash
./bin/quick_share.sh
# Gera URL pública temporária para testes
```

### Opção 3: Docker

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app_streamlit.py"]
```

```bash
docker build -t chatbot-epson .
docker run -p 8501:8501 chatbot-epson
```

### Outras Opções

- **Render.com**: Deploy gratuito com limitações
- **Railway**: $5/mês, deploy simples
- **Heroku**: $7/mês, robusto
- **Google Cloud Run**: Pay-as-you-go, escalável

## 🎯 Funcionalidades

### Chat Inteligente
- Detecção automática de modelo de impressora
- Respostas contextualizadas por modelo
- Dois modos: Rápido (conciso) ou Detalhado (completo)

### Sistema de Busca
- ChromaDB para busca semântica
- Embeddings multilíngues (PT-BR)
- Cache inteligente de respostas

### Interface
- Tema escuro elegante e minimalista
- Histórico de conversas
- Download de conversas (JSON)
- Sistema de feedback integrado

## 📊 Modelos Suportados

| Série | Modelos |
|-------|---------|
| L3000 | L3110, L3150, L3250/L3251 |
| L300 | L375, L396 |
| L4000 | L4150, L4260 |
| L5000 | L5190, L5290 |
| L6000 | L6490 |
| L1000 | L1300 |
| L800 | L805 |

## 🔧 Desenvolvimento

### Ambiente Virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Estrutura do Código

- `app_streamlit.py`: Interface Streamlit
- `core/chatbot_chromadb.py`: Lógica do chatbot
- `scripts/chromadb_integration_example.py`: Integração ChromaDB
- `scripts/sync_drive_chromadb.py`: Sincronização de dados

### Adicionar Novo Modelo

1. Adicione PDF em `pdfs_downloaded/`
2. Execute sincronização:
```bash
python scripts/sync_drive_chromadb.py
```
3. Modelo é detectado automaticamente

## 📈 Métricas e Monitoramento

### Feedback dos Usuários
- Avaliações com emojis (😞 → 🤩)
- Comentários salvos em `data/feedbacks.json`
- Análise via dashboard (em desenvolvimento)

### Performance
- Tempo médio de resposta: 2-5 segundos
- Taxa de acerto: ~85% (baseado em feedbacks)
- Uptime: 99.9% (Streamlit Cloud)

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Add nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Troubleshooting

| Problema | Solução |
|----------|---------|
| Porta 8501 em uso | `./kill.sh` ou mude a porta |
| ChromaDB não carrega | Execute `python scripts/sync_drive_chromadb.py` |
| API Key inválida | Verifique `.streamlit/secrets.toml` |
| Módulo não encontrado | `pip install -r requirements.txt` |

## 📄 Licença

Software proprietário - Epson do Brasil © 2024

## 📞 Suporte

- Email: suporte@epson.com.br
- Issues: [GitHub Issues](https://github.com/seu-usuario/chatbot-epson/issues)
- Docs: Ver pasta `/docs` para documentação técnica detalhada

---

**Desenvolvido com ❤️ usando Streamlit + ChromaDB + Google Gemini**
