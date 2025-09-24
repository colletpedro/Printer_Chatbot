# 🚀 INSTRUÇÕES DE DEPLOY IMEDIATO

## ✅ PASSOS PARA DEPLOY (5 minutos)

### 1️⃣ Delete o App Antigo (se ainda existir)
- Vá para https://share.streamlit.io/
- Se tiver um app travado, delete ele completamente

### 2️⃣ Crie um Novo App
Clique em **"New app"** e preencha EXATAMENTE assim:

```
Repository: colletpedro/Printer_Chatbot
Branch: main
Main file path: app_streamlit_cloud.py
```

⚠️ **IMPORTANTE**: Use `app_streamlit_cloud.py` (NÃO use app_streamlit.py)

### 3️⃣ Configure os Secrets
1. Clique em **"Advanced settings"**
2. Na área **"Secrets"**, cole EXATAMENTE isto:

```toml
GEMINI_API_KEY = "AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk"
```

### 4️⃣ Clique em Deploy!
- O deploy levará 2-3 minutos
- Você verá os logs de instalação
- Quando terminar, terá seu link!

## 📋 CHECKLIST

Antes de clicar em Deploy, confirme:
- [ ] Repository: `colletpedro/Printer_Chatbot`
- [ ] Branch: `main`
- [ ] Main file: `app_streamlit_cloud.py` ⚠️
- [ ] Secrets: GEMINI_API_KEY configurada

## 🎯 O QUE ESPERAR

### ✅ Sucesso:
- Deploy em 2-3 minutos
- App abre normalmente
- Chatbot funcionando

### ❌ Se der erro:
1. Verifique se usou `app_streamlit_cloud.py`
2. Confirme que adicionou a API key nos Secrets
3. Tente deletar e criar novo app

## 💡 DIFERENÇA DOS ARQUIVOS

- **app_streamlit.py** = Versão completa (COM ChromaDB) - NÃO USE NO CLOUD
- **app_streamlit_cloud.py** = Versão otimizada (SEM ChromaDB) - USE ESTA!

## 🔗 URL FINAL

Após o deploy, seu app estará em:
```
https://[algum-nome].streamlit.app/
```

Você pode personalizar o nome depois em Settings.

---

**RESUMO**: Use `app_streamlit_cloud.py` e adicione a API key nos Secrets!
