# 🚀 Guia de Deploy - Chatbot Epson

## Opções de Hospedagem (Do Mais Fácil ao Mais Complexo)

---

## 1️⃣ **Streamlit Cloud** (RECOMENDADO - Grátis)
**Ideal para: MVP, Testes, Feedback inicial**

### Vantagens:
- ✅ **100% Gratuito**
- ✅ Deploy automático via GitHub
- ✅ HTTPS incluído
- ✅ Atualizações automáticas
- ✅ Sem configuração de servidor

### Como fazer:
1. **Suba o código para GitHub**
```bash
git init
git add .
git commit -m "Initial deployment"
git remote add origin https://github.com/seu-usuario/chatbot-epson.git
git push -u origin main
```

2. **Acesse [share.streamlit.io](https://share.streamlit.io)**

3. **Clique em "New app"**

4. **Configure:**
   - Repository: `seu-usuario/chatbot-epson`
   - Branch: `main`
   - Main file path: `app_streamlit.py`

5. **Adicione secrets em Settings > Secrets:**
```toml
GEMINI_API_KEY = "AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk"
```

6. **Deploy!** URL será: `https://seu-app.streamlit.app`

---

## 2️⃣ **Render.com** (Grátis com limitações)
**Ideal para: Pequenas equipes, uso moderado**

### Como fazer:
1. **Crie `render.yaml`:**
```yaml
services:
  - type: web
    name: chatbot-epson
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "streamlit run app_streamlit.py --server.port=$PORT --server.address=0.0.0.0"
    envVars:
      - key: GEMINI_API_KEY
        value: AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk
```

2. **Deploy via GitHub no [render.com](https://render.com)**

---

## 3️⃣ **Ngrok** (Teste Rápido - Temporário)
**Ideal para: Demonstrações, testes rápidos**

### Como fazer:
```bash
# Instalar ngrok
brew install ngrok  # macOS

# Rodar localmente
./start.sh

# Em outro terminal
ngrok http 8501

# Compartilhe a URL: https://xxx.ngrok.io
```

---

## 4️⃣ **Railway.app** ($5/mês)
**Ideal para: Produção inicial**

### Como fazer:
1. **Crie `railway.toml`:**
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "streamlit run app_streamlit.py --server.port=$PORT --server.address=0.0.0.0"
```

2. **Deploy:**
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

---

## 5️⃣ **Heroku** ($7/mês)
**Ideal para: Produção estabelecida**

### Arquivos necessários:

**`Procfile`:**
```
web: sh setup.sh && streamlit run app_streamlit.py
```

**`setup.sh`:**
```bash
mkdir -p ~/.streamlit/
echo "[server]\nport = $PORT\nenableCORS = false\n" > ~/.streamlit/config.toml
```

### Deploy:
```bash
heroku create chatbot-epson
heroku config:set GEMINI_API_KEY=sua_chave
git push heroku main
```

---

## 6️⃣ **Docker + Cloud Run (Google)** 
**Ideal para: Escala empresarial**

**`Dockerfile`:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD streamlit run app_streamlit.py \
    --server.port=8080 \
    --server.address=0.0.0.0
```

### Deploy:
```bash
# Build e push
gcloud builds submit --tag gcr.io/PROJECT_ID/chatbot-epson

# Deploy
gcloud run deploy chatbot-epson \
    --image gcr.io/PROJECT_ID/chatbot-epson \
    --platform managed \
    --allow-unauthenticated
```

---

## 7️⃣ **VPS Próprio** (DigitalOcean/Linode)
**Ideal para: Controle total**

### Script de instalação:
```bash
#!/bin/bash
# No servidor Ubuntu/Debian

# Instalar Python
sudo apt update
sudo apt install python3-pip python3-venv nginx -y

# Clonar repositório
git clone https://github.com/seu-usuario/chatbot-epson.git
cd chatbot-epson

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar systemd
sudo nano /etc/systemd/system/chatbot.service
```

**`chatbot.service`:**
```ini
[Unit]
Description=Chatbot Epson
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/chatbot-epson
Environment="PATH=/home/ubuntu/chatbot-epson/venv/bin"
ExecStart=/home/ubuntu/chatbot-epson/venv/bin/streamlit run app_streamlit.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx config:
```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 📊 Comparação Rápida

| Plataforma | Custo | Dificuldade | Performance | Escalabilidade |
|------------|-------|-------------|-------------|----------------|
| **Streamlit Cloud** | Grátis | ⭐ Fácil | ⭐⭐⭐ Boa | ⭐⭐ Limitada |
| **Render** | Grátis* | ⭐⭐ Média | ⭐⭐⭐ Boa | ⭐⭐⭐ Boa |
| **Ngrok** | Grátis | ⭐ Fácil | ⭐⭐ Local | ⭐ Nenhuma |
| **Railway** | $5/mês | ⭐⭐ Média | ⭐⭐⭐⭐ Ótima | ⭐⭐⭐⭐ Ótima |
| **Heroku** | $7/mês | ⭐⭐⭐ Média | ⭐⭐⭐⭐ Ótima | ⭐⭐⭐⭐ Ótima |
| **Cloud Run** | Pay-as-you-go | ⭐⭐⭐⭐ Difícil | ⭐⭐⭐⭐⭐ Excelente | ⭐⭐⭐⭐⭐ Excelente |
| **VPS** | $5-20/mês | ⭐⭐⭐⭐⭐ Difícil | ⭐⭐⭐⭐ Ótima | ⭐⭐⭐ Manual |

---

## 🎯 Recomendação para Início

### Para feedback inicial e testes:
1. **Use Streamlit Cloud** - É grátis e rápido
2. **Configure Google Analytics** para métricas
3. **Adicione formulário de feedback** no app

### Passos imediatos:
```bash
# 1. Preparar para GitHub
echo "chromadb_storage/" >> .gitignore
echo "venv/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
echo ".env" >> .gitignore

# 2. Commit
git add .
git commit -m "Ready for deployment"

# 3. Push para GitHub
git push origin main

# 4. Deploy no Streamlit Cloud
# Acesse: https://share.streamlit.io
```

---

## 📈 Monitoramento e Feedback

### Adicione ao app:
```python
# No final do app_streamlit.py
with st.sidebar:
    st.markdown("---")
    st.subheader("📝 Feedback")
    feedback = st.text_area("Deixe sua sugestão:")
    if st.button("Enviar Feedback"):
        # Salvar em banco ou enviar email
        st.success("Obrigado pelo feedback!")
```

### Analytics:
```python
# Google Analytics
st.components.v1.html("""
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_ID');
</script>
""", height=0)
```

---

## 🔒 Segurança para Produção

1. **Remova API keys do código:**
```python
# Em vez de:
GEMINI_API_KEY = "chave_hardcoded"

# Use:
import os
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
```

2. **Limite de uso:**
```python
# Adicione rate limiting
from datetime import datetime, timedelta

if 'last_query' in st.session_state:
    if datetime.now() - st.session_state.last_query < timedelta(seconds=2):
        st.error("Aguarde 2 segundos entre perguntas")
        return
```

3. **Autenticação (opcional):**
```python
# Senha simples
password = st.text_input("Senha:", type="password")
if password != st.secrets["APP_PASSWORD"]:
    st.error("Senha incorreta")
    st.stop()
```

---

## 📱 URL para Compartilhar

Após deploy, compartilhe:

### Template de mensagem:
```
🚀 Teste nosso novo Chatbot Epson!

🔗 Link: https://seu-app.streamlit.app

✨ Features:
• Respostas instantâneas sobre impressoras
• Interface moderna e intuitiva
• Busca inteligente com IA

📝 Seu feedback é importante!
Teste e nos diga o que achou.
```

---

## 🆘 Suporte

Problemas comuns:

1. **"Module not found"**: Verifique requirements.txt
2. **"Port already in use"**: Mude a porta
3. **"API key invalid"**: Configure secrets corretamente
4. **ChromaDB não carrega**: Reduza tamanho ou use banco remoto

---

**Pronto para deploy!** Escolha a opção mais adequada e compartilhe o link para feedback! 🚀
