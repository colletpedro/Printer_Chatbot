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

def normalize_text(text):
    """Normaliza texto para comparação mais flexível"""
    import unicodedata
    import re
    
    # Converter para lowercase
    text = text.lower().strip()
    
    # Remover acentos
    text = ''.join(c for c in unicodedata.normalize('NFD', text) 
                   if unicodedata.category(c) != 'Mn')
    
    # Remover pontuação e múltiplos espaços
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def detect_printer_in_query(query):
    """Detecta se algum modelo de impressora foi mencionado na pergunta"""
    query_normalized = normalize_text(query)
    
    for model in PRINTER_MODELS:
        # Remove "Epson " do modelo para comparação mais flexível
        model_simple = model.replace("Epson ", "").lower()
        model_normalized = normalize_text(model_simple)
        
        # Verificar variações
        variations = [
            model_normalized,
            model_normalized.replace(" ", ""),
            model_normalized.replace("l", "l "),  # L3150 → L 3150
        ]
        
        for variant in variations:
            if variant in query_normalized:
                return model
    return None

def analyze_user_response(prompt, stage):
    """Analisa resposta do usuário de forma inteligente e flexível"""
    # Normalizar texto para comparação
    prompt_normalized = normalize_text(prompt)
    
    if stage == "initial" or stage is None:
        # Verificar se é multifuncional
        multifuncional_keywords = [
            "multifuncional", "multi funcional", "mult", "3 em 1", "3em1",
            "copia", "copiar", "copi", "digitaliza", "digitalizar", "digital",
            "scanner", "scan", "escanear", "escaneamento", "xerox",
            "todas", "tudo", "completa", "sim ela copia", "sim copia",
            "faz copia", "tem scanner", "tem copia"
        ]
        
        # Verificar impressora simples
        simples_keywords = [
            "so imprime", "apenas imprime", "apenas impressora", "somente imprime",
            "simples", "basica", "normal", "comum", "nao copia", "nao digitaliza",
            "sem scanner", "sem copia", "impressora apenas", "so impressao",
            "nao ela so imprime", "nao so imprime"
        ]
        
        # Testar multifuncional
        for keyword in multifuncional_keywords:
            if keyword in prompt_normalized:
                return "type_known_multi"
        
        # Testar simples
        for keyword in simples_keywords:
            if keyword in prompt_normalized:
                return "type_known_simple"
        
        # Verificar respostas diretas sim/não
        if any(word in prompt_normalized for word in ["sim", "yes", "uhum", "aham", "isso"]):
            # Se disse sim na pergunta sobre multifuncional
            return "type_known_multi"
        
        if any(word in prompt_normalized for word in ["nao", "no", "nop", "negativo"]):
            # Se disse não na pergunta sobre multifuncional  
            return "type_known_simple"
            
        # Verificar se não sabe
        if any(phrase in prompt_normalized for phrase in ["nao sei", "nao lembro", "esqueci", "nao tenho certeza"]):
            return "need_help"
    
    elif stage in ["type_known", "type_known_multi", "type_known_simple"]:
        # Coletar características
        features_detected = []
        
        # WiFi
        if any(word in prompt_normalized for word in ["wifi", "wi fi", "wireless", "sem fio", "rede", "internet"]):
            features_detected.append("wifi")
        elif any(word in prompt_normalized for word in ["sem wifi", "nao tem wifi", "cabo", "usb apenas"]):
            features_detected.append("no_wifi")
        
        # Tanque
        if any(word in prompt_normalized for word in ["tanque", "tank", "ecotank", "eco tank", "refil", "garrafa"]):
            features_detected.append("tanque")
        elif any(word in prompt_normalized for word in ["cartucho", "sem tanque", "nao tem tanque"]):
            features_detected.append("no_tanque")
        
        # Cores
        if any(word in prompt_normalized for word in ["colorida", "colorido", "cores", "color", "cmyk"]):
            features_detected.append("colorida")
        elif any(word in prompt_normalized for word in ["preto e branco", "preto branco", "pb", "monocromatica", "mono"]):
            features_detected.append("pb")
        
        # Idade
        if any(word in prompt_normalized for word in ["nova", "novo", "recente", "2024", "2023", "2022", "ano passado"]):
            features_detected.append("nova")
        elif any(word in prompt_normalized for word in ["antiga", "antigo", "velha", "velho", "anos atras", "2020", "2019", "2018"]):
            features_detected.append("antiga")
        
        if features_detected:
            return "features_known"
        
        # Respostas genéricas sim/não
        if any(word in prompt_normalized for word in ["sim", "tem", "possui", "isso", "claro"]):
            return "features_known"  # Avançar
        elif any(word in prompt_normalized for word in ["nao", "nao tem", "sem", "negativo"]):
            return "features_known"  # Avançar
    
    elif stage == "features_known":
        # Verificar tamanhos
        if any(word in prompt_normalized for word in ["compacta", "pequena", "pequeno", "mini", "portatil"]):
            return "size_known"
        elif any(word in prompt_normalized for word in ["media", "medio", "normal", "padrao", "regular"]):
            return "size_known"
        elif any(word in prompt_normalized for word in ["grande", "gigante", "robusta", "profissional", "escritorio"]):
            return "size_known"
        
        # Verificar se usuário desistiu
        if any(word in prompt_normalized for word in ["desisto", "nao consigo", "nao sei", "deixa", "esquece", "cancela"]):
            return "failed"
    
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
   
💡 Pode responder de forma simples como "é multifuncional" ou "só imprime"."""
    
    elif stage == "need_help":
        return """🤔 **Sem problemas! Vou te ajudar a descobrir!**
        
**Vamos começar com algo simples:**
Sua impressora tem uma **tampa em cima que abre** para colocar documentos?
(Isso é o scanner - se tem, é multifuncional)

- **SIM** → É multifuncional
- **NÃO** → É impressora simples

Responda com suas palavras! 😊"""
    
    elif stage == "type_known_multi":
        return """✅ **Ótimo! Sua impressora é multifuncional!**
        
**Agora me conte sobre estas características:**
- Tem **Wi-Fi** ou conexão sem fio?
- Você vê **tanques de tinta** transparentes na frente ou lateral?
- É **colorida** ou só **preto e branco**?
- É **nova** (últimos 2 anos) ou mais **antiga**?

💡 Responda o que souber, não precisa ser tudo!"""
    
    elif stage == "type_known_simple":
        return """✅ **Ok! Sua impressora é modelo simples (só imprime)!**
        
**Me ajude com algumas informações:**
- Tem **tanques de tinta** visíveis?
- É **colorida** ou **preto e branco**?
- Qual o **tamanho** dela? (pequena, média, grande)

💡 Qualquer detalhe ajuda!"""
    
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
- Você consegue ver alguma **etiqueta com o modelo** na própria impressora?
- Geralmente fica na parte frontal, superior ou traseira
- Procure por algo como: **L3150, L375, L4260**, etc.

Se não encontrar, me diga o **tamanho** (pequena, média ou grande)."""
    
    elif stage in ["size_known", "failed"]:
        return """❌ **Não consegui identificar o modelo exato**
        
Para sua segurança, preciso saber o modelo específico antes de dar instruções técnicas.

**Por favor, tente:**
1. **Olhar a etiqueta** na impressora (frente, tampa ou atrás)
2. **Verificar a nota fiscal** ou caixa
3. **Olhar no manual** da impressora
4. **Ver nas configurações** do computador

O modelo sempre começa com **"L"** seguido de números (Ex: L3150, L805)

Quando souber, me diga! 🖨️"""
    
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
                # Usar função inteligente de análise
                current_stage = st.session_state.identification_stage
                analysis_result = analyze_user_response(prompt, current_stage)
                
                # Determinar próximo estágio baseado na análise
                if analysis_result:
                    new_stage = analysis_result
                else:
                    # Se não entendeu a resposta, manter no mesmo estágio
                    new_stage = current_stage if current_stage else "initial"
                
                # Atualizar estágio
                st.session_state.identification_stage = new_stage
                
                # Gerar pergunta de afunilamento apropriada
                funnel_response = generate_funnel_question(prompt, new_stage)
                st.markdown(funnel_response)
                
                # Adicionar resposta ao histórico
                st.session_state.messages.append({"role": "assistant", "content": funnel_response})
