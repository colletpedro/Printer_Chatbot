#!/usr/bin/env python3
"""
Versão simplificada para Streamlit Cloud - Chatbot Epson
Sem dependências pesadas como ChromaDB
"""

import streamlit as st
import google.generativeai as genai
import time
import re
import os

# Configuração da página
st.set_page_config(
    page_title="Chatbot Epson - Suporte Técnico",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração da API Gemini
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = "AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Rate limiting
last_request_time = 0
MIN_REQUEST_INTERVAL = 2

# Metadados das impressoras
PRINTER_METADATA = {
    'L3110': 'Epson L3110 - Multifuncional EcoTank',
    'L3150': 'Epson L3150 - Multifuncional EcoTank com Wi-Fi',
    'L3250': 'Epson L3250/L3251 - Multifuncional EcoTank com Wi-Fi',
    'L375': 'Epson L375 - Multifuncional EcoTank',
    'L4150': 'Epson L4150 - Multifuncional EcoTank com ADF',
    'L4260': 'Epson L4260 - Multifuncional EcoTank com ADF',
    'L5190': 'Epson L5190 - Multifuncional com Fax',
    'L5290': 'Epson L5290 - Multifuncional com Fax e Ethernet',
    'L6490': 'Epson L6490 - Multifuncional A3',
    'L805': 'Epson L805 - Fotográfica',
    'L1300': 'Epson L1300 - A3+',
    'L396': 'Epson L396 - Multifuncional compacta'
}

# Inicializa session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'selected_printer' not in st.session_state:
    st.session_state.selected_printer = None
if 'response_mode' not in st.session_state:
    st.session_state.response_mode = 'detalhado'

def check_printer_context(query):
    """Verifica se a pergunta é sobre impressoras"""
    try:
        prompt = f"""Analise se a pergunta é sobre impressoras. Responda APENAS "SIM" ou "NÃO".

Pergunta: "{query}"

É sobre impressoras, problemas de impressão, tinta, papel, configuração de impressoras, scanner ou cópia?"""
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=10
            )
        )
        
        if response and response.text:
            return "SIM" in response.text.upper()
        return True
        
    except Exception as e:
        print(f"Erro ao verificar contexto: {e}")
        return True

def detect_printer_from_query(query):
    """Detecta modelo de impressora na query"""
    query_upper = query.upper()
    
    for model_key in PRINTER_METADATA.keys():
        if model_key in query_upper:
            return model_key
    
    # Busca por números de modelo
    import re
    numbers = re.findall(r'\b[L]?\d{3,4}\b', query_upper)
    for num in numbers:
        for model_key in PRINTER_METADATA.keys():
            if num in model_key:
                return model_key
    
    return None

def process_query_simple(query, printer_model, mode='detalhado'):
    """Processa pergunta usando apenas Gemini (sem ChromaDB)"""
    global last_request_time
    
    try:
        # Rate limiting
        current_time = time.time()
        if current_time - last_request_time < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - (current_time - last_request_time))
        
        printer_name = PRINTER_METADATA.get(printer_model, printer_model)
        
        if mode == 'rapido':
            prompt = f"""Você é um especialista em impressoras Epson {printer_name}.
Responda a pergunta de forma BREVE e DIRETA em 3-4 passos.

Pergunta: {query}

Resposta concisa:"""
            max_tokens = 300
        else:
            prompt = f"""Você é um especialista em impressoras Epson {printer_name}.
Forneça uma resposta DETALHADA e COMPLETA com passos numerados.

Pergunta: {query}

Resposta detalhada:"""
            max_tokens = 800
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=max_tokens
            )
        )
        
        last_request_time = time.time()
        
        if response and response.text:
            return response.text, "📚 Conhecimento base Gemini"
        else:
            return None, "Erro ao gerar resposta"
            
    except Exception as e:
        return None, f"Erro: {e}"

def main():
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🖨️ Chatbot Epson")
        st.markdown("**Sistema de Suporte Técnico**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Seleção de impressora
        st.subheader("🖨️ Impressora")
        
        printer_options = ['Detecção Automática'] + list(PRINTER_METADATA.keys())
        selected = st.selectbox(
            "Selecione o modelo:",
            options=printer_options,
            index=0
        )
        
        if selected != 'Detecção Automática':
            st.session_state.selected_printer = selected
        else:
            st.session_state.selected_printer = None
        
        # Modo de resposta
        st.subheader("💬 Modo de Resposta")
        st.session_state.response_mode = st.radio(
            "Como deseja as respostas?",
            ['detalhado', 'rapido'],
            format_func=lambda x: '📖 Detalhado' if x == 'detalhado' else '⚡ Rápido'
        )
        
        # Limpar chat
        if st.button("🗑️ Limpar Conversa", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        # Info
        st.markdown("---")
        st.caption("**Versão:** 2.0 Cloud")
        st.caption("**Modelos suportados:**")
        for model in list(PRINTER_METADATA.keys())[:5]:
            st.caption(f"• {model}")
        st.caption("...e mais")
    
    # Mensagem de boas-vindas
    if len(st.session_state.messages) == 0:
        with st.chat_message("assistant"):
            st.markdown("""👋 **Olá! Sou o assistente técnico Epson!**
            
Posso ajudar com:
- 🔧 Problemas técnicos
- 🖨️ Configuração de impressoras
- 🎨 Qualidade de impressão
- 📡 Conexão Wi-Fi
- 🛠️ Manutenção e limpeza

**Digite sua pergunta abaixo!**""")
    
    # Exibe histórico
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("source"):
                st.caption(message["source"])
    
    # Input do usuário
    if prompt := st.chat_input("Digite sua pergunta sobre impressoras Epson..."):
        # Adiciona mensagem do usuário
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Verifica contexto
        if not check_printer_context(prompt):
            with st.chat_message("assistant"):
                out_of_context = """🤔 **Desculpe, não posso ajudar com esse assunto.**

Sou especializado em **impressoras Epson**. Posso ajudar com:
- Problemas técnicos
- Configuração
- Manutenção
- Qualidade de impressão
- Conexão e rede

**Por favor, faça uma pergunta sobre impressoras!**"""
                st.markdown(out_of_context)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": out_of_context
                })
            st.stop()
        
        # Detecta ou usa impressora selecionada
        printer_model = st.session_state.selected_printer
        
        if not printer_model:
            detected = detect_printer_from_query(prompt)
            if detected:
                printer_model = detected
                with st.chat_message("assistant"):
                    st.info(f"🔍 Detectado: **{PRINTER_METADATA.get(detected, detected)}**")
            else:
                # Usa modelo genérico
                printer_model = "EcoTank"
                with st.chat_message("assistant"):
                    st.info("💡 Usando conhecimento geral sobre impressoras Epson")
        
        # Processa pergunta
        with st.spinner('🤖 Processando...'):
            response, source = process_query_simple(
                prompt,
                printer_model,
                st.session_state.response_mode
            )
        
        # Exibe resposta
        with st.chat_message("assistant"):
            if response:
                mode_emoji = "⚡" if st.session_state.response_mode == 'rapido' else "📖"
                printer_name = PRINTER_METADATA.get(printer_model, printer_model)
                header = f"{mode_emoji} **[{printer_name}]**\n\n"
                st.markdown(header + response)
                st.caption(source)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": header + response,
                    "source": source
                })
            else:
                error_msg = "❌ Desculpe, não consegui processar sua pergunta. Tente novamente."
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "source": source
                })

if __name__ == "__main__":
    main()
