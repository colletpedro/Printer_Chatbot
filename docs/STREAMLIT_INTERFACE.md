# 🖨️ Interface Streamlit - Chatbot Epson

## 📋 Visão Geral

Interface web moderna e responsiva para o Chatbot Epson, desenvolvida com Streamlit. Oferece uma experiência de usuário intuitiva para obter suporte técnico sobre impressoras Epson EcoTank.

## ✨ Características

### Interface Principal
- **Design Moderno**: Interface limpa e profissional com tema Epson
- **Chat Interativo**: Histórico completo de conversas com timestamps
- **Detecção Automática**: Identifica automaticamente o modelo da impressora
- **Busca Semântica**: Powered by ChromaDB com embeddings ML

### Recursos Avançados
- **Dois Modos de Resposta**:
  - 🚀 **Modo Rápido**: Respostas concisas em 3-4 passos
  - 📖 **Modo Detalhado**: Explicações completas com contexto

- **Controles de Rate Limiting**:
  - Máximo 8 perguntas por minuto
  - Intervalo mínimo de 4 segundos entre perguntas
  - Indicadores visuais de limite

- **Gestão de Histórico**:
  - Visualização completa de todas as conversas
  - Download do histórico em formato JSON
  - Limpeza com um clique

## 🚀 Como Executar

### Método 1: Script Automatizado (Recomendado)
```bash
cd /Users/pedrocollet/Downloads/GeminiMGI_Apresentacao
./executables/run_streamlit.sh
```

### Método 2: Execução Manual
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências (se necessário)
pip install -r requirements_streamlit.txt

# Executar aplicação
streamlit run app_streamlit.py
```

### Método 3: Com Configurações Personalizadas
```bash
streamlit run app_streamlit.py \
    --server.port 8501 \
    --server.address localhost \
    --theme.base light \
    --theme.primaryColor "#1c83e1"
```

## 📦 Instalação de Dependências

### Requisitos Principais
```bash
pip install -r requirements_streamlit.txt
```

### Dependências:
- `streamlit==1.29.0` - Framework web
- `chromadb==0.4.18` - Banco de dados vetorial
- `sentence-transformers==2.2.2` - Embeddings ML
- `google-generativeai==0.3.2` - API Gemini
- `python-dotenv==1.0.0` - Variáveis de ambiente

## 🎨 Personalização

### Temas e Cores
O arquivo `app_streamlit.py` inclui CSS customizado que pode ser modificado:

```python
# Cores principais
primary_color = "#1c83e1"  # Azul Epson
background_color = "#f0f8ff"  # Azul claro
```

### Configurações do Sistema
Edite as constantes no início do arquivo:

```python
# Rate limiting
MIN_REQUEST_INTERVAL = 4  # segundos
MAX_REQUESTS_PER_MINUTE = 8

# API Key
GEMINI_API_KEY = "sua_chave_aqui"
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente
```bash
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0  # Para acesso externo
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

### Deploy em Produção

#### 1. Deploy Local com HTTPS
```bash
streamlit run app_streamlit.py \
    --server.enableCORS false \
    --server.enableXsrfProtection true \
    --server.sslCertFile /path/to/cert.pem \
    --server.sslKeyFile /path/to/key.pem
```

#### 2. Deploy com Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements_streamlit.txt .
RUN pip install -r requirements_streamlit.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app_streamlit.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0"]
```

#### 3. Deploy na Nuvem

**Streamlit Cloud (Recomendado para MVP)**:
1. Faça push do código para GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte seu repositório
4. Configure as variáveis de ambiente
5. Deploy automático!

**Heroku**:
```bash
# Procfile
web: sh setup.sh && streamlit run app_streamlit.py

# setup.sh
mkdir -p ~/.streamlit/
echo "[server]\nport = $PORT\nenableCORS = false\n" > ~/.streamlit/config.toml
```

## 📊 Métricas e Monitoramento

### Estatísticas Disponíveis
- Total de perguntas realizadas
- Modelos de impressora mais consultados
- Taxa de sucesso das respostas
- Tempo médio de resposta

### Logs
O sistema gera logs em:
- `data/streamlit.log` - Logs da aplicação
- `data/chromadb_queries.log` - Consultas ao ChromaDB

## 🔍 Solução de Problemas

### Erro: ChromaDB não inicializado
```bash
# Execute primeiro:
python scripts/sync_drive_chromadb.py
```

### Erro: Porta 8501 em uso
```bash
# Use outra porta:
streamlit run app_streamlit.py --server.port 8502
```

### Performance lenta
1. Verifique a conexão com internet (API Gemini)
2. Otimize o ChromaDB:
```bash
python scripts/cleanup_chromadb.py
```

## 🎯 Roadmap Futuro

### v1.1 - Melhorias de UX
- [ ] Sugestões automáticas de perguntas
- [ ] Preview de respostas antes de enviar
- [ ] Modo escuro
- [ ] Suporte multi-idioma

### v1.2 - Recursos Avançados
- [ ] Analytics dashboard
- [ ] Exportação para PDF
- [ ] Integração com WhatsApp Business
- [ ] Cache de respostas frequentes

### v2.0 - Enterprise
- [ ] Autenticação de usuários
- [ ] Multi-tenancy
- [ ] API REST
- [ ] Webhooks para notificações

## 📝 Notas de Desenvolvimento

### Estrutura do Código
```
app_streamlit.py
├── Configurações iniciais
├── CSS customizado
├── Estado da sessão
├── Funções auxiliares
│   ├── initialize_system()
│   ├── check_rate_limit()
│   ├── detect_printer()
│   ├── semantic_search()
│   └── generate_response()
├── Interface principal
│   ├── Header
│   ├── Sidebar
│   ├── Chat area
│   └── Footer
└── Main execution
```

### Boas Práticas
1. **Cache**: Use `@st.cache_resource` para recursos pesados
2. **Estado**: Mantenha estado mínimo em `st.session_state`
3. **Recarregamento**: Use `st.rerun()` com moderação
4. **Performance**: Minimize chamadas à API

## 🤝 Contribuindo

Para contribuir com melhorias:
1. Faça fork do projeto
2. Crie uma branch para sua feature
3. Teste localmente
4. Envie pull request

## 📄 Licença

Sistema proprietário Epson. Uso interno apenas.

## 📞 Suporte

Para dúvidas ou problemas:
- Email: suporte@epson.com.br
- Documentação: `/docs`
- Issues: GitHub do projeto

---

**Última atualização**: Dezembro 2024  
**Versão**: 1.0.0  
**Status**: Pronto para Deploy MVP
