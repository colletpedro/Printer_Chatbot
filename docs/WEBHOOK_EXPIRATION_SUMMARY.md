# 📅 Resumo: Expiração de Webhooks

## 🕐 **O que significa "Webhook expira em 23h"?**

O **Google Drive limita webhooks a 7 dias** por segurança. Após esse período, eles param de funcionar automaticamente.

## ⏰ **Timeline de Expiração**

| Status | Ação Necessária |
|--------|----------------|
| `✅ Webhook ativo (expira em 5 dias)` | ✅ Nenhuma ação |
| `⚠️ Webhook ativo (expira em 47h) - Considere renovar` | 🔄 Planeje renovação |
| `⚠️ Webhook ativo (expira em 23h) - RENOVAR LOGO!` | 🚨 Renovar hoje |
| `❌ Webhook EXPIRADO - Execute: python renew_webhook.py` | ❌ Renovar agora |

## 🔄 **Processo de Renovação (2 opções)**

### **Opção 1: Automática (Recomendada) - 30 segundos**
```bash
source venv/bin/activate
python renew_webhook.py
```

### **Opção 2: Manual - 5 minutos**
1. `ngrok http 8080` (em terminal separado)
2. `pkill -f webhook_server.py`
3. `WEBHOOK_SECRET="webhook-secret-123" python webhook_server.py &`
4. `python setup_webhook.py` → Opção 1 → URL do ngrok → Token: webhook-secret-123

## 📋 **Checklist Semanal**

**Toda Segunda-feira:**
- [ ] Verificar status no chatbot
- [ ] Se < 48h, executar `python renew_webhook.py`
- [ ] Confirmar funcionamento com teste de PDF

## 🚨 **Sinais de Webhook Expirado**

1. **No chatbot**: Status mostra "❌ Webhook EXPIRADO"
2. **PDFs novos**: Não são detectados automaticamente
3. **Logs vazios**: `webhook.log` para de receber notificações

## 💡 **Dicas Importantes**

1. **Configure lembrete**: Toda segunda-feira, verificar status
2. **Mantenha ngrok rodando**: Deixe sempre ativo em segundo plano
3. **Use o script automático**: `python renew_webhook.py` faz tudo sozinho
4. **Teste regularmente**: Adicione PDFs de teste para confirmar funcionamento

## 🎯 **Resumo Executivo**

- **Frequência**: Renovar a cada 6-7 dias
- **Tempo**: 30 segundos com script automático
- **Comando**: `python renew_webhook.py`
- **Lembrete**: Configure no calendário para segundas-feiras

**O sistema avisa automaticamente quando precisa renovar!** 🔔 