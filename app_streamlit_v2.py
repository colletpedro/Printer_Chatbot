#!/usr/bin/env python3
"""
Chatbot Epson - Interface Streamlit V2
Versão com sistema de afunilamento melhorado
- Uma pergunta por vez
- Sem loops de perguntas repetidas  
- Não responde quando não entende após múltiplas tentativas
"""

import streamlit as st
import google.generativeai as genai
import re

# Configuração da página
st.set_page_config(
    page_title="Chatbot Epson V2 - Suporte Técnico",
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
if 'funnel_features' not in st.session_state:
    st.session_state.funnel_features = {}
if 'funnel_attempt' not in st.session_state:
    st.session_state.funnel_attempt = 0
if 'stage_attempts' not in st.session_state:
    st.session_state.stage_attempts = 0

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
    """Analisa resposta do usuário de forma linear e clara"""
    prompt_normalized = normalize_text(prompt)
    
    # Respostas muito curtas ou sem contexto - ignorar
    if len(prompt_normalized) < 2:
        return None
    
    # Detecção se o usuário desistiu (em qualquer estágio)
    if any(word in prompt_normalized for word in ["desisto", "nao consigo", "nao sei mesmo", "deixa pra la", "esquece", "cancela"]):
        return "failed"
    
    # Se o usuário está fazendo uma pergunta nova (não relacionada ao afunilamento)
    question_indicators = ["como", "porque", "por que", "quando", "onde", "o que", "qual problema", "ajuda com"]
    if any(indicator in prompt_normalized for indicator in question_indicators):
        # Não processar como resposta de afunilamento
        return None
    
    # ESTÁGIO 1: Identificar tipo (multifuncional ou simples)
    if stage == "initial" or stage is None:
        multifuncional_keywords = [
            "multifuncional", "multi funcional", "mult", "3 em 1", "3em1",
            "copia", "copiar", "digitaliza", "digitalizar", "scanner", "scan",
            "escanear", "xerox", "todas funcoes", "sim ela copia"
        ]
        
        simples_keywords = [
            "so imprime", "apenas imprime", "apenas impressora", "somente imprime",
            "simples", "basica", "nao copia", "nao digitaliza", "sem scanner"
        ]
        
        # Testar tipo
        for keyword in multifuncional_keywords:
            if keyword in prompt_normalized:
                st.session_state.funnel_features['tipo'] = 'multifuncional'
                return "ask_wifi"
        
        for keyword in simples_keywords:
            if keyword in prompt_normalized:
                st.session_state.funnel_features['tipo'] = 'simples'
                return "ask_tanque"
        
        # Respostas sim/não contextuais
        if any(word in prompt_normalized for word in ["sim", "yes", "uhum", "aham", "claro", "isso"]):
            st.session_state.funnel_features['tipo'] = 'multifuncional'
            return "ask_wifi"
        
        if any(word in prompt_normalized for word in ["nao", "no", "nop", "negativo"]):
            st.session_state.funnel_features['tipo'] = 'simples'
            return "ask_tanque"
        
        if any(phrase in prompt_normalized for phrase in ["nao sei", "nao lembro", "nao tenho certeza"]):
            return "need_visual_help"
    
    # ESTÁGIO 2: Perguntar sobre Wi-Fi (apenas para multifuncionais)
    elif stage == "ask_wifi":
        # Respostas positivas específicas para WiFi
        if any(word in prompt_normalized for word in ["wifi", "wi fi", "wireless", "sem fio", "rede wifi"]):
            st.session_state.funnel_features['wifi'] = True
            return "ask_tanque"
        # Resposta genérica "sim" só se for curta e clara
        elif prompt_normalized in ["sim", "tem", "sim tem", "tem sim", "possui", "sim possui"]:
            st.session_state.funnel_features['wifi'] = True
            return "ask_tanque"
        # Respostas negativas específicas
        elif any(word in prompt_normalized for word in ["sem wifi", "nao tem wifi", "cabo", "usb apenas", "fio"]):
            st.session_state.funnel_features['wifi'] = False
            return "ask_tanque"
        # Resposta genérica "não" só se for curta e clara
        elif prompt_normalized in ["nao", "nao tem", "sem", "negativo", "n", "nop"]:
            st.session_state.funnel_features['wifi'] = False
            return "ask_tanque"
        elif any(phrase in prompt_normalized for phrase in ["nao sei", "nao lembro", "nao tenho certeza"]):
            return "ask_tanque"  # Pula se não souber
        # Não entendeu
        return None
    
    # ESTÁGIO 3: Perguntar sobre tanque de tinta
    elif stage == "ask_tanque":
        # Respostas positivas específicas para tanque
        if any(word in prompt_normalized for word in ["tanque", "tank", "ecotank", "eco tank", "refil", "garrafa", "reservatorio"]):
            st.session_state.funnel_features['tanque'] = True
            return "ask_color"
        # Respostas indicando que vê tanques
        elif any(phrase in prompt_normalized for phrase in ["vejo tanque", "sim vejo", "vejo sim", "tem tanque"]):
            st.session_state.funnel_features['tanque'] = True
            return "ask_color"
        # Resposta genérica "sim" apenas se for muito clara
        elif prompt_normalized in ["sim", "vejo", "sim tem", "tem sim"]:
            st.session_state.funnel_features['tanque'] = True
            return "ask_color"
        # Respostas negativas específicas
        elif any(word in prompt_normalized for word in ["cartucho", "usa cartucho", "sem tanque", "nao vejo tanque"]):
            st.session_state.funnel_features['tanque'] = False
            return "ask_color"
        # Resposta genérica "não" apenas se for clara
        elif prompt_normalized in ["nao", "nao vejo", "nao tem", "usa cartucho"]:
            st.session_state.funnel_features['tanque'] = False
            return "ask_color"
        elif any(phrase in prompt_normalized for phrase in ["nao sei", "nao lembro", "nao tenho certeza"]):
            return "ask_color"  # Pula se não souber
        # Não entendeu
        return None
    
    # ESTÁGIO 4: Perguntar sobre colorida
    elif stage == "ask_color":
        # Respostas positivas específicas para colorida
        if any(word in prompt_normalized for word in ["colorida", "colorido", "cores", "color", "cmyk"]):
            st.session_state.funnel_features['colorida'] = True
            return "ask_size"
        # Respostas negativas específicas
        elif any(phrase in prompt_normalized for phrase in ["preto e branco", "preto branco", "pb", "monocromatica", "mono", "apenas preto", "so preto"]):
            st.session_state.funnel_features['colorida'] = False
            return "ask_size"
        # Respostas genéricas só em contexto muito claro
        elif prompt_normalized == "sim" and "color" in str(st.session_state.messages[-2:]).lower():
            st.session_state.funnel_features['colorida'] = True
            return "ask_size"
        elif prompt_normalized == "nao" and "color" in str(st.session_state.messages[-2:]).lower():
            st.session_state.funnel_features['colorida'] = False
            return "ask_size"
        elif any(phrase in prompt_normalized for phrase in ["nao sei", "nao lembro", "nao tenho certeza"]):
            return "ask_size"  # Pula se não souber
        # Não entendeu
        return None
    
    # ESTÁGIO 5: Perguntar sobre tamanho
    elif stage == "ask_size":
        # Tamanhos específicos
        if any(word in prompt_normalized for word in ["pequena", "pequeno", "compacta", "mini", "portatil"]):
            st.session_state.funnel_features['tamanho'] = 'pequena'
            return "try_identify"
        elif any(word in prompt_normalized for word in ["media", "medio", "normal", "padrao", "regular"]):
            st.session_state.funnel_features['tamanho'] = 'media'
            return "try_identify"
        elif any(word in prompt_normalized for word in ["grande", "gigante", "robusta", "profissional", "escritorio", "enorme"]):
            st.session_state.funnel_features['tamanho'] = 'grande'
            return "try_identify"
        elif any(phrase in prompt_normalized for phrase in ["nao sei", "nao lembro", "nao tenho certeza"]):
            return "ask_visual_check"
        # Não entendeu
        return None
    
    # ESTÁGIO 6: Tentativa de identificação visual
    elif stage == "ask_visual_check":
        # Procurar por qualquer menção de modelo
        pattern = r'[lL]\s*\d{3,4}'
        matches = re.findall(pattern, prompt)
        if matches:
            # Tentar detectar o modelo mencionado
            detected = detect_printer_in_query(prompt)
            if detected:
                st.session_state.identified_printer = detected
                return "model_identified"
        return "failed"
    
    # Estados especiais
    elif stage == "need_visual_help":
        if any(word in prompt_normalized for word in ["tampa", "sim", "tem", "vejo", "abre"]):
            st.session_state.funnel_features['tipo'] = 'multifuncional'
            return "ask_wifi"
        elif any(word in prompt_normalized for word in ["nao", "sem tampa", "nao tem", "nao abre"]):
            st.session_state.funnel_features['tipo'] = 'simples'
            return "ask_tanque"
    
    return None

def generate_contextual_hint(stage):
    """Gera dicas contextuais quando não entende a resposta do usuário"""
    if stage == "initial":
        return """🤔 **Não entendi sua resposta...**
        
Por favor, responda de forma simples:
- **"é multifuncional"** se ela imprime, copia e digitaliza
- **"só imprime"** se ela apenas imprime
- **"não sei"** se não tiver certeza"""
    
    elif stage == "ask_wifi":
        return """🤔 **Não entendi sobre o Wi-Fi...**
        
Tente responder:
- **"sim"** ou **"tem wifi"** se tem conexão sem fio
- **"não"** ou **"sem wifi"** se precisa de cabo
- **"não sei"** se não tiver certeza"""
    
    elif stage == "ask_tanque":
        return """🤔 **Não entendi sobre os tanques...**
        
Responda:
- **"sim"** ou **"vejo tanques"** se tem reservatórios transparentes de tinta
- **"não"** ou **"usa cartucho"** se usa cartuchos tradicionais
- **"não sei"** se não tiver certeza"""
    
    elif stage == "ask_color":
        return """🤔 **Não entendi sobre as cores...**
        
Diga simplesmente:
- **"colorida"** se imprime em cores
- **"preto e branco"** se só imprime em preto
- **"não sei"** se não tiver certeza"""
    
    elif stage == "ask_size":
        return """🤔 **Não entendi sobre o tamanho...**
        
Escolha um:
- **"pequena"** - Compacta, cabe em mesa pequena
- **"média"** - Tamanho padrão de escritório
- **"grande"** - Robusta, profissional"""
    
    # Para outros estágios, retornar None (não responder)
    return None

def identify_possible_models(features):
    """Identifica possíveis modelos baseado nas características coletadas"""
    possible = []
    
    # Mapear características para modelos
    if features.get('tipo') == 'multifuncional':
        if features.get('tanque'):
            # Multifuncionais com tanque
            if features.get('wifi'):
                if features.get('colorida', True):
                    if features.get('tamanho') == 'pequena':
                        possible.extend(['L3150', 'L3250'])
                    elif features.get('tamanho') == 'media':
                        possible.extend(['L4260', 'L4150'])
                    else:
                        possible.extend(['L5290', 'L6490'])
                else:
                    possible.append('L5190')  # Mono com tanque
            else:
                # Sem WiFi com tanque
                possible.extend(['L3110', 'L3251'])
        else:
            # Multifuncionais com cartucho
            if features.get('wifi'):
                possible.extend(['L396', 'L375'])
    else:
        # Impressoras simples (não multifuncionais)
        if features.get('tanque'):
            if features.get('tamanho') == 'grande':
                possible.append('L1300')
            else:
                possible.append('L805')
    
    return possible

def generate_funnel_question(query, stage=None):
    """Gera uma pergunta por vez para identificar a impressora"""
    
    # Pergunta inicial
    if stage is None or stage == "initial":
        return """🔍 **Preciso identificar sua impressora primeiro!**
        
Para fornecer o melhor suporte, preciso saber o modelo da sua impressora Epson.

**Pergunta rápida:**
Sua impressora é **multifuncional** (imprime, copia e digitaliza) ou **apenas imprime**?

💡 Responda simplesmente: "é multifuncional" ou "só imprime\""""
    
    # Ajuda visual para identificar tipo
    elif stage == "need_visual_help":
        return """🤔 **Vamos descobrir juntos!**
        
**Olhe para sua impressora:**
Ela tem uma **tampa em cima que abre** para colocar documentos?
(Isso seria o scanner)

✅ **SIM** = É multifuncional
❌ **NÃO** = É impressora simples"""
    
    # Pergunta sobre Wi-Fi (para multifuncionais)
    elif stage == "ask_wifi":
        features = st.session_state.funnel_features
        tipo = features.get('tipo', '')
        
        return f"""✅ **Ótimo! Sua impressora é {tipo}!**
        
**Próxima pergunta:**
Sua impressora tem **Wi-Fi** (conexão sem fio)?

💡 Responda: "sim", "não" ou "não sei"""
    
    # Pergunta sobre tanque
    elif stage == "ask_tanque":
        features = st.session_state.funnel_features
        tipo = features.get('tipo', 'impressora')
        
        tipo_msg = "multifuncional" if tipo == "multifuncional" else "impressora"
        wifi_msg = ""
        if 'wifi' in features:
            wifi_msg = " com Wi-Fi" if features['wifi'] else " sem Wi-Fi"
        
        return f"""✅ **Identificando sua {tipo_msg}{wifi_msg}...**
        
**Próxima pergunta:**
Você vê **tanques de tinta transparentes** na frente ou lateral da impressora?
(São reservatórios que você abastece com garrafinhas de tinta)

💡 Responda: "sim vejo" ou "não, usa cartucho"""
    
    # Pergunta sobre cores
    elif stage == "ask_color":
        features = st.session_state.funnel_features
        tanque_msg = " com tanque de tinta" if features.get('tanque') else " com cartucho"
        
        return f"""📋 **Quase lá! Já sei que é uma impressora{tanque_msg}.**
        
**Próxima pergunta:**
Sua impressora é **colorida** ou só **preto e branco**?

💡 Responda: "colorida" ou "preto e branco"""
    
    # Pergunta sobre tamanho
    elif stage == "ask_size":
        features = st.session_state.funnel_features
        return """🎯 **Última pergunta!**
        
**Qual o tamanho da sua impressora?**

📏 **Pequena/Compacta** = Cabe facilmente em uma mesa
📐 **Média** = Tamanho padrão de escritório
📦 **Grande** = Robusta, para uso profissional

💡 Responda: "pequena", "média" ou "grande"""
    
    # Tentativa de identificação
    elif stage == "try_identify":
        features = st.session_state.funnel_features
        
        # Tentar sugerir modelos baseado nas características
        sugestoes = identify_possible_models(features)
        
        if sugestoes:
            models_list = "\n".join([f"- **{m}**" for m in sugestoes[:3]])
            return f"""🔍 **Baseado nas características, pode ser um destes modelos:**
            
{models_list}

**Você consegue verificar o modelo exato?**
Procure uma etiqueta com "L" seguido de números (ex: L3150)

💡 Digite o modelo ou diga "não encontro"""
        else:
            return """❓ **Preciso do modelo exato para continuar...**
            
**Por favor, procure o modelo na impressora:**
- Etiqueta na frente, tampa ou atrás
- Começa com "L" + números (ex: L3150)

💡 Quando encontrar, digite aqui!"""
    
    # Checagem visual final
    elif stage == "ask_visual_check":
        return """🔍 **Vamos tentar uma última vez!**
        
**Procure com atenção:**
1. **Na frente** da impressora (abaixo dos botões)
2. **Na tampa superior** (onde abre o scanner)
3. **Atrás** da impressora
4. **Embaixo** (etiqueta com informações)

O modelo sempre começa com **"L"** seguido de 3-4 números.
**Exemplo:** L3150, L375, L4260

💡 Digite o que encontrar ou "não achei"""
    
    # Falha na identificação
    elif stage == "failed":
        st.session_state.funnel_attempt += 1
        attempts = st.session_state.funnel_attempt
        
        if attempts < 2:
            return """⚠️ **Ainda não consegui identificar, mas não desista!**
            
**Outras formas de descobrir o modelo:**
1. **No computador:** Configurações > Impressoras
2. **Na nota fiscal** ou caixa do produto
3. **No manual** da impressora
4. **No app Epson** do celular

Quando descobrir, digite o modelo aqui! 🖨️"""
        else:
            return """❌ **Não consegui identificar sua impressora**
            
Para sua segurança, preciso do modelo exato antes de dar instruções.

**Use a barra lateral →**
Selecione seu modelo no menu dropdown

**Ou digite diretamente:**
"Minha impressora é L3150" (exemplo)

Estou aqui quando souber o modelo! 🖨️"""
    
    # Modelo identificado
    elif stage == "model_identified":
        model = st.session_state.identified_printer
        return f"""✅ **Perfeito! Identifiquei sua {model}!**
        
Agora posso ajudar com qualquer problema ou dúvida sobre sua impressora.

**Como posso ajudar você hoje?** 🖨️"""
    
    # Estado desconhecido
    else:
        return """❓ **Houve um problema no processo...**
        
**Por favor, me diga:**
Qual o modelo da sua impressora Epson?
(Exemplo: L3150, L375, L4260)

💡 Ou selecione na barra lateral →"""

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
st.title("🖨️ Chatbot Epson V2 - Suporte Técnico")
st.markdown("Sistema inteligente de suporte para impressoras Epson")
st.markdown("🆕 **Versão 2.1** - Sistema de afunilamento melhorado")

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
        st.session_state.funnel_features = {}
        st.session_state.funnel_attempt = 0
        st.session_state.stage_attempts = 0
        st.rerun()
    
    # Resetar identificação
    if st.session_state.identified_printer and st.button("🔄 Trocar Impressora", use_container_width=True):
        st.session_state.identified_printer = None
        st.session_state.identification_stage = None
        st.session_state.funnel_features = {}
        st.session_state.funnel_attempt = 0
        st.session_state.stage_attempts = 0
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Versão:** 2.1 (Melhorada)")
    st.markdown("**Status:** ✅ Online")
    st.markdown("**Modo:** Afunilamento Inteligente")
    st.markdown("🆕 **Melhorias:**")
    st.markdown("- Sem loops")
    st.markdown("- Uma pergunta por vez")
    st.markdown("- Análise contextual")

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
                
                # Verificar se foi identificado um modelo
                if analysis_result == "model_identified" or st.session_state.identified_printer:
                    # Modelo foi identificado!
                    if st.session_state.identified_printer:
                        funnel_response = generate_funnel_question(prompt, "model_identified")
                        st.markdown(funnel_response)
                        st.session_state.messages.append({"role": "assistant", "content": funnel_response})
                        st.session_state.identification_stage = None  # Resetar estágio
                    else:
                        # Não deveria chegar aqui, mas por segurança
                        new_stage = "initial"
                        st.session_state.identification_stage = new_stage
                        funnel_response = generate_funnel_question(prompt, new_stage)
                        st.markdown(funnel_response)
                        st.session_state.messages.append({"role": "assistant", "content": funnel_response})
                else:
                    # Determinar próximo estágio baseado na análise
                    if analysis_result:
                        # Entendeu a resposta - avançar para próximo estágio
                        new_stage = analysis_result
                        st.session_state.stage_attempts = 0  # Resetar contador
                        
                        # Atualizar estágio
                        st.session_state.identification_stage = new_stage
                        
                        # Gerar pergunta de afunilamento apropriada
                        funnel_response = generate_funnel_question(prompt, new_stage)
                        st.markdown(funnel_response)
                        
                        # Adicionar resposta ao histórico
                        st.session_state.messages.append({"role": "assistant", "content": funnel_response})
                    else:
                        # Não entendeu a resposta
                        st.session_state.stage_attempts += 1
                        
                        # Se é a primeira vez que não entende, dar dica contextual
                        if st.session_state.stage_attempts == 1:
                            hint_response = generate_contextual_hint(current_stage)
                            if hint_response:
                                st.markdown(hint_response)
                                st.session_state.messages.append({"role": "assistant", "content": hint_response})
                        # Se já tentou várias vezes, sugerir usar a sidebar
                        elif st.session_state.stage_attempts >= 2:
                            fallback_msg = """💡 **Dica: Use a barra lateral!**
                            
Se você souber o modelo, pode selecioná-lo diretamente no menu dropdown →
                            
Ou tente digitar algo como: "Minha impressora é L3150"""
                            st.markdown(fallback_msg)
                            st.session_state.messages.append({"role": "assistant", "content": fallback_msg})
                            st.session_state.stage_attempts = 0  # Resetar para evitar spam
                        # Caso contrário, não responder nada (como solicitado pelo usuário)
