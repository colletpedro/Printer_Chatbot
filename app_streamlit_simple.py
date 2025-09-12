#!/usr/bin/env python3
"""
Interface Streamlit Simplificada - Sem ChromaDB
Para deploy inicial no Streamlit Cloud
"""

import streamlit as st
import time
import json
import os
from datetime import datetime
import google.generativeai as genai

# Configuração da página
st.set_page_config(
    page_title="Chatbot Epson - Suporte Técnico",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS do tema escuro
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --bg-primary: #0a0a0a;
        --bg-secondary: #141414;
        --bg-card: #1a1a1a;
        --border: #262626;
        --text-primary: #e5e5e5;
        --text-secondary: #a3a3a3;
        --accent: #3b82f6;
    }
    
    .stApp {
        background: var(--bg-primary);
        color: var(--text-primary);
    }
</style>
""", unsafe_allow_html=True)

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
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'selected_printer' not in st.session_state:
    st.session_state.selected_printer = None

def generate_response(query, printer_model=None):
    """Gera resposta usando Gemini"""
    try:
        prompt = f"""Você é um especialista em impressoras Epson.
        
        Modelo da impressora: {printer_model if printer_model else 'Não especificado'}
        
        Pergunta do usuário: {query}
        
        Forneça uma resposta útil e clara."""
        
        response = model.generate_content(prompt)
        
        if response and response.text:
            return True, response.text
        else:
            return False, "Não foi possível gerar resposta"
            
    except Exception as e:
        return False, f"Erro: {e}"

# Interface principal
def main():
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🖨️ Chatbot Epson - Suporte Técnico")
        st.markdown("**Sistema inteligente de suporte (Versão Simplificada)**")
    
    # Aviso sobre versão simplificada
    st.info("⚠️ Versão simplificada sem busca em base de conhecimento. Respostas baseadas apenas em IA.")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Seleção de impressora
        st.subheader("🖨️ Modelo da Impressora")
        selected_printer = st.selectbox(
            "Selecione o modelo:",
            ["Detectar automaticamente"] + PRINTER_MODELS,
            index=0
        )
        
        if selected_printer != "Detectar automaticamente":
            st.session_state.selected_printer = selected_printer
            st.success(f"✅ {selected_printer}")
        
        # Limpar histórico
        if st.button("🗑️ Limpar Histórico", use_container_width=True):
            st.session_state.conversation_history = []
            st.rerun()
        
        # Sobre
        st.subheader("ℹ️ Sobre")
        st.markdown("""
        **Versão:** Simplificada  
        **IA:** Google Gemini  
        **Status:** Online  
        """)
    
    # Chat
    chat_container = st.container()
    
    with chat_container:
        # Histórico
        if st.session_state.conversation_history:
            st.subheader("💬 Histórico da Conversa")
            for item in st.session_state.conversation_history:
                with st.chat_message("user"):
                    st.write(item['question'])
                
                with st.chat_message("assistant"):
                    st.markdown(item['response'])
        
        # Input
        st.markdown("---")
        st.subheader("🤔 Faça sua pergunta")
        
        with st.form("question_form", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                user_question = st.text_input(
                    "Digite sua pergunta sobre impressoras Epson:",
                    placeholder="Ex: Como trocar a tinta da minha impressora?"
                )
            
            with col2:
                submit_button = st.form_submit_button(
                    "🚀 Enviar",
                    use_container_width=True
                )
        
        # Processar pergunta
        if submit_button and user_question:
            with st.spinner("🤖 Gerando resposta..."):
                # Detectar modelo se mencionado
                printer_model = st.session_state.selected_printer
                for model_name in PRINTER_MODELS:
                    if model_name.lower() in user_question.lower():
                        printer_model = model_name
                        break
                
                # Gerar resposta
                success, response = generate_response(user_question, printer_model)
                
                # Adicionar ao histórico
                history_item = {
                    'timestamp': datetime.now().strftime("%H:%M"),
                    'question': user_question,
                    'response': response,
                    'printer': printer_model or "Geral"
                }
                
                st.session_state.conversation_history.append(history_item)
                st.rerun()

if __name__ == "__main__":
    main()
