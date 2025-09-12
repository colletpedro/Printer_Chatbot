#!/usr/bin/env python3
"""
Interface Streamlit para o Chatbot Epson com ChromaDB
Sistema web moderno e responsivo para disponibilização do chatbot

Características:
- Interface limpa e moderna
- Histórico de conversas
- Seleção de modo (rápido/detalhado)
- Indicadores visuais de status
- Suporte a múltiplas impressoras
- Rate limiting visual
"""

import streamlit as st
import time
import json
import os
import sys
from datetime import datetime
import google.generativeai as genai

# Adiciona path para importar módulos do core
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

# Importa módulos do sistema
from chromadb_integration_example import ChromaDBSearch
from core.chatbot_chromadb import (
    sync_printer_metadata_from_chromadb,
    find_similar_printers,
    get_printer_metadata_dynamic,
    expand_ink_query,
    format_response,
    PRINTER_METADATA,
    MIN_REQUEST_INTERVAL,
    MAX_REQUESTS_PER_MINUTE
)

# Configuração da página
st.set_page_config(
    page_title="Chatbot Epson - Suporte Técnico",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado com tema elegante profissional
st.markdown("""
<style>
    /* Importar fonte elegante */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Variáveis de cor - Escuro Elegante e Minimalista */
    :root {
        --bg-primary: #0a0a0a;      /* Preto profundo */
        --bg-secondary: #141414;    /* Cinza escuro */
        --bg-card: #1a1a1a;         /* Cards cinza carvão */
        --border: #262626;          /* Borda cinza escuro */
        --text-primary: #e5e5e5;    /* Texto claro */
        --text-secondary: #a3a3a3;  /* Texto cinza médio */
        --text-dim: #737373;        /* Texto cinza escuro */
        --accent: #3b82f6;          /* Azul elegante */
        --accent-hover: #60a5fa;    /* Azul mais claro no hover */
        --sidebar-bg: #0f0f0f;      /* Sidebar quase preto */
        --success: #22c55e;         /* Verde suave */
        --warning: #eab308;         /* Amarelo suave */
        --error: #ef4444;           /* Vermelho suave */
    }
    
    /* Background minimalista */
    .stApp {
        background: var(--bg-primary);
        color: var(--text-primary);
    }
    
    /* Sidebar minimalista */
    section[data-testid="stSidebar"] {
        background: var(--sidebar-bg);
        border-right: 1px solid var(--border);
    }
    
    section[data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }
    
    /* Headers limpos e simples */
    h1, h2, h3 {
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        letter-spacing: -0.01em;
    }
    
    h1 {
        color: var(--text-primary) !important;
        border-bottom: 1px solid var(--border);
        padding-bottom: 16px;
        font-size: 2rem;
        font-weight: 600;
    }
    
    /* Cards minimalistas */
    .stAlert, div[data-testid="stVerticalBlock"] > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px;
        box-shadow: none;
    }
    
    /* Botões elegantes escuros */
    .stButton > button {
        background: var(--accent);
        color: white !important;
        border: 1px solid transparent;
        border-radius: 6px;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease;
        box-shadow: none;
        text-transform: none;
        letter-spacing: normal;
        font-size: 0.9rem;
    }
    
    .stButton > button:hover {
        background: var(--accent-hover);
        border-color: var(--accent);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
    }
    
    /* Inputs minimalistas */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        background-color: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 4px;
        font-family: 'Inter', sans-serif;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* Métricas limpas */
    [data-testid="metric-container"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent);
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0;
        box-shadow: none;
    }
    
    [data-testid="metric-container"] [data-testid="metric-label"] {
        color: var(--text-secondary) !important;
        font-size: 0.875rem;
        font-weight: 400;
        text-transform: none;
        letter-spacing: normal;
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: var(--text-primary) !important;
        font-weight: 600;
        font-size: 1.25rem;
    }
    
    /* Chat messages elegantes escuras */
    .stChatMessage {
        background: var(--bg-card) !important;
        border-radius: 8px;
        margin: 12px 0;
        padding: 16px;
        border: 1px solid var(--border);
        box-shadow: none;
    }
    
    /* User messages */
    [data-testid="stChatMessageContent-user"] {
        background: #1e293b;
        border-left: 3px solid var(--accent);
    }
    
    /* Assistant messages */
    [data-testid="stChatMessageContent-assistant"] {
        background: var(--bg-card);
        border-left: 3px solid #404040;
    }
    
    /* Tabs elegantes */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--bg-secondary);
        border-radius: 6px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary) !important;
        background-color: transparent;
        border-radius: 4px;
        transition: all 0.2s;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary);
        color: var(--accent) !important;
    }
    
    /* Radio buttons e checkboxes */
    .stRadio > label,
    .stCheckbox > label {
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Download button minimalista */
    .stDownloadButton > button {
        background: var(--success) !important;
        color: white !important;
        font-weight: 500;
        border: none !important;
    }
    
    .stDownloadButton > button:hover {
        background: #059669 !important;
        transform: none;
    }
    
    /* Scrollbar minimalista */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-dim);
    }
    
    /* Info e warning boxes */
    .stAlert > div {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border-radius: 4px;
        border-left: 3px solid var(--accent);
    }
    
    /* Captions e small text */
    .stCaption, small {
        color: var(--text-dim) !important;
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
    }
    
    /* Dividers elegantes */
    hr {
        border: none;
        height: 1px;
        background: var(--border);
        margin: 2rem 0;
        opacity: 0.5;
    }
    
    /* Expander premium */
    .streamlit-expanderHeader {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px;
        color: var(--text-primary) !important;
    }
    
    /* Código e pre */
    code, pre {
        background-color: var(--bg-primary) !important;
        color: var(--accent) !important;
        border: 1px solid var(--border);
        border-radius: 4px;
        font-family: 'Courier New', monospace;
    }
    
    /* Links com estilo */
    a {
        color: var(--accent) !important;
        text-decoration: none;
        transition: all 0.2s;
        font-weight: 500;
    }
    
    a:hover {
        color: var(--accent-soft) !important;
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização do estado da sessão
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.chromadb_search = None
    st.session_state.available_models = []
    st.session_state.conversation_history = []
    st.session_state.selected_printer = None
    st.session_state.response_mode = 'rapido'
    st.session_state.last_request_time = 0
    st.session_state.request_times = []
    st.session_state.rate_limit_warning = False

# Configuração da API Gemini
GEMINI_API_KEY = "AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@st.cache_resource
def initialize_system():
    """Inicializa o sistema ChromaDB e carrega recursos"""
    try:
        # Inicializa ChromaDB
        chromadb_search = ChromaDBSearch()
        
        # Sincroniza metadados
        sync_printer_metadata_from_chromadb()
        
        # Obtém modelos disponíveis
        available_models = chromadb_search.get_available_printer_models()
        
        return chromadb_search, available_models, True
    except Exception as e:
        st.error(f"❌ Erro ao inicializar sistema: {e}")
        return None, [], False

def check_rate_limit():
    """Verifica rate limiting - DESATIVADO para melhor experiência"""
    # Rate limiting removido conforme solicitado
    # Retorna sempre True para permitir perguntas sem espera
    return True, "OK"

def detect_printer(query, available_models):
    """Detecta o modelo da impressora a partir da query"""
    # Primeiro tenta detecção simples
    for model in available_models:
        model_clean = model.replace('impressora', '').lower()
        if model_clean in query.lower():
            return model
    
    # Tenta busca por similaridade
    similar = find_similar_printers(query, 0.6)
    if similar:
        return similar[0][0]
    
    return None

def semantic_search(query, printer_model=None):
    """Realiza busca semântica no ChromaDB"""
    if not st.session_state.chromadb_search:
        return []
    
    try:
        # Expande query se for sobre tinta
        expanded_query = expand_ink_query(query)
        
        results = st.session_state.chromadb_search.semantic_search(
            query=expanded_query,
            printer_model=printer_model,
            n_results=15,
            min_similarity=0.2
        )
        
        return results
    except Exception as e:
        st.error(f"Erro na busca: {e}")
        return []

def generate_response(query, manual_sections, mode='rapido', printer_model=None):
    """Gera resposta usando Gemini"""
    try:
        # Prepara contexto
        context_parts = []
        for section, score in manual_sections[:5]:
            context_parts.append(
                f"SEÇÃO (Score: {score}):\n"
                f"TÍTULO: {section['title']}\n"
                f"CONTEÚDO: {section['content'][:1000]}..."
            )
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Define prompt baseado no modo
        if mode == 'rapido':
            system_prompt = f"""Você é um especialista técnico em impressoras EPSON.
            
INSTRUÇÕES PARA MODO RÁPIDO:
- Responda de forma BREVE e PRÁTICA em 3-4 passos
- Use linguagem simples e direta
- Foque no modelo {printer_model if printer_model else 'não especificado'}

CONTEXTO DO MANUAL:
{context}"""
        else:
            system_prompt = f"""Você é um assistente técnico especializado em impressoras Epson.

Forneça uma resposta COMPLETA e DETALHADA baseada no manual.

Modelo: {printer_model if printer_model else 'não especificado'}

CONTEXTO DO MANUAL:
{context}"""
        
        # Gera resposta
        combined_prompt = f"{system_prompt}\n\nPERGUNTA: {query}"
        
        response = model.generate_content(
            combined_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1500 if mode == 'rapido' else 2500,
                temperature=0.1,
            )
        )
        
        if response and response.text:
            # Atualiza controle de rate limiting
            current_time = time.time()
            st.session_state.last_request_time = current_time
            st.session_state.request_times.append(current_time)
            
            return True, format_response(response.text)
        else:
            return False, "Não foi possível gerar resposta"
            
    except Exception as e:
        return False, f"Erro na API: {e}"

# Interface principal
def main():
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🖨️ Chatbot Epson - Suporte Técnico")
        st.markdown("**Sistema inteligente de suporte para impressoras Epson EcoTank**")
    
    # Inicialização do sistema
    if not st.session_state.initialized:
        with st.spinner("🔧 Inicializando sistema ChromaDB..."):
            chromadb_search, available_models, success = initialize_system()
            if success:
                st.session_state.chromadb_search = chromadb_search
                st.session_state.available_models = available_models
                st.session_state.initialized = True
                st.success(f"✅ Sistema inicializado! {len(available_models)} modelos disponíveis.")
            else:
                st.error("❌ Falha ao inicializar o sistema. Verifique o ChromaDB.")
                st.stop()
    
    # Sidebar com configurações
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Seleção do modo de resposta
        st.subheader("📝 Modo de Resposta")
        mode_option = st.radio(
            "Escolha o tipo de resposta:",
            options=['rapido', 'detalhado'],
            format_func=lambda x: '🚀 Rápido (3-4 passos)' if x == 'rapido' else '📖 Detalhado (explicações completas)',
            index=0 if st.session_state.response_mode == 'rapido' else 1
        )
        st.session_state.response_mode = mode_option
        
        # Seleção manual de impressora
        st.subheader("🖨️ Modelo da Impressora")
        
        printer_options = ['Detectar automaticamente'] + st.session_state.available_models
        selected_printer = st.selectbox(
            "Selecione o modelo:",
            options=printer_options,
            index=0
        )
        
        if selected_printer != 'Detectar automaticamente':
            st.session_state.selected_printer = selected_printer
            metadata = get_printer_metadata_dynamic(selected_printer, None)
            st.info(f"**{metadata['full_name']}**\n\n{metadata['description']}")
        else:
            st.session_state.selected_printer = None
        
        # Estatísticas
        st.subheader("📊 Estatísticas")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Perguntas", len(st.session_state.conversation_history))
        with col2:
            st.metric("Modelos", len(st.session_state.available_models))
        
        # Limpar histórico
        if st.button("🗑️ Limpar Histórico", use_container_width=True):
            st.session_state.conversation_history = []
            st.rerun()
        
        # Informações do sistema
        st.subheader("ℹ️ Sobre")
        st.markdown("""
        **Versão:** 1.0.0  
        **Tecnologia:** ChromaDB + Gemini  
        **Busca:** Semântica com ML  
        **Interface:** Streamlit  
        
        ---
        
        **Características:**
        - Respostas instantâneas
        - Busca inteligente
        - Interface premium
        """)
        
        # Sistema de Feedback
        st.markdown("---")
        st.subheader("📝 Feedback")
        
        with st.form("feedback_form"):
            rating = st.select_slider(
                "Como você avalia o chatbot?",
                options=["😞", "😐", "🙂", "😊", "🤩"],
                value="🙂"
            )
            
            feedback_text = st.text_area(
                "Deixe sua sugestão ou comentário:",
                placeholder="O que podemos melhorar?",
                max_chars=500
            )
            
            submit_feedback = st.form_submit_button("Enviar Feedback", use_container_width=True)
            
            if submit_feedback and feedback_text:
                # Salvar feedback em arquivo JSON
                import json
                from datetime import datetime
                
                feedback_data = {
                    "timestamp": datetime.now().isoformat(),
                    "rating": rating,
                    "feedback": feedback_text
                }
                
                try:
                    # Criar pasta data se não existir
                    os.makedirs("data", exist_ok=True)
                    
                    # Ler feedbacks existentes ou criar novo arquivo
                    feedback_file = "data/feedbacks.json"
                    if os.path.exists(feedback_file):
                        with open(feedback_file, "r") as f:
                            feedbacks = json.load(f)
                    else:
                        feedbacks = []
                    
                    # Adicionar novo feedback
                    feedbacks.append(feedback_data)
                    
                    # Salvar
                    with open(feedback_file, "w") as f:
                        json.dump(feedbacks, f, indent=2, ensure_ascii=False)
                    
                    st.success("✅ Obrigado pelo seu feedback!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar feedback: {e}")
    
    # Área principal de chat
    chat_container = st.container()
    
    # Exibir histórico de conversas
    with chat_container:
        if st.session_state.conversation_history:
            st.subheader("💬 Histórico da Conversa")
            for item in st.session_state.conversation_history:
                # Pergunta do usuário
                with st.chat_message("user"):
                    st.markdown(f"**{item['timestamp']}**")
                    st.write(item['question'])
                    if item.get('printer'):
                        st.caption(f"🖨️ {item['printer']}")
                
                # Resposta do bot
                with st.chat_message("assistant"):
                    if item.get('error'):
                        st.error(item['response'])
                    else:
                        st.markdown(item['response'])
                        if item.get('sources'):
                            st.caption(f"📚 Fontes: {item['sources']} seções do manual")
        
        # Área de input
        st.markdown("---")
        st.subheader("🤔 Faça sua pergunta")
        
        # Formulário de pergunta
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
            
            # Exemplos de perguntas
            st.caption("💡 **Exemplos:** Como limpar os cabeçotes? | Wi-Fi não conecta | Papel atolado | Trocar tinta")
        
        # Processar pergunta
        if submit_button and user_question:
            with st.spinner("🤔 Processando sua pergunta..."):
                # Detectar impressora
                if st.session_state.selected_printer:
                    printer_model = st.session_state.selected_printer
                else:
                    printer_model = detect_printer(user_question, st.session_state.available_models)
                    if not printer_model and len(st.session_state.available_models) > 0:
                        # Se não detectou, usa um modelo padrão ou pede ao usuário
                        st.warning("⚠️ Modelo de impressora não detectado. Usando busca geral.")
                        printer_model = None
                
                # Busca semântica
                with st.spinner("🔍 Buscando informações no manual..."):
                    results = semantic_search(user_question, printer_model)
                
                if results:
                    # Gerar resposta
                    with st.spinner(f"🤖 Gerando resposta {'rápida' if st.session_state.response_mode == 'rapido' else 'detalhada'}..."):
                        success, response = generate_response(
                            user_question,
                            results,
                            st.session_state.response_mode,
                            printer_model
                        )
                    
                    # Adicionar ao histórico
                    history_item = {
                        'timestamp': datetime.now().strftime("%H:%M"),
                        'question': user_question,
                        'response': response,
                        'printer': get_printer_metadata_dynamic(printer_model, None)['full_name'] if printer_model else "Geral",
                        'sources': len(results),
                        'error': not success
                    }
                    
                    st.session_state.conversation_history.append(history_item)
                    
                    # Recarregar para mostrar a nova conversa
                    st.rerun()
                else:
                    st.error("❌ Nenhuma informação relevante encontrada. Tente reformular sua pergunta.")
    
    # Footer com recursos adicionais
    st.markdown("---")
    
    # Exportar histórico
    if st.session_state.conversation_history:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Preparar dados para download
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'total_questions': len(st.session_state.conversation_history),
                'conversations': st.session_state.conversation_history
            }
            
            json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
            
            st.download_button(
                label="📥 Baixar Histórico (JSON)",
                data=json_str,
                file_name=f"chatbot_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    # Informações do rodapé
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🏢 Epson Support**")
        st.caption("Sistema oficial de suporte")
    with col2:
        st.markdown(
            "<div style='text-align: center; color: #888;'>"
            "Desenvolvido com ❤️ usando<br>"
            "Streamlit + ChromaDB + Gemini"
            "</div>",
            unsafe_allow_html=True
        )
    with col3:
        st.markdown("**📊 Status do Sistema**")
        if st.session_state.chromadb_search:
            st.caption("✅ ChromaDB: Online")
        else:
            st.caption("❌ ChromaDB: Offline")

if __name__ == "__main__":
    main()
