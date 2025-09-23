# 🖨️ Chatbot Epson - Frontend Streamlit com ChromaDB

## 📝 Descrição

Interface web moderna para o sistema de suporte técnico Epson, construída com Streamlit e integrada ao ChromaDB para busca semântica inteligente.

## ✨ Características Principais

### 🔍 Busca Semântica Avançada
- **ChromaDB Exclusivo**: Sistema baseado 100% em busca vetorial
- **Detecção Automática**: Identifica o modelo da impressora na pergunta
- **Contexto Inteligente**: Busca informações relevantes nos manuais

### 💬 Modos de Resposta
- **📖 Detalhado**: Explicações completas com passo a passo
- **⚡ Rápido**: Respostas diretas em 3-4 passos

### 🎨 Interface Moderna
- Design limpo e intuitivo
- Chat em tempo real
- Histórico de conversas
- Métricas de uso

## 🚀 Instalação e Execução

### Pré-requisitos
```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar ChromaDB (se ainda não configurado)
python scripts/sync_drive_chromadb.py
```

### Executar Localmente
```bash
# Método 1: Script de inicialização
./start.sh

# Método 2: Comando direto
streamlit run app_streamlit.py
```

### Acessar a Interface
```
http://localhost:8501
```

## 📋 Funcionalidades

### Barra Lateral
- **Seleção de Impressora**: Manual ou automática
- **Modo de Resposta**: Detalhado ou Rápido
- **Botão Atualizar**: Verifica novos dados
- **Limpar Chat**: Reinicia conversa
- **Status do Sistema**: ChromaDB e modelos disponíveis

### Chat Principal
- **Detecção Automática**: Identifica modelo na pergunta
- **Respostas Contextualizadas**: Baseadas nos manuais oficiais
- **Rate Limiting**: Controle de requisições
- **Indicadores Visuais**: Modelo e modo usado

### Métricas
- Contador de perguntas
- Modelos disponíveis
- Modo atual

## 🔧 Configuração

### API Key Gemini
O sistema usa a API do Google Gemini. Configure em `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "sua_chave_aqui"
```

Ou use a chave padrão incluída no código (para testes).

### ChromaDB
O sistema requer ChromaDB configurado com os manuais:

```bash
# Verificar se ChromaDB está configurado
ls chromadb_storage/

# Se não estiver, executar migração
python scripts/migrate_from_drive_to_chromadb.py
```

## 📊 Arquitetura

```
app_streamlit.py
    ↓
core/chatbot_chromadb.py
    ↓
ChromaDB (busca vetorial)
    ↓
Google Gemini API (geração de respostas)
```

### Fluxo de Dados
1. **Usuário** faz pergunta
2. **Detecção** do modelo de impressora
3. **Busca Semântica** no ChromaDB
4. **Geração** de resposta com Gemini
5. **Formatação** e exibição

## 🎯 Exemplos de Uso

### Perguntas com Detecção Automática
- "Como trocar tinta da L3150?"
- "Minha L4260 não está imprimindo"
- "Configurar Wi-Fi na L3250"

### Perguntas Genéricas (requer seleção manual)
- "Como limpar cabeças de impressão?"
- "Papel emperrado, o que fazer?"
- "Impressora não liga"

## 🐛 Solução de Problemas

### ChromaDB não inicializa
```bash
# Reinstalar ChromaDB
pip install --upgrade chromadb

# Verificar base de dados
python scripts/test_chromadb.py
```

### Rate Limiting
- Aguarde o tempo indicado entre perguntas
- Limite: 8 perguntas por minuto

### Modelo não detectado
- Selecione manualmente na barra lateral
- Inclua o modelo na pergunta

## 📈 Melhorias Futuras

- [ ] Cache de respostas frequentes
- [ ] Exportação de histórico
- [ ] Modo offline (respostas básicas)
- [ ] Integração com mais modelos
- [ ] Dashboard de analytics

## 📝 Notas de Desenvolvimento

### Estrutura de Arquivos
```
app_streamlit.py         # Frontend Streamlit
core/
  chatbot_chromadb.py    # Lógica principal
scripts/
  chromadb_integration.py # Integração ChromaDB
chromadb_storage/        # Base de dados vetorial
```

### Principais Funções
- `init_system()`: Inicializa ChromaDB
- `detect_printer_from_query()`: Detecta modelo
- `process_user_query()`: Processa pergunta
- `enhanced_search_chromadb()`: Busca semântica

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Add: Nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

## 📄 Licença

Projeto desenvolvido para demonstração técnica.

---

**Versão:** 2.0 | **Status:** ✅ Pronto para Produção
