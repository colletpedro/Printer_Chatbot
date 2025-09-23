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
if 'funnel_active' not in st.session_state:
    st.session_state.funnel_active = False
if 'funnel_stage' not in st.session_state:
    st.session_state.funnel_stage = None
if 'funnel_answers' not in st.session_state:
    st.session_state.funnel_answers = {}
if 'pending_question' not in st.session_state:
    st.session_state.pending_question = None

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

def filter_printers_by_features(answers):
    """Filtra impressoras baseado nas respostas do usuário"""
    available = []
    
    # Mapeia características para modelos baseado nos metadados disponíveis
    printer_features = {}
    
    print(f"DEBUG: Modelos disponíveis no sistema: {st.session_state.available_models}")
    
    # Usa os modelos disponíveis do sistema e suas características conhecidas
    for model_id in st.session_state.available_models:
        # Características conhecidas dos modelos
        if 'L805' in model_id or 'l805' in model_id:
            printer_features[model_id] = {'a3': False, 'multifuncional': False, 'fax': False, 'adf': False, 'duplex': False}
        elif 'L1300' in model_id or 'l1300' in model_id:
            printer_features[model_id] = {'a3': True, 'multifuncional': False, 'fax': False, 'adf': False, 'duplex': False}
        elif 'L375' in model_id or 'l375' in model_id:
            printer_features[model_id] = {'a3': False, 'multifuncional': True, 'fax': False, 'adf': False, 'duplex': False}
        elif 'L396' in model_id or 'l396' in model_id:
            printer_features[model_id] = {'a3': False, 'multifuncional': True, 'fax': False, 'adf': False, 'duplex': False}
        elif 'L3110' in model_id or 'l3110' in model_id:
            printer_features[model_id] = {'a3': False, 'multifuncional': True, 'fax': False, 'adf': False, 'duplex': False}
        elif 'L3150' in model_id or 'l3150' in model_id:
            printer_features[model_id] = {'a3': False, 'multifuncional': True, 'fax': False, 'adf': False, 'duplex': False}
        elif ('L3250' in model_id or 'l3250' in model_id) or ('L3251' in model_id or 'l3251' in model_id):
            printer_features[model_id] = {'a3': False, 'multifuncional': True, 'fax': False, 'adf': False, 'duplex': True}
        elif 'L4150' in model_id or 'l4150' in model_id:
            printer_features[model_id] = {'a3': False, 'multifuncional': True, 'fax': False, 'adf': True, 'duplex': True}
        elif 'L4260' in model_id or 'l4260' in model_id:
            printer_features[model_id] = {'a3': False, 'multifuncional': True, 'fax': False, 'adf': True, 'duplex': True}
        elif 'L5190' in model_id or 'l5190' in model_id:
            printer_features[model_id] = {'a3': False, 'multifuncional': True, 'fax': True, 'adf': True, 'duplex': True}
        elif 'L5290' in model_id or 'l5290' in model_id:
            printer_features[model_id] = {'a3': False, 'multifuncional': True, 'fax': True, 'adf': True, 'duplex': True}
        elif 'L6490' in model_id or 'l6490' in model_id:
            printer_features[model_id] = {'a3': True, 'multifuncional': True, 'fax': False, 'adf': True, 'duplex': True}
    
    print(f"DEBUG: Features mapeadas: {printer_features}")
    print(f"DEBUG: Respostas do usuário para filtrar: {answers}")
    
    # Filtra baseado nas respostas
    for model_id, features in printer_features.items():
        match = True
        
        # Verifica cada resposta
        if 'multifuncional' in answers:
            if answers['multifuncional'] != features['multifuncional']:
                match = False
        
        if 'a3' in answers:
            if answers['a3'] != features['a3']:
                match = False
        
        if 'duplex' in answers:
            if answers['duplex'] != features['duplex']:
                match = False
        
        if 'adf' in answers:
            if answers['adf'] != features['adf']:
                match = False
        
        if 'fax' in answers:
            if answers['fax'] != features['fax']:
                match = False
        
        if match:
            available.append(model_id)
    
    return available

def get_funnel_question(stage, answers):
    """Retorna a próxima pergunta do afunilamento baseado no estágio"""
    
    if stage == 1:
        return {
            'question': "🖨️ **Sua impressora é multifuncional?**\n\n(Multifuncional = imprime, copia e digitaliza)",
            'options': ['Sim, é multifuncional', 'Não, só imprime', 'Não sei'],
            'key': 'multifuncional'
        }
    
    # Se não é multifuncional, pula direto para A3
    if stage == 2 and answers.get('multifuncional') == False:
        return {
            'question': "📄 **Sua impressora suporta papel A3?**\n\n(A3 = folha grande, 420mm × 297mm)",
            'options': ['Sim, imprime A3', 'Não, apenas A4', 'Não sei'],
            'key': 'a3'
        }
    
    # Se é multifuncional, pergunta sobre duplex
    if stage == 2 and answers.get('multifuncional') == True:
        return {
            'question': "📑 **Sua impressora imprime frente e verso automaticamente (duplex)?**",
            'options': ['Sim, tem duplex', 'Não, apenas um lado', 'Não sei'],
            'key': 'duplex'
        }
    
    # Pergunta sobre ADF (para multifuncionais)
    if stage == 3 and answers.get('multifuncional') == True:
        return {
            'question': "📋 **Sua impressora tem alimentador automático de documentos (ADF)?**\n\n(ADF = bandeja na parte superior para digitalizar várias folhas)",
            'options': ['Sim, tem ADF', 'Não, só vidro do scanner', 'Não sei'],
            'key': 'adf'
        }
    
    # Pergunta sobre FAX (para multifuncionais com ADF)
    if stage == 4 and answers.get('multifuncional') == True and answers.get('adf') == True:
        return {
            'question': "📠 **Sua impressora tem função de FAX?**",
            'options': ['Sim, tem FAX', 'Não tem FAX', 'Não sei'],
            'key': 'fax'
        }
    
    # Pergunta sobre A3 (para multifuncionais)
    if (stage == 5 or (stage == 4 and answers.get('adf') != True)) and answers.get('multifuncional') == True:
        return {
            'question': "📄 **Sua impressora suporta papel A3?**\n\n(A3 = folha grande, 420mm × 297mm)",
            'options': ['Sim, imprime A3', 'Não, apenas A4', 'Não sei'],
            'key': 'a3'
        }
    
    return None

def start_funnel():
    """Inicia o processo de afunilamento"""
    st.session_state.funnel_active = True
    st.session_state.funnel_stage = 1
    st.session_state.funnel_answers = {}

def process_funnel_answer(answer, key):
    """Processa a resposta do afunilamento"""
    # Mapeia resposta para booleano
    if "Sim" in answer:
        st.session_state.funnel_answers[key] = True
    elif "Não" in answer and "Não sei" not in answer:
        st.session_state.funnel_answers[key] = False
    # Se "Não sei", não adiciona ao filtro
    
    # Debug: mostra respostas coletadas
    print(f"DEBUG: Resposta processada - {key}: {st.session_state.funnel_answers.get(key, 'Não sei')}")
    print(f"DEBUG: Todas respostas até agora: {st.session_state.funnel_answers}")
    
    # Avança para próximo estágio
    st.session_state.funnel_stage += 1
    print(f"DEBUG: Avançando para estágio {st.session_state.funnel_stage}")
    
    # Verifica se já pode identificar a impressora
    filtered = filter_printers_by_features(st.session_state.funnel_answers)
    print(f"DEBUG: Modelos filtrados: {filtered} (Total: {len(filtered)})")
    
    if len(filtered) == 1:
        # Encontrou única impressora
        st.session_state.selected_printer = filtered[0]
        st.session_state.funnel_active = False
        st.session_state.funnel_stage = None
        return True, filtered[0]
    elif len(filtered) == 0:
        # Nenhuma impressora corresponde
        st.session_state.funnel_active = False
        st.session_state.funnel_stage = None
        return False, None
    elif st.session_state.funnel_stage > 5 or get_funnel_question(st.session_state.funnel_stage, st.session_state.funnel_answers) is None:
        # Máximo de perguntas atingido ou não há mais perguntas
        if len(filtered) <= 3 and len(filtered) > 0:
            # Mostra opções restantes
            if len(filtered) == 2:
                # Se são exatamente 2 modelos, mostra ambos para escolha
                return None, filtered
            else:
                # Se são 3 modelos, também mostra para escolha
                return None, filtered
        elif len(filtered) == 1:
            # Encontrou única impressora após todas perguntas
            st.session_state.selected_printer = filtered[0]
            st.session_state.funnel_active = False
            st.session_state.funnel_stage = None
            return True, filtered[0]
        else:
            # Nenhuma impressora ou muitas opções
            st.session_state.funnel_active = False
            st.session_state.funnel_stage = None
            return False, None
    
    return None, None

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
        
        # Se há impressora identificada pelo afunilamento
        if st.session_state.selected_printer and not st.session_state.funnel_active:
            current_printer_name = PRINTER_METADATA.get(
                st.session_state.selected_printer, {}
            ).get('full_name', st.session_state.selected_printer)
            st.success(f"📌 Identificada: **{current_printer_name}**")
        
        # Lista de modelos para seleção
        model_options = ["Detectar automaticamente"] + [
            PRINTER_METADATA.get(m, {}).get('full_name', m) 
            for m in st.session_state.available_models 
            if m in PRINTER_METADATA
        ]
        
        # Define o índice padrão baseado na impressora selecionada
        default_index = 0
        if st.session_state.selected_printer:
            printer_name = PRINTER_METADATA.get(st.session_state.selected_printer, {}).get('full_name')
            if printer_name in model_options:
                default_index = model_options.index(printer_name)
        
        selected = st.selectbox(
            "Selecione o modelo:",
            options=model_options,
            index=default_index,
            help="Escolha sua impressora ou deixe o sistema detectar"
        )
        
        if selected != "Detectar automaticamente":
            # Encontra o ID do modelo baseado no nome completo
            for model_id, metadata in PRINTER_METADATA.items():
                if metadata.get('full_name') == selected:
                    # Se mudou de modelo, limpa afunilamento
                    if st.session_state.selected_printer != model_id:
                        st.session_state.funnel_active = False
                        st.session_state.funnel_stage = None
                        st.session_state.funnel_answers = {}
                        
                        # Se tinha uma pergunta pendente e selecionou modelo, processa
                        if st.session_state.pending_question and st.session_state.selected_printer is None:
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"✅ **Modelo selecionado: {selected}**\n\nVou responder sua pergunta agora!"
                            })
                    
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
                st.session_state.funnel_active = False
                st.session_state.funnel_stage = None
                st.session_state.funnel_answers = {}
                st.session_state.pending_question = None
                st.rerun()
        
        # Botão para cancelar afunilamento
        if st.session_state.funnel_active:
            st.markdown("---")
            if st.button("❌ Cancelar Identificação", use_container_width=True, type="secondary"):
                st.session_state.funnel_active = False
                st.session_state.funnel_stage = None
                st.session_state.funnel_answers = {}
                st.session_state.pending_question = None
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
    
    # Sistema de afunilamento ativo
    if st.session_state.funnel_active:
        question_data = get_funnel_question(st.session_state.funnel_stage, st.session_state.funnel_answers)
        
        if question_data:
            # Mostra pergunta do afunilamento
            with st.chat_message("assistant"):
                # Mostra progresso
                if st.session_state.funnel_stage > 1:
                    progress = f"📊 Pergunta {st.session_state.funnel_stage} de no máximo 5\n\n"
                    st.markdown(progress)
                
                st.markdown(question_data['question'])
                
                # Botões de resposta
                cols = st.columns(len(question_data['options']))
                for i, option in enumerate(question_data['options']):
                    with cols[i]:
                        if st.button(option, key=f"funnel_btn_{st.session_state.funnel_stage}_{i}", use_container_width=True):
                            # Processa resposta
                            result, data = process_funnel_answer(option, question_data['key'])
                            
                            # Adiciona ao histórico
                            st.session_state.messages.append({
                                "role": "user", 
                                "content": option
                            })
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": question_data['question']
                            })
                            
                            if result is True:
                                # Impressora identificada
                                printer_name = PRINTER_METADATA.get(data, {}).get('full_name', data)
                                
                                # Adiciona mensagem de identificação ao histórico
                                success_msg = f"✅ **Impressora identificada: {printer_name}**\n\nAgora posso responder sua pergunta!"
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": success_msg
                                })
                                
                                # Marca impressora como selecionada
                                st.session_state.selected_printer = data
                                
                                # Se há pergunta pendente, adiciona ao histórico para processar
                                if st.session_state.pending_question:
                                    # Adiciona a pergunta pendente como se fosse nova
                                    st.session_state.messages.append({
                                        "role": "user",
                                        "content": f"[Pergunta original] {st.session_state.pending_question}"
                                    })
                                    
                                    # Processa a pergunta
                                    with st.spinner('🤖 Processando sua pergunta...'):
                                        response, source = process_user_query(
                                            st.session_state.pending_question,
                                            data,
                                            st.session_state.response_mode
                                        )
                                        
                                        if response:
                                            mode_emoji = "⚡" if st.session_state.response_mode == 'rapido' else "📖"
                                            header = f"{mode_emoji} **[{printer_name}]**\n\n"
                                            st.session_state.messages.append({
                                                "role": "assistant",
                                                "content": header + response,
                                                "source": source
                                            })
                                            st.session_state.question_count += 1
                                
                                # Limpa estado do afunilamento
                                st.session_state.funnel_active = False
                                st.session_state.funnel_stage = None
                                st.session_state.funnel_answers = {}
                                st.session_state.pending_question = None
                                
                                st.rerun()
                            elif result is False:
                                st.error("❌ Não foi possível identificar uma impressora com essas características.")
                                st.session_state.pending_question = None
                                st.rerun()
                            elif result is None and data:
                                # Múltiplas opções - permite escolha
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": f"🔍 **Encontrei {len(data)} modelos possíveis com essas características:**"
                                })
                                
                                # Limpa afunilamento e mostra opções para escolha manual
                                st.session_state.funnel_active = False
                                st.session_state.funnel_stage = None
                                
                                # Adiciona mensagem com modelos possíveis
                                models_list = "\n".join([f"• {PRINTER_METADATA.get(m, {}).get('full_name', m)}" for m in data])
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": f"{models_list}\n\n**Por favor, selecione o modelo na barra lateral ou digite o modelo específico.**"
                                })
                                
                                st.rerun()
                            else:
                                st.rerun()
        else:
            # Fim do afunilamento sem resultado
            st.session_state.funnel_active = False
            st.session_state.funnel_stage = None
    
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
                # Inicia processo de afunilamento
                st.session_state.pending_question = prompt
                start_funnel()
                st.rerun()
        
        # Se chegou aqui, tem modelo de impressora
        if printer_model:
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
