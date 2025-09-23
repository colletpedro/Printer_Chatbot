# 🚀 Guia de Deploy - Chatbot Epson Streamlit

## Deploy no Streamlit Community Cloud

### 📋 Pré-requisitos
- Conta no GitHub (já tem ✅)
- Repositório no GitHub (já tem ✅)
- Conta no Streamlit Cloud (criar se não tiver)

### 🔧 Passo a Passo

#### 1. Acesse o Streamlit Cloud
1. Vá para: https://share.streamlit.io/
2. Faça login com sua conta GitHub
3. Clique em **"New app"** ou **"Deploy an app"**

#### 2. Configure o Deploy
Preencha os campos:
- **Repository**: `colletpedro/Printer_Chatbot`
- **Branch**: `main`
- **Main file path**: `app_streamlit.py`

#### 3. Configure os Secrets (IMPORTANTE!)
1. Clique em **"Advanced settings"**
2. Na seção **"Secrets"**, adicione:

```toml
GEMINI_API_KEY = "AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk"
```

⚠️ **Nota**: Esta é sua chave API do Gemini. Se preferir usar outra, substitua aqui.

#### 4. Clique em Deploy
- O deploy levará alguns minutos (3-5 min normalmente)
- Você verá logs de instalação das dependências
- Quando concluído, receberá um link público

### 🔗 URL do App
Após o deploy, seu app estará disponível em:
```
https://[seu-usuario]-printer-chatbot.streamlit.app/
```

### 📱 Compartilhamento
O link pode ser compartilhado com qualquer pessoa! O app funciona em:
- Desktop 💻
- Tablet 📱
- Mobile 📱

### 🔄 Atualizações Automáticas
- Qualquer push para a branch `main` atualiza automaticamente o app
- Mudanças levam 1-2 minutos para aparecer

### ⚙️ Configurações Opcionais

#### Recursos do App
No painel do Streamlit Cloud, você pode ajustar:
- **Resources**: Aumentar RAM/CPU se necessário
- **Logs**: Ver logs em tempo real
- **Analytics**: Ver uso e visitantes

#### Domínio Customizado
1. Vá em Settings do app
2. Em "Custom subdomain", escolha um nome
3. Ficará: `https://[nome-escolhido].streamlit.app`

### 🐛 Troubleshooting

**Erro de importação ChromaDB?**
- O requirements.txt já está configurado corretamente

**Erro de API Key?**
- Verifique se adicionou a GEMINI_API_KEY nos Secrets

**App muito lento?**
- Normal no primeiro carregamento
- ChromaDB precisa inicializar na primeira vez

### 📊 Limites do Plano Gratuito
- 1 app público
- 1GB de armazenamento
- Recursos compartilhados
- Perfeito para este projeto!

### 🎯 Próximos Passos
1. Faça o deploy seguindo os passos acima
2. Teste o app com diferentes perguntas
3. Compartilhe o link com usuários teste
4. Monitore os logs para erros

## 💡 Dicas Pro

### Backup da API Key
Considere ter uma API key de backup configurada:
```python
# No código (app_streamlit.py):
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = st.secrets.get("BACKUP_API_KEY", "key-padrão")
```

### Monitoramento
- Ative notificações no Streamlit Cloud
- Receba alertas se o app cair
- Veja estatísticas de uso

---

## 📞 Suporte
Se tiver problemas:
1. Verifique os logs no Streamlit Cloud
2. Confirme que o GitHub está atualizado
3. Verifique se os Secrets estão configurados

Boa sorte com o deploy! 🚀
