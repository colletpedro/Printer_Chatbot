# 🔄 Guia de Renovação de Webhook

## 📋 Quando Renovar?

Renove o webhook quando:
- ✅ Status mostrar "❌ Webhook expirado"
- ✅ Status mostrar "⚠️ Webhook ativo (expira em menos de 24h)"
- ✅ PDFs novos não estão sendo detectados automaticamente

## 🛠️ Processo de Renovação (5 minutos)

### **Passo 1: Verificar Status Atual**
```bash
source venv/bin/activate
python setup_webhook.py
# Escolha opção 2 (List active webhooks)
```

### **Passo 2: Parar Webhooks Expirados**
```bash
# No mesmo script, escolha opção 4 (Stop all webhooks)
```

### **Passo 3: Verificar ngrok**
```bash
# Em um terminal separado:
ngrok http 8080
```
- Copie a URL HTTPS (ex: `https://abc123.ngrok-free.app`)

### **Passo 4: Reiniciar Webhook Server**
```bash
# Mate processos antigos:
pkill -f webhook_server.py

# Inicie novo servidor:
source venv/bin/activate
WEBHOOK_SECRET="webhook-secret-123" python webhook_server.py &
```

### **Passo 5: Registrar Novo Webhook**
```bash
python setup_webhook.py
# Escolha opção 1 (Setup new webhook)
# URL: https://SUA_URL_NGROK.ngrok-free.app/drive-webhook
# Token: webhook-secret-123
```

### **Passo 6: Testar**
```bash
python test_webhook.py
# Verifique se está funcionando
```

## 🤖 Processo Automatizado (Recomendado)

### **Script de Renovação Automática**
Vou criar um script que faz tudo isso automaticamente:

```bash
# Comando único para renovar tudo:
python renew_webhook.py
```

## ⏰ Frequência de Renovação

- **Google Drive**: Webhooks expiram em **7 dias**
- **Recomendação**: Renovar a cada **6 dias** (1 dia antes)
- **Lembrete**: Configure um lembrete no calendário

## 🔔 Sinais de que o Webhook Expirou

1. **No chatbot**: Status mostra "❌ Webhook expirado"
2. **Teste manual**: Adicionar PDF no Drive não gera logs
3. **Logs vazios**: `webhook.log` não recebe notificações novas
4. **Erro 404**: ngrok mostra erro ao tentar acessar webhook

## 📝 Checklist de Renovação

- [ ] Verificar status atual
- [ ] Parar webhooks antigos  
- [ ] Confirmar ngrok rodando
- [ ] Reiniciar webhook_server.py
- [ ] Registrar novo webhook
- [ ] Testar com PDF de exemplo
- [ ] Confirmar chatbot detecta atualizações

## 🚨 Troubleshooting

### Problema: "Address already in use"
```bash
lsof -ti:8080 | xargs kill
```

### Problema: "ngrok not found"
```bash
brew install ngrok/ngrok/ngrok
```

### Problema: "Invalid webhook notification"
- Verificar se WEBHOOK_SECRET está correto
- Confirmar URL do ngrok está atualizada

## 💡 Dicas

1. **Mantenha ngrok rodando**: Deixe sempre ativo em segundo plano
2. **Use screen/tmux**: Para manter processos rodando após fechar terminal
3. **Documente URLs**: Anote a URL do ngrok atual
4. **Teste regularmente**: Adicione PDFs de teste periodicamente 