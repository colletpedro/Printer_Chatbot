# 🔧 Solução para Deploy no Streamlit Cloud

## ❌ Erro: "Error installing requirements"

### Soluções (tente na ordem):

## Solução 1: Use a versão simplificada (MAIS RÁPIDA) ✅

No Streamlit Cloud, mude as configurações:

1. **Main file path**: `app_streamlit_simple.py` (em vez de app_streamlit.py)
2. **Requirements**: O Streamlit usará automaticamente `requirements.txt`

Se ainda falhar, continue para Solução 2.

---

## Solução 2: Use requirements minimal

1. No seu app Streamlit Cloud, vá em **"Manage app"**
2. Clique em **"Advanced settings"**
3. Em **"Python dependencies"**, cole isto:

```txt
streamlit==1.29.0
google-generativeai==0.3.2
python-dotenv==1.0.0
pandas==2.1.4
numpy==1.24.3
```

4. **Save** e **Reboot app**

---

## Solução 3: Deploy versão ultra-minimal primeiro

1. Crie um novo app no Streamlit Cloud
2. Configure:
   - **Repository**: `colletpedro/Printer_Chatbot`
   - **Branch**: `main`
   - **Main file**: `app_streamlit_simple.py`
   
3. Em **Advanced settings** → **Python dependencies**:
```txt
streamlit
google-generativeai
```

4. Deploy e teste se funciona

5. Depois adicione gradualmente:
```txt
pandas
numpy
python-dotenv
```

---

## Solução 4: Configurar secrets

Em **Settings** → **Secrets**, adicione:

```toml
GEMINI_API_KEY = "AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk"
```

---

## 📝 Opções de Deploy Disponíveis

Agora você tem 3 versões para escolher:

| Arquivo | Descrição | Dependências |
|---------|-----------|--------------|
| `app_streamlit_simple.py` | Versão sem ChromaDB | Mínimas (funciona com certeza) |
| `app_streamlit.py` | Versão completa | Todas (pode dar erro) |

| Requirements | Uso |
|--------------|-----|
| `requirements_streamlit_cloud.txt` | Ultra-minimal (5 pacotes) |
| `requirements_minimal.txt` | Minimal (7 pacotes) |
| `requirements.txt` | Completo (20+ pacotes) |

---

## 🚀 Recomendação

1. **Comece com `app_streamlit_simple.py`** - Garante que funcione
2. **Use requirements minimal** - Menos chance de erro
3. **Depois migre** para versão completa quando estiver funcionando

---

## 💡 Dica: Deploy Alternativo

Se Streamlit Cloud continuar com problemas, use **Hugging Face Spaces**:

1. Vá para [huggingface.co/spaces](https://huggingface.co/spaces)
2. Create new Space
3. Choose Streamlit
4. Clone do GitHub
5. Deploy!

Hugging Face é mais tolerante com dependências pesadas.

---

## ✅ Teste Local Primeiro

```bash
# Criar ambiente limpo
python -m venv test_env
source test_env/bin/activate

# Testar requirements minimal
pip install -r requirements_minimal.txt

# Rodar app simples
streamlit run app_streamlit_simple.py
```

Se funcionar local, funcionará no cloud!
