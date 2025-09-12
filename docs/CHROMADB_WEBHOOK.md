# Sistema de Webhook ChromaDB

## 📋 Visão Geral

Sistema de webhook automatizado que monitora alterações no Google Drive e executa automaticamente o script `update_chromadb.sh` para manter o ChromaDB sempre atualizado.

## 🎯 Objetivo

Automatizar completamente a sincronização entre Google Drive e ChromaDB, eliminando a necessidade de executar manualmente o script de atualização quando PDFs são adicionados, modificados ou removidos.

## 🏗️ Arquitetura

```
Google Drive (PDFs)
      ↓
  [Alteração detectada]
      ↓
Webhook Notification → Servidor Webhook (porta 8080)
                              ↓
                    Executa update_chromadb.sh
                              ↓
                       ChromaDB Atualizado
```

## 📁 Estrutura de Arquivos

### Novos Arquivos Criados

```
webhook/
├── chromadb_webhook_server.py    # Servidor principal do webhook
├── register_chromadb_webhook.py  # Script de registro no Google Drive
└── test_chromadb_webhook.py      # Script de teste do webhook

executables/
├── run_chromadb_webhook.sh       # Inicia o servidor webhook
├── register_chromadb_webhook.sh  # Registra webhook no Drive
└── test_chromadb_webhook.sh      # Testa o webhook

data/
├── chromadb_webhook_config.json    # Configuração do webhook
├── chromadb_webhook_activity.json  # Log de atividades
└── chromadb_webhook.log            # Log detalhado do servidor
```

## 🚀 Guia de Instalação

### 1. Instalar Dependências

```bash
# Flask para o servidor
pip install flask

# Google API Client (se ainda não instalado)
pip install google-api-python-client google-auth

# Requests para testes
pip install requests
```

### 2. Configurar Servidor Webhook

```bash
# Tornar executável
chmod +x executables/run_chromadb_webhook.sh

# Iniciar servidor
./executables/run_chromadb_webhook.sh
```

O servidor iniciará na porta 8080 por padrão.

### 3. Expor com Ngrok (para desenvolvimento/teste)

Em outro terminal:

```bash
# Instalar ngrok se necessário
# Mac: brew install ngrok
# Linux: snap install ngrok

# Expor porta 8080
ngrok http 8080
```

Copie a URL HTTPS fornecida (exemplo: `https://abc123.ngrok.io`)

### 4. Registrar Webhook no Google Drive

```bash
# Tornar executável
chmod +x executables/register_chromadb_webhook.sh

# Registrar webhook
./executables/register_chromadb_webhook.sh
```

Quando solicitado:
1. Escolha opção `1` (Registrar novo webhook)
2. Digite a URL do ngrok + `/webhook` (exemplo: `https://abc123.ngrok.io/webhook`)

### 5. Testar o Webhook

```bash
# Tornar executável
chmod +x executables/test_chromadb_webhook.sh

# Testar
./executables/test_chromadb_webhook.sh
```

## 📡 Endpoints do Servidor

### `POST /webhook`
- **Descrição**: Recebe notificações do Google Drive
- **Ação**: Executa `update_chromadb.sh` quando detecta mudanças
- **Headers necessários**: 
  - `X-Goog-Channel-Token`: Token de autenticação
  - `X-Goog-Resource-State`: Estado do recurso (update, sync, etc.)

### `GET /health`
- **Descrição**: Verifica se o servidor está funcionando
- **Resposta**: Status do servidor e verificações básicas

### `POST /test-update`
- **Descrição**: Executa manualmente o script de atualização
- **Autenticação**: Requer header `Authorization: Bearer {WEBHOOK_SECRET}`
- **Uso**: Para testes e forçar atualização manual

### `GET /`
- **Descrição**: Página inicial com informações do servidor
- **Resposta**: Lista de endpoints disponíveis

## 🔐 Segurança

### Variáveis de Ambiente

```bash
# Definir secret customizado (recomendado para produção)
export WEBHOOK_SECRET="seu-secret-seguro-aqui"

# Definir porta customizada
export WEBHOOK_PORT=8080
```

### Token de Autenticação

O webhook verifica autenticação através de:
1. Header `X-Goog-Channel-Token` do Google Drive
2. HMAC signature para validação adicional

## 📊 Monitoramento

### Logs de Atividade

Visualizar atividade recente:
```bash
# Ver últimas atividades
cat data/chromadb_webhook_activity.json | jq '.'

# Ver log completo
tail -f data/chromadb_webhook.log
```

### Tipos de Eventos Registrados

- `server_started`: Servidor iniciado
- `webhook_received`: Notificação recebida
- `change_detected`: Mudança detectada no Drive
- `update_started`: Atualização iniciada
- `update_success`: Atualização concluída com sucesso
- `update_failed`: Erro na atualização
- `webhook_synced`: Webhook sincronizado com Drive

## ⏰ Renovação do Webhook

Webhooks do Google Drive expiram em 7 dias. Para renovar:

```bash
# Verificar status atual
./executables/test_chromadb_webhook.sh

# Re-registrar se necessário
./executables/register_chromadb_webhook.sh
```

## 🔧 Troubleshooting

### Servidor não inicia

```bash
# Verificar se porta está em uso
lsof -i:8080

# Usar porta diferente
export WEBHOOK_PORT=8081
./executables/run_chromadb_webhook.sh
```

### Webhook não recebe notificações

1. Verificar se ngrok está rodando
2. Confirmar URL correta no registro
3. Verificar logs: `tail -f data/chromadb_webhook.log`
4. Testar manualmente: `./executables/test_chromadb_webhook.sh`

### Script de atualização não executa

1. Verificar permissões: `ls -la executables/update_chromadb.sh`
2. Testar manualmente: `./executables/update_chromadb.sh`
3. Verificar logs de erro em `data/chromadb_webhook.log`

## 🌐 Deploy em Produção

Para ambiente de produção:

1. **Use HTTPS real** (não ngrok):
   - Configure reverse proxy (nginx/apache)
   - Use certificado SSL válido

2. **Configure como serviço systemd**:

```bash
# /etc/systemd/system/chromadb-webhook.service
[Unit]
Description=ChromaDB Webhook Server
After=network.target

[Service]
Type=simple
User=seu-usuario
WorkingDirectory=/caminho/para/GeminiMGI_Apresentacao
Environment="WEBHOOK_SECRET=seu-secret-seguro"
ExecStart=/usr/bin/python3 webhook/chromadb_webhook_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. **Configurar renovação automática**:

Adicionar ao crontab:
```bash
# Renovar webhook a cada 6 dias
0 0 */6 * * /caminho/para/executables/register_chromadb_webhook.sh
```

## 📝 Fluxo Completo de Uso

1. **Desenvolvimento/Teste**:
   ```bash
   # Terminal 1: Servidor
   ./executables/run_chromadb_webhook.sh
   
   # Terminal 2: Ngrok
   ngrok http 8080
   
   # Terminal 3: Registrar
   ./executables/register_chromadb_webhook.sh
   
   # Terminal 4: Testar
   ./executables/test_chromadb_webhook.sh
   ```

2. **Operação Normal**:
   - Adicione/modifique/remova PDFs no Google Drive
   - O webhook detecta automaticamente
   - ChromaDB é atualizado sem intervenção manual

## 🎯 Benefícios

- ✅ **Automação Total**: Sem necessidade de intervenção manual
- ✅ **Tempo Real**: Atualizações assim que mudanças ocorrem
- ✅ **Confiável**: Logs detalhados e sistema de retry
- ✅ **Simples**: Scripts bash para todas as operações
- ✅ **Testável**: Sistema completo de testes incluído

## 📞 Suporte

Em caso de problemas:

1. Verificar logs: `tail -f data/chromadb_webhook.log`
2. Testar webhook: `./executables/test_chromadb_webhook.sh`
3. Verificar status: `cat data/chromadb_webhook_config.json`
4. Re-registrar se necessário: `./executables/register_chromadb_webhook.sh`

---

**Versão**: 1.0.0  
**Data**: Janeiro 2025  
**Autor**: Sistema ChromaDB Webhook
