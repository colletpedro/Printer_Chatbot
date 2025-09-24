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
if 'funnel_active' not in st.session_state:
    st.session_state.funnel_active = False
if 'funnel_stage' not in st.session_state:
    st.session_state.funnel_stage = None
if 'funnel_answers' not in st.session_state:
    st.session_state.funnel_answers = {}
if 'pending_question' not in st.session_state:
    st.session_state.pending_question = None
if 'auto_selected' not in st.session_state:
    st.session_state.auto_selected = False
if 'selection_counter' not in st.session_state:
    st.session_state.selection_counter = 0

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

def filter_printers_by_features(answers):
    """Filtra impressoras baseado nas respostas do usuário"""
    available = []
    
    # Define características conhecidas dos modelos
    printer_features = {
        'L805': {'a3': False, 'multifuncional': False, 'fax': False, 'adf': False, 'duplex': False},
        'L1300': {'a3': True, 'multifuncional': False, 'fax': False, 'adf': False, 'duplex': False},
        'L375': {'a3': False, 'multifuncional': True, 'fax': False, 'adf': False, 'duplex': False},
        'L396': {'a3': False, 'multifuncional': True, 'fax': False, 'adf': False, 'duplex': False},
        'L3110': {'a3': False, 'multifuncional': True, 'fax': False, 'adf': False, 'duplex': False},
        'L3150': {'a3': False, 'multifuncional': True, 'fax': False, 'adf': False, 'duplex': False},
        'L3250': {'a3': False, 'multifuncional': True, 'fax': False, 'adf': False, 'duplex': True},
        'L4150': {'a3': False, 'multifuncional': True, 'fax': False, 'adf': True, 'duplex': True},
        'L4260': {'a3': False, 'multifuncional': True, 'fax': False, 'adf': True, 'duplex': True},
        'L5190': {'a3': False, 'multifuncional': True, 'fax': True, 'adf': True, 'duplex': True},
        'L5290': {'a3': False, 'multifuncional': True, 'fax': True, 'adf': True, 'duplex': True},
        'L6490': {'a3': True, 'multifuncional': True, 'fax': False, 'adf': True, 'duplex': True}
    }
    
    # Filtra baseado nas respostas
    for model_id, features in printer_features.items():
        match = True
        
        for key, value in answers.items():
            if key in features and features[key] != value:
                match = False
                break
        
        if match:
            available.append(model_id)
    
    return available

def get_funnel_question(stage, answers):
    """Retorna a próxima pergunta do afunilamento"""
    
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
    
    # Pergunta sobre ADF
    if stage == 3 and answers.get('multifuncional') == True:
        return {
            'question': "📋 **Sua impressora tem alimentador automático de documentos (ADF)?**\n\n(ADF = bandeja na parte superior para digitalizar várias folhas)",
            'options': ['Sim, tem ADF', 'Não, só vidro do scanner', 'Não sei'],
            'key': 'adf'
        }
    
    # Pergunta sobre FAX
    if stage == 4 and answers.get('multifuncional') == True and answers.get('adf') == True:
        return {
            'question': "📠 **Sua impressora tem função de FAX?**",
            'options': ['Sim, tem FAX', 'Não tem FAX', 'Não sei'],
            'key': 'fax'
        }
    
    # Pergunta sobre A3
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
    
    # Avança para próximo estágio
    st.session_state.funnel_stage += 1
    
    # Verifica se já pode identificar a impressora
    filtered = filter_printers_by_features(st.session_state.funnel_answers)
    
    if len(filtered) == 1:
        # Encontrou única impressora - NÃO modifica session_state aqui!
        # Deixa o código principal fazer isso após processar
        return True, filtered[0]
    elif len(filtered) == 0:
        # Nenhuma impressora corresponde
        return False, None
    elif st.session_state.funnel_stage > 5 or get_funnel_question(st.session_state.funnel_stage, st.session_state.funnel_answers) is None:
        # Máximo de perguntas atingido
        if len(filtered) <= 3 and len(filtered) > 0:
            return None, filtered
        else:
            return False, None
    
    return None, None

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
        
        # Mostra status atual ANTES do selectbox
        if st.session_state.selected_printer:
            printer_name = PRINTER_METADATA.get(st.session_state.selected_printer, st.session_state.selected_printer)
            if st.session_state.get('auto_selected', False):
                st.success(f"✅ **{printer_name}** (selecionada automaticamente)")
            else:
                st.info(f"📌 **{printer_name}** (selecionada)")
        
        printer_options = ['Detecção Automática'] + list(PRINTER_METADATA.keys())
        
        # Sempre mostra o selectbox com o valor atual
        selected = st.selectbox(
            "Alterar modelo:" if st.session_state.selected_printer else "Selecione o modelo:",
            options=printer_options,
            index=0 if not st.session_state.selected_printer else printer_options.index(st.session_state.selected_printer) if st.session_state.selected_printer in printer_options else 0,
            key="printer_selector",
            help="Selecione manualmente ou deixe em 'Detecção Automática' para identificação inteligente"
        )
        
        # Processa mudança manual
        if selected != 'Detecção Automática':
            if selected != st.session_state.selected_printer:
                st.session_state.selected_printer = selected
                st.session_state.auto_selected = False
                st.rerun()
        else:
            # Se mudou para Detecção Automática manualmente
            if st.session_state.selected_printer and not st.session_state.get('auto_selected', False):
                st.session_state.selected_printer = None
                st.session_state.auto_selected = False
                st.rerun()
        
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
        st.caption("**Versão:** 2.0.5 Cloud (24/09 - Funnel Fix)")
        st.caption("**Última Atualização:** 15:35")
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
    
    # Sistema de afunilamento ativo
    if st.session_state.funnel_active:
        question_data = get_funnel_question(st.session_state.funnel_stage, st.session_state.funnel_answers)
        
        if question_data:
            # Mostra pergunta do afunilamento
            with st.chat_message("assistant"):
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
                            
                            # Adiciona pergunta e resposta ao histórico
                            if not any(msg['content'] == question_data['question'] for msg in st.session_state.messages[-2:] if msg['role'] == 'assistant'):
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": question_data['question']
                                })
                            
                            st.session_state.messages.append({
                                "role": "user", 
                                "content": option
                            })
                            
                            if result is True:
                                # Impressora identificada - marca como selecionada automaticamente
                                st.session_state.selected_printer = data
                                st.session_state.auto_selected = True
                                st.session_state.selection_counter = st.session_state.get('selection_counter', 0) + 1
                                
                                printer_name = PRINTER_METADATA.get(data, data)
                                success_msg = f"✅ **Impressora identificada: {printer_name}**\n\nAgora posso responder sua pergunta!\n\n💡 *Impressora {printer_name} selecionada automaticamente na barra lateral*"
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": success_msg
                                })
                                
                                # Se há pergunta pendente, processa
                                if st.session_state.pending_question:
                                    with st.spinner('🤖 Processando...'):
                                        response, source = process_query_simple(
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
                                
                                # Limpa estado do afunilamento
                                st.session_state.funnel_active = False
                                st.session_state.funnel_stage = None
                                st.session_state.funnel_answers = {}
                                st.session_state.pending_question = None
                                # Força atualização completa
                                st.rerun()
                            
                            elif result is False:
                                st.error("❌ Não foi possível identificar uma impressora com essas características.")
                                # Limpa o afunilamento quando não encontra impressora
                                st.session_state.funnel_active = False
                                st.session_state.funnel_stage = None
                                st.session_state.funnel_answers = {}
                                st.session_state.pending_question = None
                                st.rerun()
                            
                            elif result is None and data:
                                # Múltiplas opções - mostra escolha
                                with st.chat_message("assistant"):
                                    st.markdown("🔍 **Encontrei algumas opções. Qual é a sua impressora?**")
                                    for model in data:
                                        model_name = PRINTER_METADATA.get(model, model)
                                        if st.button(f"➡️ {model_name}", key=f"select_{model}", use_container_width=True):
                                            # Marca impressora como selecionada automaticamente
                                            st.session_state.selected_printer = model
                                            st.session_state.auto_selected = True
                                            st.session_state.selection_counter = st.session_state.get('selection_counter', 0) + 1
                                            st.session_state.funnel_active = False
                                            st.session_state.funnel_stage = None
                                            st.session_state.funnel_answers = {}
                                            
                                            # Adiciona mensagem informando a seleção
                                            st.session_state.messages.append({
                                                "role": "assistant",
                                                "content": f"✅ **{model_name} selecionada!**\n\n💡 *Impressora configurada na barra lateral*"
                                            })
                                            
                                            # Processa pergunta pendente
                                            if st.session_state.pending_question:
                                                with st.spinner('🤖 Processando...'):
                                                    response, source = process_query_simple(
                                                        st.session_state.pending_question,
                                                        model,
                                                        st.session_state.response_mode
                                                    )
                                                    if response:
                                                        mode_emoji = "⚡" if st.session_state.response_mode == 'rapido' else "📖"
                                                        header = f"{mode_emoji} **[{model_name}]**\n\n"
                                                        st.session_state.messages.append({
                                                            "role": "assistant",
                                                            "content": header + response,
                                                            "source": source
                                                        })
                                            st.session_state.pending_question = None
                                            st.rerun()
                            else:
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
                # Marca como selecionada automaticamente
                st.session_state.selected_printer = detected
                st.session_state.auto_selected = True
                st.session_state.selection_counter = st.session_state.get('selection_counter', 0) + 1
                with st.chat_message("assistant"):
                    st.info(f"🔍 Detectado: **{PRINTER_METADATA.get(detected, detected)}**\n\n💡 *Impressora selecionada automaticamente na barra lateral*")
            else:
                # Inicia processo de afunilamento
                st.session_state.pending_question = prompt
                start_funnel()
                st.rerun()
        
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
