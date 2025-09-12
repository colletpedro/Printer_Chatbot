## Documentação Unificada – GeminiMGI

> Sistema completo de chatbot com IA para suporte técnico de impressoras Epson, integrado ao ChromaDB para busca semântica e automações via Webhook.

### Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Instalação e Configuração](#instalação-e-configuração)
  - [Dependências Essenciais](#dependências-essenciais)
  - [ChromaDB](#chromadb)
  - [Webhook (Google Drive)](#webhook-google-drive)
- [Execução Rápida](#execução-rápida)
- [Sistema ChromaDB](#sistema-chromadb)
  - [Migração e Testes](#migração-e-testes)
  - [Modelos de Embedding (E5, BGE-M3, MiniLM)](#modelos-de-embedding-e5-bge-m3-minilm)
  - [Atualização Automática do ChromaDB](#atualização-automática-do-chromadb)
- [Chatbot: Detecção de Modelo e Afunilamento](#chatbot-detecção-de-modelo-e-afunilamento)
  - [Melhoria: Digitação Direta do Modelo](#melhoria-digitação-direta-do-modelo)
  - [Perguntas de Afunilamento](#perguntas-de-afunilamento)
  - [Exemplo Prático do Fluxo](#exemplo-prático-do-fluxo)
- [Webhook: Configuração, Renovação e Expiração](#webhook-configuração-renovação-e-expiração)
- [Auto-Reload da Base de Conhecimento](#auto-reload-da-base-de-conhecimento)
- [Limpeza de PDFs Removidos](#limpeza-de-pdfs-removidos)
- [Troubleshooting](#troubleshooting)
- [Comandos Úteis](#comandos-úteis)

---

## Visão Geral

O projeto GeminiMGI é um assistente técnico para impressoras Epson que combina:

- IA conversacional (Google Gemini)
- Busca semântica com ChromaDB (embeddings E5 como padrão)
- Automação por Webhook para manter a base atualizada
- Base de manuais de 9 modelos (L1300, L3110, L3150, L3250/L3251, L375, L4150, L4260, L5190, L6490)

Principais benefícios:

- Respostas precisas por similaridade semântica
- Atualizações automáticas quando PDFs mudam no Drive
- Fluxo para identificar o modelo da impressora mesmo quando o usuário não sabe o modelo

## Arquitetura

```
Google Drive ──▶ Webhook Server ──▶ Atualização de Base
       │                              │
       ▼                              ▼
    Chatbot  ◀────────────────────── ChromaDB (busca semântica)
```

## Estrutura do Projeto

```
GeminiMGI_Apresentacao/
├── core/                    # Núcleo (chatbot, extração, chaves)
├── chromadb_storage/        # Base ChromaDB (obrigatória)
├── scripts/                 # Migração, testes e utilitários
├── webhook/                 # Servidor e ferramentas de Webhook
├── docs/                    # Guias específicos
├── pdfs_downloaded/         # Manuais das impressoras
└── run_*.sh                 # Scripts de execução
```

## Instalação e Configuração

### Dependências Essenciais

1) Ambiente

```bash
python3 -m venv venv
source venv/bin/activate
```

2) Core

```bash
pip install requests PyPDF2
```

3) ChromaDB (recomendado)

```bash
pip install -r scripts/requirements_chromadb.txt
```

4) Webhook (opcional)

```bash
pip install -r webhook/requirements_webhook.txt
```

5) Chaves

- O arquivo `core/key.json` já contém as chaves necessárias para o projeto.

### ChromaDB

- Migrar a base: `python3 scripts/migrate_to_chromadb.py`
- Testar migração: `python3 scripts/test_chromadb.py`

Parâmetros úteis da migração:

```
--json data/manual_complete.json
--db ./chromadb_storage
--collection epson_manuals
--batch 128
--model intfloat/multilingual-e5-base
```

### Webhook (Google Drive)

1) Instalar dependências (ver acima)

2) Rodar servidor local

```bash
python3 webhook/webhook_server.py
```

3) Expor com ngrok (teste)

```bash
ngrok http 8080
```

4) Registrar webhook

```bash
python3 webhook/setup_webhook.py
# Opção 1 (Setup new webhook) e informe a URL HTTPS do ngrok
```

5) Validar

```bash
python3 webhook/test_webhook.py
```

## Execução Rápida

Chatbot (ChromaDB):

```bash
./run_chatbot_chromadb.sh
# ou
source venv/bin/activate && python3 core/chatbot_chromadb.py
```

Webhook server:

```bash
./run_webhook_server.sh
# ou
python3 webhook/webhook_server.py
```

## Sistema ChromaDB

### Migração e Testes

- Migração: `python3 scripts/migrate_to_chromadb.py`
- Testes: `python3 scripts/test_chromadb.py`
- Exemplo de integração: `python3 scripts/chromadb_integration_example.py`

Resultados esperados (validação):

- 5.184 documentos indexados
- 11 modelos de impressora
- Busca semântica respondendo por similaridade (melhor que busca textual)

Sobre a migração para 100% ChromaDB:

- Remoção de fallbacks JSON em cenários de produção
- Inicialização obriga a presença do ChromaDB
- Código mais enxuto e com performance superior

### Modelos de Embedding (E5, BGE-M3, MiniLM)

Presets suportados ao migrar:

```bash
# E5 (padrão recomendado)
python scripts/migrate_to_chromadb.py --model-preset multilingual-e5-base

# E5 small (mais rápido)
python scripts/migrate_to_chromadb.py --model-preset multilingual-e5-small

# BGE-M3 (máxima qualidade)
python scripts/migrate_to_chromadb.py --model-preset bge-m3

# Modelo customizado
python scripts/migrate_to_chromadb.py --model intfloat/multilingual-e5-large
```

Prefixos automáticos (aplicados no pipeline):

- Documentos: `passage: ...`
- Consultas: `query: ...`

Requisitos recomendados:

- ChromaDB >= 0.4.22
- sentence-transformers >= 2.2.2
- torch >= 1.9.0

### Atualização Automática do ChromaDB

O chatbot verifica atualizações de PDFs no início da execução e dispara a migração automaticamente quando necessário:

Fluxo resumido ao iniciar o chatbot:

1. Verifica mudanças na base (Drive/JSON)
2. Se houver, executa `scripts/migrate_to_chromadb.py`
3. Recarrega a coleção do ChromaDB
4. Prossegue com o chat usando a base atualizada

Vantagens:

- Zero intervenção manual
- Mantém o sistema sempre atualizado
- Tratamento de erros resiliente (se falhar, segue com a base atual)

## Chatbot: Detecção de Modelo e Afunilamento

O chatbot identifica o modelo da impressora de três formas:

1) Detecção automática por menções na pergunta (e aliases)
2) Digitação direta do modelo (L3110, 5190, Epson L6490, L 3250, etc.)
3) Afunilamento por perguntas estratégicas quando o usuário não sabe o modelo

### Melhoria: Digitação Direta do Modelo

- Usuário pode informar livremente: `L3110`, `Epson L4150`, `5190`, `L 3250` etc.
- O sistema normaliza e mapeia para o modelo correto
- Comandos de recuperação: `lista`, `sair`

### Perguntas de Afunilamento

1) Formato do papel: A4 vs A3+
2) Tipo de equipamento: só imprime vs multifuncional
3) FAX: possui ou não
4) ADF: bandeja superior para digitalização automática
5) Duplex: impressão frente e verso automática

Resultados esperados por característica:

- A3+: L6490, L1300
- Só imprime: L1300
- Com FAX: L5190, L6490
- Com ADF: L4150, L4260, L5190, L6490
- Com Duplex: L3250/L3251, L4150, L4260, L5190, L6490

### Exemplo Prático do Fluxo

```
Início: 9 modelos
→ Papel A4 → 7 modelos
→ Multifuncional → 7 modelos
→ Sem FAX → 6 modelos
→ Com ADF → 2 modelos (L4150, L4260)
→ Com Duplex → permanecem 2 modelos (L4150, L4260)
```

Ajustes de UX aplicados no chatbot:

- Remoção de emojis nas mensagens do terminal
- Remoção de medidas exatas (simplificação do texto)

## Webhook: Configuração, Renovação e Expiração

Configuração (resumo):

1) Instale dependências: `pip install -r webhook/requirements_webhook.txt`
2) Inicie servidor: `python3 webhook/webhook_server.py`
3) Exponha com ngrok: `ngrok http 8080`
4) Registre: `python3 webhook/setup_webhook.py` (Opção 1)
5) Teste: `python3 webhook/test_webhook.py`

Renovação:

- Webhooks do Google expiram em 7 dias
- Recomenda-se renovar a cada 6 dias
- Comando automatizado: `python3 webhook/renew_webhook.py`

Sinais de expiração:

- Chatbot indica expiração
- PDFs novos não disparam atualização
- Logs `webhook.log` sem eventos recentes

## Auto-Reload da Base de Conhecimento

O chatbot monitora atualizações:

- Na inicialização, verifica timestamps e status
- Durante a execução, pode realizar verificações periódicas
- Comando manual `reload` (quando aplicável)

Benefícios:

- Não exige reinício manual
- Verifica apenas quando necessário
- Mantém a experiência fluida

Observação: em ambientes 100% ChromaDB, a atualização do conteúdo efetiva ocorre via re-migração (automática quando habilitada).

## Limpeza de PDFs Removidos

Use quando PDFs forem removidos do Drive e você deseja refletir na base:

Opção shell (recomendada):

```bash
./cleanup_removed_pdfs.sh
```

Opção Python:

```bash
source venv/bin/activate
python3 scripts/cleanup_removed_pdfs.py
```

Como funciona (alto nível):

1) Lista PDFs no Drive e modelos correspondentes
2) Identifica seções órfãs em `data/manual_complete.json`
3) Exibe e confirma remoções
4) Atualiza a base com segurança

Cuidados:

- Operação é permanente; faça backup se necessário
- Reinicie o chatbot após a limpeza para refletir mudanças

## Troubleshooting

ChromaDB não disponível:

```bash
pip install -r scripts/requirements_chromadb.txt
python3 scripts/migrate_to_chromadb.py
```

Collection não existe:

```bash
python3 scripts/migrate_to_chromadb.py
```

Webhook não recebe notificações:

```bash
python3 webhook/test_webhook.py
python3 webhook/renew_webhook.py
tail -f webhook/webhook.log
```

Erros comuns (rede/memória/modelo):

- Reduza `--batch` na migração (p.ex. 64)
- Troque o modelo de embedding temporariamente
- Verifique conexão e permissões do Google Drive

## Comandos Úteis

Executar chatbot (ChromaDB):

```bash
./run_chatbot_chromadb.sh
```

Migrar/validar ChromaDB:

```bash
python3 scripts/migrate_to_chromadb.py
python3 scripts/test_chromadb.py
```

Webhook:

```bash
./run_webhook_server.sh
python3 webhook/setup_webhook.py
python3 webhook/test_webhook.py
python3 webhook/renew_webhook.py
```

Limpeza de PDFs removidos:

```bash
./cleanup_removed_pdfs.sh
```

---

### Notas de Implementação e Melhorias Recentes

- Detecção de modelo aprimorada por digitação direta
- Sistema de afunilamento com 5 perguntas estratégicas
- Ajustes de UX no terminal (sem emojis e medidas)
- Validações e correções consolidadas (sintaxe, metadados, testes)
- Opção por arquitetura 100% ChromaDB em produção


