# ChatBot CLI - Assistente de Impressoras

Chatbot especializado em impressoras Epson L3250/L3251 usando Google Gemini API.

## Como usar

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar o chatbot
python chatbot.py
```

## Funcionalidades

- **Especializado**: Foco em impressoras Epson L3250/L3251
- **Base de conhecimento**: Manual completo de 114 seções
- **Busca inteligente**: Variações de palavras e sinônimos
- **Rate limiting**: Controle automático de requisições à API
- **Dois modos**: Rápido (conciso) ou Detalhado (completo)

## Tópicos suportados

- Problemas de impressão e qualidade
- Configuração WiFi e conectividade
- Troca de cartuchos e manutenção
- Digitalização e cópias
- Instalação de drivers
- Limpeza e solução de problemas

## Primeira execução

```bash
# Criar ambiente virtual
python3 -m venv venv

# Ativar e instalar dependências
source venv/bin/activate
pip install requests PyPDF2

# Executar
python chatbot.py
```

## Comandos

| Comando | Função |
|---------|--------|
| `source venv/bin/activate` | Ativar ambiente virtual |
| `python chatbot.py` | Iniciar o chatbot |
| `sair` / `exit` / `quit` | Encerrar |
| `Ctrl+C` | Forçar encerramento |

## Requisitos

- Python 3.6+
- Conexão com internet
- API Key do Google Gemini (já configurada)

---

**ChatBot CLI para Impressoras Epson L3250/L3251** 