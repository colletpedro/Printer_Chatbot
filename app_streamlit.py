#!/usr/bin/env python3
"""
Frontend Streamlit para o Chatbot Epson com ChromaDB
Interface web moderna para o sistema de busca semântica
"""

import streamlit as st
import google.generativeai as genai
import json
import time
import re
import os
import sys
from datetime import datetime

# Adiciona path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

# Configuração da página
st.set_page_config(
    page_title="Chatbot Epson - Suporte Técnico",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importações do sistema principal
from core.chatbot_chromadb import (
    init_chromadb,
    sync_printer_metadata_from_chromadb,
    enhanced_search_chromadb,
    get_printer_metadata_dynamic,
    call_api_detailed,
    format_response,
    can_make_request,
    check_and_reload_manual,
    PRINTER_METADATA,
    normalize_text,
    find_similar_printers
)

# Configuração da API Gemini
# Tenta pegar do secrets, se não existir usa a key padrão
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = "AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk"

genai.configure(api_key=GEMINI_API_KEY)

# Inicialização do estado da sessão
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'chromadb_initialized' not in st.session_state:
    st.session_state.chromadb_initialized = False
if 'chromadb_search' not in st.session_state:
    st.session_state.chromadb_search = None
if 'available_models' not in st.session_state:
    st.session_state.available_models = []
if 'selected_printer' not in st.session_state:
    st.session_state.selected_printer = None
if 'response_mode' not in st.session_state:
    st.session_state.response_mode = 'detalhado'
if 'last_update_check' not in st.session_state:
    st.session_state.last_update_check = datetime.now()
if 'question_count' not in st.session_state:
    st.session_state.question_count = 0

def init_system():
    """Inicializa o sistema ChromaDB"""
    if not st.session_state.chromadb_initialized:
        with st.spinner('🚀 Inicializando sistema ChromaDB...'):
            try:
                # Inicializa ChromaDB
                from core.chatbot_chromadb import chromadb_search, using_chromadb
                init_chromadb()
                st.session_state.chromadb_search = chromadb_search
                
                # Sincroniza metadados
                sync_printer_metadata_from_chromadb()
                
                # Obtém modelos disponíveis
                if chromadb_search:
                    st.session_state.available_models = chromadb_search.get_available_printer_models()
                else:
                    st.session_state.available_models = list(PRINTER_METADATA.keys())
                
                st.session_state.chromadb_initialized = True
                return True
                
            except Exception as e:
                st.error(f"❌ Erro ao inicializar ChromaDB: {e}")
                st.info("💡 Execute: `python scripts/sync_drive_chromadb.py` para configurar o ChromaDB")
                return False
    return True

def check_for_updates():
    """Verifica atualizações na base de conhecimento"""
    try:
        is_updated, status = check_and_reload_manual()
        if is_updated:
            st.info(f"🔄 {status}")
            # Re-sincroniza se houver atualizações
            sync_printer_metadata_from_chromadb()
            if st.session_state.chromadb_search:
                st.session_state.available_models = st.session_state.chromadb_search.get_available_printer_models()
        return is_updated, status
    except Exception as e:
        return False, f"Erro ao verificar atualizações: {e}"

def detect_printer_from_query(query):
    """Detecta modelo de impressora na query"""
    # Primeiro tenta detecção simples
    query_lower = normalize_text(query)
    
    for model_id, metadata in PRINTER_METADATA.items():
        # Verifica aliases
        for alias in metadata.get('aliases', []):
            if normalize_text(alias) in query_lower:
                return model_id
        
        # Verifica nome completo
        if normalize_text(metadata['full_name']) in query_lower:
            return model_id
    
    # Tenta detecção por similaridade
    similar = find_similar_printers(query, 0.7)
    if similar:
        return similar[0][0]  # Retorna o primeiro match
    
    return None

def process_user_query(query, printer_model, mode='detalhado'):
    """Processa a pergunta do usuário"""
    try:
        # Busca semântica no ChromaDB
        with st.spinner('🔍 Buscando informações relevantes...'):
            manual_sections = enhanced_search_chromadb(query, printer_model)
        
        if not manual_sections:
            return None, "Nenhuma informação relevante encontrada no manual."
        
        # Gera resposta com Gemini
        with st.spinner('🤖 Gerando resposta...'):
            success, response = call_api_detailed(query, manual_sections, mode, printer_model)
        
        if success:
            formatted = format_response(response)
            sources_count = len(manual_sections)
            return formatted, f"📚 Baseado em {sources_count} seção(ões) do manual"
        else:
            return None, response
            
    except Exception as e:
        return None, f"Erro ao processar pergunta: {e}"

# Interface principal
def main():
    # Inicializa o sistema
    if not init_system():
        st.stop()
    
    # Header principal
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🖨️ Chatbot Epson")
        st.markdown("**Sistema Inteligente de Suporte Técnico**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Status do sistema
        if st.session_state.chromadb_initialized:
            st.success("✅ ChromaDB Ativo")
            st.info(f"📚 {len(st.session_state.available_models)} modelos disponíveis")
        else:
            st.error("❌ ChromaDB não inicializado")
        
        st.markdown("---")
        
        # Seleção de impressora
        st.subheader("🖨️ Impressora")
        
        # Lista de modelos para seleção
        model_options = ["Detectar automaticamente"] + [
            PRINTER_METADATA.get(m, {}).get('full_name', m) 
            for m in st.session_state.available_models 
            if m in PRINTER_METADATA
        ]
        
        selected = st.selectbox(
            "Selecione o modelo:",
            options=model_options,
            help="Escolha sua impressora ou deixe o sistema detectar"
        )
        
        if selected != "Detectar automaticamente":
            # Encontra o ID do modelo baseado no nome completo
            for model_id, metadata in PRINTER_METADATA.items():
                if metadata.get('full_name') == selected:
                    st.session_state.selected_printer = model_id
                    break
        else:
            st.session_state.selected_printer = None
        
        st.markdown("---")
        
        # Modo de resposta
        st.subheader("💬 Modo de Resposta")
        
        mode = st.radio(
            "Escolha o tipo de resposta:",
            options=['detalhado', 'rapido'],
            format_func=lambda x: '📖 Detalhado' if x == 'detalhado' else '⚡ Rápido',
            help="Detalhado: explicações completas | Rápido: respostas diretas"
        )
        st.session_state.response_mode = mode
        
        st.markdown("---")
        
        # Botões de ação
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Atualizar", use_container_width=True):
                with st.spinner("Verificando..."):
                    updated, msg = check_for_updates()
                    if updated:
                        st.success("Base atualizada!")
                    else:
                        st.info(msg)
        
        with col2:
            if st.button("🗑️ Limpar Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.question_count = 0
                st.rerun()
        
        st.markdown("---")
        
        # Informações
        st.caption("**Versão:** 2.0 ChromaDB")
        st.caption(f"**Perguntas:** {st.session_state.question_count}")
        
        # Dicas
        with st.expander("💡 Dicas de Uso"):
            st.markdown("""
            **Como usar:**
            1. Digite sua pergunta sobre impressoras Epson
            2. O sistema detectará o modelo automaticamente
            3. Ou selecione manualmente na barra lateral
            
            **Exemplos de perguntas:**
            - Como trocar a tinta?
            - Impressora não liga
            - Configurar Wi-Fi
            - Papel emperrado
            
            **Modos:**
            - **Detalhado**: Passo a passo completo
            - **Rápido**: Resposta direta em 3-4 passos
            """)
    
    # Área principal do chat
    
    # Verifica atualizações a cada 10 perguntas
    if st.session_state.question_count > 0 and st.session_state.question_count % 10 == 0:
        check_for_updates()
    
    # Mensagem de boas-vindas
    if len(st.session_state.messages) == 0:
        with st.chat_message("assistant"):
            st.markdown("""👋 **Olá! Sou o assistente técnico Epson!**
            
Posso ajudar com:
- 🔧 Problemas técnicos e soluções
- 🖨️ Configuração de impressoras
- 🎨 Qualidade de impressão
- 📡 Conexão Wi-Fi e rede
- 🛠️ Manutenção e limpeza

**Digite sua pergunta abaixo!**""")
    
    # Exibe histórico de mensagens
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
        
        # Verifica rate limiting
        can_proceed, rate_msg = can_make_request()
        if not can_proceed:
            with st.chat_message("assistant"):
                st.warning(rate_msg)
            st.stop()
        
        # Detecta ou usa impressora selecionada
        printer_model = st.session_state.selected_printer
        
        if not printer_model:
            # Tenta detectar da query
            detected = detect_printer_from_query(prompt)
            if detected:
                printer_model = detected
                printer_name = PRINTER_METADATA.get(detected, {}).get('full_name', detected)
                with st.chat_message("assistant"):
                    st.info(f"🔍 Impressora detectada: **{printer_name}**")
            else:
                # Solicita ao usuário especificar o modelo
                with st.chat_message("assistant"):
                    st.warning("""⚠️ **Modelo de impressora não identificado**
                    
Por favor:
1. Selecione o modelo na barra lateral, ou
2. Inclua o modelo na sua pergunta (ex: "Como trocar tinta da L3150?")

Modelos disponíveis: L3110, L3150, L3250, L375, L4150, L4260, L5190, L6490, L1300, etc.""")
                st.stop()
        
        # Nome da impressora para exibição
        printer_name = PRINTER_METADATA.get(printer_model, {}).get('full_name', printer_model)
        
        # Processa a pergunta
        response, source = process_user_query(
            prompt, 
            printer_model,
            st.session_state.response_mode
        )
        
        # Exibe resposta
        with st.chat_message("assistant"):
            if response:
                # Adiciona indicador do modelo e modo
                mode_emoji = "⚡" if st.session_state.response_mode == 'rapido' else "📖"
                header = f"{mode_emoji} **[{printer_name}]**\n\n"
                st.markdown(header + response)
                
                # Exibe fonte
                if source:
                    st.caption(source)
                
                # Salva no histórico
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": header + response,
                    "source": source
                })
                
                # Incrementa contador
                st.session_state.question_count += 1
                
            else:
                # Erro ou sem resultados
                st.error(source or "Não foi possível gerar uma resposta.")
                
                # Dicas
                st.info("""💡 **Dicas:**
• Tente reformular sua pergunta
• Use termos mais específicos
• Verifique se o modelo da impressora está correto""")
    
    # Footer com métricas
    if st.session_state.question_count > 0:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Perguntas", st.session_state.question_count)
        with col2:
            st.metric("🖨️ Modelos", len(st.session_state.available_models))
        with col3:
            mode_text = "Rápido" if st.session_state.response_mode == 'rapido' else "Detalhado"
            st.metric("⚙️ Modo", mode_text)

if __name__ == "__main__":
    main()
