#!/usr/bin/env python3
"""
Interface Streamlit Ultra-Minimal
Para garantir deploy no Streamlit Cloud
"""

import streamlit as st
import google.generativeai as genai
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Chatbot Epson - Suporte Técnico",
    page_icon="🖨️",
    layout="wide"
)

# Configuração da API Gemini
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Lista de modelos suportados
PRINTER_MODELS = [
    "Epson L3110", "Epson L3150", "Epson L3250", "Epson L3251",
    "Epson L375", "Epson L396", "Epson L4150", "Epson L4260",
    "Epson L5190", "Epson L5290", "Epson L6490", "Epson L1300", "Epson L805"
]

# Inicialização do estado
if 'messages' not in st.session_state:
    st.session_state.messages = []

def generate_response(query, printer_model=None):
    """Gera resposta usando Gemini"""
    try:
        prompt = f"""Você é um especialista em impressoras Epson.
        
        Modelo da impressora: {printer_model if printer_model else 'Não especificado'}
        
        Pergunta do usuário: {query}
        
        Forneça uma resposta útil e clara em português."""
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text
        else:
            return "Não foi possível gerar resposta. Tente novamente."
            
    except Exception as e:
        return f"Erro ao gerar resposta: {str(e)}"

# Interface principal
st.title("🖨️ Chatbot Epson - Suporte Técnico")
st.markdown("Sistema inteligente de suporte para impressoras Epson")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Seleção de impressora
    selected_printer = st.selectbox(
        "Modelo da Impressora:",
        ["Não especificado"] + PRINTER_MODELS
    )
    
    # Limpar chat
    if st.button("🗑️ Limpar Conversa"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Versão:** Minimal")
    st.markdown("**Status:** ✅ Online")

# Mostrar mensagens anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input do usuário
if prompt := st.chat_input("Digite sua pergunta sobre impressoras Epson..."):
    # Adicionar mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Gerar e mostrar resposta
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            response = generate_response(prompt, selected_printer if selected_printer != "Não especificado" else None)
            st.markdown(response)
    
    # Adicionar resposta ao histórico
    st.session_state.messages.append({"role": "assistant", "content": response})
