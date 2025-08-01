# 🤖 Chatbot Epson - Sistema Inteligente

Sistema automatizado de suporte técnico para impressoras Epson com detecção automática de novos PDFs via webhook.

## 📁 Estrutura do Projeto

```
GeminiMGI/
├── 🤖 core/                    # Sistema principal
│   ├── chatbot.py             # Aplicação principal do chatbot
│   ├── extract_pdf_complete.py # Processamento de PDFs
│   ├── update_drive.py        # Atualização automática do Drive
│   └── key.json              # Credenciais do Google Drive
│
├── 🔗 webhook/                # Sistema de webhook
│   ├── webhook_server.py      # Servidor webhook
│   ├── setup_webhook.py       # Gerenciamento de webhooks
│   ├── renew_webhook.py       # Renovação automática
│   ├── test_webhook.py        # Testes do webhook
│   └── requirements_webhook.txt # Dependências
│
├── 📊 data/                   # Dados e logs
│   ├── manual_complete.json   # Base de conhecimento
│   ├── webhook_channels.json  # Canais ativos
│   ├── webhook_activity.json  # Log de atividades
│   ├── webhook.log           # Logs detalhados
│   ├── printer_metadata_generated.json # Metadados das impressoras
│   └── processing_log.json   # Log de processamento
│
├── 🛠️ scripts/               # Scripts auxiliares
│   └── generate_printer_metadata.py # Geração automática de metadados
│
├── 📝 docs/                  # Documentação
│   ├── WEBHOOK_SETUP_GUIDE.md
│   ├── WEBHOOK_RENEWAL_GUIDE.md
│   ├── AUTO_RELOAD_SYSTEM.md
│   └── ...
│
├── 📁 pdfs_downloaded/       # PDFs baixados do Drive
├── 🐍 venv/                  # Ambiente virtual Python
└── 📜 Scripts de conveniência
    ├── run_chatbot.sh        # Executar chatbot
    ├── run_webhook_server.sh # Executar webhook server
    └── renew_webhook.sh      # Renovar webhook
```

## 🚀 Como Usar

### **Executar o Chatbot:**
```bash
./run_chatbot.sh
# ou
source venv/bin/activate && python core/chatbot.py
```

### **Iniciar Sistema de Webhook:**
```bash
# 1. Iniciar ngrok (terminal separado)
ngrok http 8080

# 2. Iniciar webhook server
./run_webhook_server.sh

# 3. Configurar webhook (primeira vez)
source venv/bin/activate && python webhook/setup_webhook.py
```

### **Renovar Webhook (a cada 24h):**
```bash
./renew_webhook.sh
# ou
source venv/bin/activate && python webhook/renew_webhook.py
```

## ✨ Funcionalidades

- 🤖 **Chatbot inteligente** com detecção automática de modelos
- 🔄 **Auto-reload** da base de conhecimento
- 📡 **Webhook automático** para detecção de novos PDFs
- 🔧 **Geração automática** de metadados para novos modelos
- 📊 **Logs detalhados** de todas as operações

## 🎯 Fluxo Automatizado

1. PDF adicionado no Google Drive
2. Webhook detecta mudança automaticamente
3. Base de conhecimento é atualizada
4. Metadados são gerados para novos modelos
5. Chatbot detecta e recarrega automaticamente
6. Novo modelo fica disponível instantaneamente

**Sistema completamente automatizado!** 🎉 