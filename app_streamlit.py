#!/usr/bin/env python3
"""
Chatbot Epson - Interface Streamlit
Versão limpa e funcional para deploy
"""

import streamlit as st
import google.generativeai as genai

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
if 'response_mode' not in st.session_state:
    st.session_state.response_mode = "detalhado"

def generate_response(query, printer_model=None, mode="detalhado"):
    """Gera resposta usando Gemini"""
    try:
        # Ajusta o prompt baseado no modo
        if mode == "rápido":
            mode_instruction = """
            Forneça uma resposta BREVE e DIRETA, em no máximo 3-4 frases.
            Vá direto ao ponto principal sem muitos detalhes.
            """
        else:  # detalhado
            mode_instruction = """
            Forneça uma resposta COMPLETA e DETALHADA.
            Inclua:
            - Explicação passo a passo quando aplicável
            - Possíveis causas do problema
            - Soluções alternativas se existirem
            - Dicas de prevenção quando relevante
            """
        
        prompt = f"""Você é um especialista em impressoras Epson.
        
        Modelo da impressora: {printer_model if printer_model else 'Não especificado'}
        
        {mode_instruction}
        
        Pergunta do usuário: {query}
        
        Responda em português de forma clara."""
        
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
        "🖨️ Modelo da Impressora:",
        ["Não especificado"] + PRINTER_MODELS
    )
    
    st.markdown("---")
    
    # Modo de resposta
    st.subheader("💬 Modo de Resposta")
    response_mode = st.radio(
        "Escolha o tipo de resposta:",
        ["rápido", "detalhado"],
        index=1,  # detalhado por padrão
        help="Rápido: respostas diretas e concisas\nDetalhado: explicações completas com passo a passo"
    )
    st.session_state.response_mode = response_mode
    
    if response_mode == "rápido":
        st.info("⚡ Respostas rápidas e diretas")
    else:
        st.info("📖 Respostas detalhadas com explicações")
    
    st.markdown("---")
    
    # Limpar chat
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Versão:** 1.0")
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
            response = generate_response(
                prompt, 
                selected_printer if selected_printer != "Não especificado" else None,
                mode=st.session_state.response_mode
            )
            st.markdown(response)
    
    # Adicionar resposta ao histórico
    st.session_state.messages.append({"role": "assistant", "content": response})
