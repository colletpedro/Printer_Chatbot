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
if 'identified_printer' not in st.session_state:
    st.session_state.identified_printer = None
if 'identification_stage' not in st.session_state:
    st.session_state.identification_stage = None

def detect_printer_in_query(query):
    """Detecta se algum modelo de impressora foi mencionado na pergunta"""
    query_lower = query.lower()
    for model in PRINTER_MODELS:
        # Remove "Epson " do modelo para comparação mais flexível
        model_simple = model.replace("Epson ", "").lower()
        if model_simple in query_lower or model.lower() in query_lower:
            return model
    return None

def generate_funnel_question(query, stage=None):
    """Gera pergunta de afunilamento para identificar a impressora"""
    if stage is None or stage == "initial":
        return """🔍 **Preciso identificar sua impressora primeiro!**
        
Para fornecer a melhor assistência, preciso saber o modelo exato da sua impressora Epson.

**Por favor, me informe:**
1. Você sabe o modelo da sua impressora? (Ex: L3150, L375, L4260, etc.)
2. Se não souber, sua impressora é:
   - **Multifuncional** (imprime, copia e digitaliza) ou
   - **Apenas impressora** (só imprime)?
   
Digite o modelo ou responda sobre o tipo da sua impressora."""
    
    elif stage == "type_known":
        return """📋 **Vamos descobrir o modelo específico!**
        
**Me ajude com mais informações:**
- Sua impressora tem **Wi-Fi**?
- Ela tem **tanques de tinta** visíveis na frente ou lateral?
- Você lembra aproximadamente quando comprou? (ano)
- É colorida ou apenas preto e branco?"""
    
    elif stage == "features_known":
        return """🎯 **Estamos quase lá!**
        
**Última pergunta para identificar sua impressora:**
- Você consegue ver alguma etiqueta com o modelo na própria impressora?
- Geralmente fica na parte frontal, superior ou traseira
- Procure por algo como: L3150, L375, L4260, etc.

Se não encontrar, descreva o tamanho aproximado (compacta, média ou grande)."""
    
    else:
        return """❌ **Não consigo prosseguir sem identificar sua impressora**
        
Infelizmente, para fornecer suporte técnico preciso e seguro, preciso saber o modelo exato da sua impressora Epson.

**Sugestões:**
- Verifique a nota fiscal ou manual
- Procure uma etiqueta na impressora
- Acesse as configurações da impressora no computador

Quando souber o modelo, me informe para eu poder ajudar! 🖨️"""

def generate_response(query, printer_model=None, mode="detalhado"):
    """Gera resposta usando Gemini - APENAS se souber o modelo da impressora"""
    
    # NÃO responde sem modelo de impressora
    if not printer_model:
        return None
    
    try:
        # Ajusta o prompt baseado no modo
        if mode == "rápido":
            mode_instruction = """
            Forneça uma resposta BREVE e DIRETA, em no máximo 3-4 frases.
            Vá direto ao ponto principal sem muitos detalhes.
            IMPORTANTE: Seja específico para o modelo de impressora informado.
            """
        else:  # detalhado
            mode_instruction = """
            Forneça uma resposta COMPLETA e DETALHADA.
            Inclua:
            - Explicação passo a passo específica para este modelo
            - Possíveis causas do problema neste modelo específico
            - Soluções alternativas se existirem
            - Dicas de prevenção para este modelo
            IMPORTANTE: Todas as informações devem ser específicas para o modelo informado.
            """
        
        prompt = f"""Você é um especialista em impressoras Epson.
        
        Modelo da impressora: {printer_model}
        
        {mode_instruction}
        
        REGRA CRÍTICA: Forneça informações ESPECÍFICAS para o modelo {printer_model}.
        Não dê respostas genéricas. Se não souber algo específico deste modelo, seja honesto.
        
        Pergunta do usuário: {query}
        
        Responda em português de forma clara e específica para o modelo {printer_model}."""
        
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
    
    # Atualizar impressora identificada quando selecionada manualmente
    if selected_printer != "Não especificado":
        st.session_state.identified_printer = selected_printer
        st.session_state.identification_stage = None
        st.success(f"✅ Modelo identificado: {selected_printer}")
    elif st.session_state.identified_printer:
        st.info(f"📌 Modelo detectado: {st.session_state.identified_printer}")
    
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
        st.session_state.identified_printer = None
        st.session_state.identification_stage = None
        st.rerun()
    
    # Resetar identificação
    if st.session_state.identified_printer and st.button("🔄 Trocar Impressora", use_container_width=True):
        st.session_state.identified_printer = None
        st.session_state.identification_stage = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Versão:** 2.0")
    st.markdown("**Status:** ✅ Online")
    st.markdown("**Modo:** Afunilamento Obrigatório")

# Mostrar mensagem inicial se não houver histórico
if not st.session_state.messages and not st.session_state.identified_printer:
    with st.chat_message("assistant"):
        welcome_msg = """👋 **Olá! Bem-vindo ao Suporte Técnico Epson!**
        
Para fornecer o melhor suporte possível, preciso identificar o modelo exato da sua impressora.

**Você pode:**
1. Selecionar o modelo na barra lateral ➡️
2. Digitar o modelo diretamente (Ex: "Minha impressora é L3150")
3. Responder algumas perguntas para eu identificar sua impressora

**Como posso ajudar você hoje?**"""
        st.markdown(welcome_msg)

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
    
    # Detectar modelo na pergunta
    detected_model = detect_printer_in_query(prompt)
    
    # Atualizar modelo identificado se detectado
    if detected_model:
        st.session_state.identified_printer = detected_model
        st.session_state.identification_stage = None
    
    # Determinar qual modelo usar
    printer_to_use = None
    if selected_printer != "Não especificado":
        printer_to_use = selected_printer
    elif st.session_state.identified_printer:
        printer_to_use = st.session_state.identified_printer
    elif detected_model:
        printer_to_use = detected_model
    
    # Gerar e mostrar resposta
    with st.chat_message("assistant"):
        with st.spinner("Processando..."):
            # Se temos um modelo, gerar resposta normal
            if printer_to_use:
                response = generate_response(
                    prompt, 
                    printer_to_use,
                    mode=st.session_state.response_mode
                )
                
                # Adicionar indicador do modelo usado
                response_with_model = f"**[{printer_to_use}]** {response}"
                st.markdown(response_with_model)
                
                # Adicionar resposta ao histórico
                st.session_state.messages.append({"role": "assistant", "content": response_with_model})
            
            # Se não temos modelo, iniciar afunilamento
            else:
                # Analisar resposta do usuário para avançar no afunilamento
                prompt_lower = prompt.lower()
                
                # Verificar se usuário está respondendo sobre tipo de impressora
                if st.session_state.identification_stage == "initial":
                    if "multifuncional" in prompt_lower or "copia" in prompt_lower or "digitaliza" in prompt_lower:
                        st.session_state.identification_stage = "type_known"
                    elif "só imprime" in prompt_lower or "apenas imprime" in prompt_lower:
                        st.session_state.identification_stage = "type_known"
                
                # Verificar se usuário está respondendo sobre recursos
                elif st.session_state.identification_stage == "type_known":
                    if any(word in prompt_lower for word in ["wifi", "wi-fi", "tanque", "colorida", "preto"]):
                        st.session_state.identification_stage = "features_known"
                
                # Verificar se usuário está respondendo sobre características finais
                elif st.session_state.identification_stage == "features_known":
                    if any(word in prompt_lower for word in ["compacta", "média", "grande", "pequena"]):
                        st.session_state.identification_stage = "failed"
                
                # Gerar pergunta de afunilamento apropriada
                funnel_response = generate_funnel_question(prompt, st.session_state.identification_stage)
                st.markdown(funnel_response)
                
                # Atualizar estágio se for inicial
                if st.session_state.identification_stage is None:
                    st.session_state.identification_stage = "initial"
                
                # Adicionar resposta ao histórico
                st.session_state.messages.append({"role": "assistant", "content": funnel_response})
