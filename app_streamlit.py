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
if 'collected_features' not in st.session_state:
    st.session_state.collected_features = []

def detect_printer_in_query(query):
    """Detecta se algum modelo de impressora foi mencionado na pergunta"""
    query_lower = query.lower()
    for model in PRINTER_MODELS:
        # Remove "Epson " do modelo para comparação mais flexível
        model_simple = model.replace("Epson ", "").lower()
        # Verificar variações (com/sem espaço, com/sem traço)
        model_variations = [
            model_simple,
            model_simple.replace(" ", ""),
            model_simple.replace("-", ""),
            model_simple.replace("l", "l "),  # L3150 → L 3150
        ]
        for variant in model_variations:
            if variant in query_lower:
                return model
    return None

def infer_model_from_features(features):
    """Tenta inferir o modelo baseado nas características coletadas"""
    if not features:
        return None
    
    features_set = set(features) if isinstance(features, list) else {features}
    
    # Mapear características para possíveis modelos
    model_hints = {
        "Epson L3150": {"wifi", "tanque", "colorida", "multifuncional"},
        "Epson L3250": {"wifi", "tanque", "colorida", "multifuncional", "nova"},
        "Epson L3110": {"tanque", "colorida", "multifuncional", "no_wifi"},
        "Epson L375": {"wifi", "tanque", "colorida", "multifuncional", "antiga"},
        "Epson L396": {"wifi", "tanque", "colorida", "multifuncional"},
        "Epson L4150": {"wifi", "tanque", "colorida", "multifuncional"},
        "Epson L4260": {"wifi", "tanque", "colorida", "multifuncional", "nova"},
        "Epson L5190": {"wifi", "tanque", "colorida", "multifuncional", "fax"},
        "Epson L5290": {"wifi", "tanque", "colorida", "multifuncional", "fax", "nova"},
        "Epson L805": {"wifi", "tanque", "colorida", "simples"},
        "Epson L1300": {"tanque", "colorida", "simples", "grande"},
    }
    
    # Encontrar melhor correspondência
    best_match = None
    best_score = 0
    
    for model, model_features in model_hints.items():
        score = len(features_set.intersection(model_features))
        if score > best_score:
            best_score = score
            best_match = model
    
    # Retornar modelo se tiver pelo menos 2 características em comum
    return best_match if best_score >= 2 else None

def analyze_user_response(prompt, stage):
    """Analisa a resposta do usuário de forma inteligente e flexível"""
    prompt_lower = prompt.lower().strip()
    
    # Remover pontuação comum para melhor matching
    import string
    prompt_clean = prompt_lower.translate(str.maketrans('', '', string.punctuation))
    
    if stage == "initial" or stage is None:
        # Verificar se usuário mencionou tipo multifuncional
        multifuncional_keywords = [
            "multifuncional", "multi funcional", "multi", "3 em 1", "3em1",
            "copia", "copiar", "digitaliza", "digitalizar", "scanner", "scan",
            "xerox", "todas as funções", "completa", "tudo", "faz tudo"
        ]
        
        impressora_simples_keywords = [
            "só imprime", "so imprime", "apenas imprime", "apenas impressora",
            "simples", "basica", "básica", "normal", "comum",
            "não copia", "nao copia", "não digitaliza", "nao digitaliza",
            "impressora apenas", "somente impressora", "somente imprime"
        ]
        
        # Verificar multifuncional
        for keyword in multifuncional_keywords:
            if keyword in prompt_clean:
                return "multifuncional"
        
        # Verificar impressora simples
        for keyword in impressora_simples_keywords:
            if keyword in prompt_clean:
                return "simples"
        
        # Verificar se usuário disse que não sabe
        nao_sei_keywords = [
            "não sei", "nao sei", "não lembro", "nao lembro", "esqueci",
            "não faço ideia", "nao faco ideia", "não tenho certeza", "nao tenho certeza",
            "talvez", "acho que"
        ]
        
        for keyword in nao_sei_keywords:
            if keyword in prompt_clean:
                return "nao_sei"
                
    elif stage in ["type_known", "type_known_multi", "type_known_simple"]:
        # Analisar características mencionadas
        features = {
            "wifi": ["wifi", "wi fi", "wi-fi", "wireless", "sem fio", "rede", "internet", "sim tem", "tem sim", "sim"],
            "no_wifi": ["não tem wifi", "nao tem wifi", "sem wifi", "cabo", "usb", "não", "nao"],
            "tanque": ["tanque", "tanques", "tank", "ecotank", "eco tank", "refil", "bulk", "garrafa", "sim", "tem tanque"],
            "no_tanque": ["cartucho", "cartuchos", "não tem tanque", "nao tem tanque", "sem tanque"],
            "colorida": ["colorida", "colorido", "cores", "color", "cmyk", "cor", "sim colorida"],
            "pb": ["preto e branco", "pretoebranco", "pb", "p&b", "monocromatica", "mono", "só preto", "so preto"],
            "nova": ["nova", "novo", "recente", "2024", "2023", "2022", "ano passado", "mes passado", "1 ano", "2 anos"],
            "antiga": ["antiga", "antigo", "velha", "velho", "2019", "2018", "2017", "anos", "tempo", "3 anos", "4 anos", "5 anos"]
        }
        
        detected_features = []
        for feature, keywords in features.items():
            for keyword in keywords:
                if keyword in prompt_clean:
                    detected_features.append(feature)
                    break
        
        # Se detectou algo, retornar
        if detected_features:
            return detected_features
        
        # Verificar respostas simples sim/não
        sim_keywords = ["sim", "yes", "claro", "tem", "possui", "exato", "isso", "correto", "afirmativo"]
        nao_keywords = ["não", "nao", "no", "negativo", "sem", "não tem", "nao tem"]
        
        for keyword in sim_keywords:
            if keyword in prompt_clean:
                return ["resposta_sim"]
        
        for keyword in nao_keywords:
            if keyword in prompt_clean:
                return ["resposta_nao"]
            
    elif stage in ["features_known", "features_analyzed"]:
        # Verificar tamanho mencionado
        tamanhos = {
            "compacta": ["compacta", "pequena", "pequeno", "mini", "portatil", "portátil"],
            "media": ["media", "média", "medio", "médio", "normal", "padrão", "padrao"],
            "grande": ["grande", "gigante", "robusta", "profissional", "escritorio", "escritório"]
        }
        
        for tamanho, keywords in tamanhos.items():
            for keyword in keywords:
                if keyword in prompt_clean:
                    return tamanho
        
        # Verificar se usuário desistiu
        desistir_keywords = [
            "desisto", "não consigo", "nao consigo", "deixa pra lá", "deixa pra la",
            "esquece", "cancela", "para", "pare", "sair"
        ]
        
        for keyword in desistir_keywords:
            if keyword in prompt_clean:
                return "desistiu"
    
    return None

def generate_funnel_question(query, stage=None, context=None):
    """Gera pergunta de afunilamento para identificar a impressora"""
    if stage is None or stage == "initial":
        return """🔍 **Preciso identificar sua impressora primeiro!**
        
Para fornecer a melhor assistência, preciso saber o modelo exato da sua impressora Epson.

**Por favor, me informe:**
1. Você sabe o modelo da sua impressora? (Ex: L3150, L375, L4260, etc.)
2. Se não souber, me diga: ela **copia e digitaliza** também ou **só imprime**?
   
💡 Dica: Pode responder de forma simples como "é multifuncional" ou "só imprime"."""
    
    elif stage == "type_known_multi":
        return """📋 **Ótimo! Sua impressora é multifuncional!**
        
**Agora me ajude com mais detalhes:**
- Ela tem **Wi-Fi** ou conexão sem fio?
- Você vê **tanques de tinta** na frente ou lateral?
- É **colorida** ou só **preto e branco**?
- É **nova** (últimos 2 anos) ou mais **antiga**?

💡 Responda o que souber, não precisa ser tudo!"""
    
    elif stage == "type_known_simple":
        return """📋 **Ok! Sua impressora é modelo simples (só imprime)!**
        
**Me ajude com mais informações:**
- Ela tem **tanques de tinta** visíveis?
- É **colorida** ou **preto e branco**?
- Qual o **tamanho** dela? (pequena, média, grande)

💡 Qualquer detalhe ajuda!"""
    
    elif stage == "features_analyzed":
        # Resposta baseada nas características detectadas
        if context and isinstance(context, list):
            features_text = "✅ Entendi! Sua impressora tem: " + ", ".join(context)
        else:
            features_text = "✅ Ok, anotei essas informações!"
            
        return f"""{features_text}

🎯 **Última etapa para identificar o modelo:**

Por favor, **procure uma etiqueta** na sua impressora com o modelo.
Normalmente está em um destes lugares:
- **Parte frontal** (próximo aos botões)
- **Tampa superior** (ao abrir)
- **Parte traseira** (próximo às conexões)

O modelo começa com **"L"** seguido de números (Ex: L3150, L375, L4260)

Consegue ver? Se não, me diga o **tamanho aproximado** da impressora."""
    
    elif stage == "nao_sei":
        return """🤔 **Sem problemas! Vamos descobrir juntos!**

**Me responda apenas isto:**
Sua impressora faz **cópia e digitalização** (scanner) além de imprimir?

- Se **SIM** → É multifuncional
- Se **NÃO** → É impressora simples
- **Não sei** → Veja se tem uma tampa em cima que abre (isso é o scanner)

💡 Responda de forma simples!"""
    
    elif stage == "desistiu":
        return """😔 **Entendo sua dificuldade!**

**Última tentativa - Super Simples:**

1. **Olhe sua impressora agora**
2. **Procure qualquer número** que comece com **"L"**
3. **Me diga esse número**

Exemplos: L3150, L375, L805, L4260...

Se realmente não conseguir, recomendo:
- Verificar a nota fiscal
- Olhar o manual
- Pedir ajuda para alguém próximo

Estou aqui quando conseguir a informação! 🖨️"""
    
    else:
        return """❌ **Não consigo prosseguir sem identificar sua impressora**
        
Para sua segurança, preciso saber o modelo exato antes de dar instruções técnicas.

**O que fazer:**
1. Procure o modelo na própria impressora
2. Verifique nota fiscal ou caixa
3. Olhe nas configurações do computador

Quando souber o modelo, volte que eu ajudo! 🖨️"""

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
        st.session_state.collected_features = []
        st.rerun()
    
    # Resetar identificação
    if st.session_state.identified_printer and st.button("🔄 Trocar Impressora", use_container_width=True):
        st.session_state.identified_printer = None
        st.session_state.identification_stage = None
        st.session_state.collected_features = []
        st.rerun()
    
    # Mostrar features coletadas (para debug)
    if st.session_state.collected_features and not st.session_state.identified_printer:
        st.caption(f"📊 Características: {', '.join(st.session_state.collected_features)}")
    
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
                # Analisar resposta do usuário de forma inteligente
                current_stage = st.session_state.identification_stage
                analysis = analyze_user_response(prompt, current_stage)
                
                # Processar análise e atualizar estágio
                new_stage = current_stage
                context = None
                
                if current_stage in ["initial", None]:
                    if analysis == "multifuncional":
                        new_stage = "type_known_multi"
                        st.session_state.collected_features.append("multifuncional")
                    elif analysis == "simples":
                        new_stage = "type_known_simple"
                        st.session_state.collected_features.append("simples")
                    elif analysis == "nao_sei":
                        new_stage = "nao_sei"
                    else:
                        # Manter no estágio inicial se não entendeu
                        new_stage = "initial"
                
                elif current_stage == "nao_sei":
                    # Segunda tentativa após usuário dizer que não sabe
                    if analysis == "multifuncional":
                        new_stage = "type_known_multi"
                        st.session_state.collected_features.append("multifuncional")
                    elif analysis == "simples":
                        new_stage = "type_known_simple"
                        st.session_state.collected_features.append("simples")
                    else:
                        new_stage = "initial"  # Voltar ao início
                
                elif current_stage in ["type_known_multi", "type_known_simple", "type_known"]:
                    if isinstance(analysis, list) and analysis:
                        # Adicionar características coletadas
                        for feature in analysis:
                            if feature not in ["resposta_sim", "resposta_nao"] and feature not in st.session_state.collected_features:
                                st.session_state.collected_features.append(feature)
                        
                        # Tentar inferir modelo com características coletadas
                        inferred_model = infer_model_from_features(st.session_state.collected_features)
                        
                        if inferred_model:
                            # Modelo identificado por inferência!
                            st.session_state.identified_printer = inferred_model
                            st.session_state.identification_stage = None
                            
                            success_msg = f"""✅ **Modelo identificado: {inferred_model}!**
                            
Baseado nas características que você mencionou, identifiquei sua impressora!

Agora posso fornecer suporte específico para o modelo {inferred_model}.

**Faça sua pergunta sobre a {inferred_model}!**"""
                            st.markdown(success_msg)
                            st.session_state.messages.append({"role": "assistant", "content": success_msg})
                            return  # Sair para não continuar o afunilamento
                        else:
                            # Continuar coletando mais informações
                            new_stage = "features_analyzed"
                            context = analysis
                    else:
                        # Não detectou nada útil, perguntar mais detalhes
                        if len(st.session_state.collected_features) >= 3:
                            # Já coletou bastante, pedir para verificar fisicamente
                            new_stage = "features_analyzed"
                        else:
                            # Continuar perguntando
                            new_stage = current_stage
                
                elif current_stage == "features_analyzed":
                    if analysis == "desistiu":
                        new_stage = "desistiu"
                    elif analysis in ["compacta", "media", "grande"]:
                        # Adicionar tamanho às características
                        st.session_state.collected_features.append(analysis)
                        
                        # Tentar inferir modelo novamente
                        inferred_model = infer_model_from_features(st.session_state.collected_features)
                        if inferred_model:
                            st.session_state.identified_printer = inferred_model
                            st.session_state.identification_stage = None
                            success_msg = f"✅ **Modelo provável: {inferred_model}!** Posso ajudar com sua {inferred_model}?"
                            st.markdown(success_msg)
                            st.session_state.messages.append({"role": "assistant", "content": success_msg})
                            return
                        else:
                            new_stage = "failed"
                    else:
                        # Verificar se não digitou um modelo
                        possible_model = detect_printer_in_query(prompt)
                        if possible_model:
                            st.session_state.identified_printer = possible_model
                            st.session_state.identification_stage = None
                            success_msg = f"✅ **Perfeito! Modelo {possible_model} identificado!**"
                            st.markdown(success_msg)
                            st.session_state.messages.append({"role": "assistant", "content": success_msg})
                            return
                        else:
                            new_stage = "failed"
                
                elif current_stage == "desistiu":
                    # Última chance - verificar se digitou modelo
                    possible_model = detect_printer_in_query(prompt)
                    if possible_model:
                        st.session_state.identified_printer = possible_model
                        st.session_state.identification_stage = None
                        success_msg = f"✅ **Ótimo! Modelo {possible_model} identificado!**"
                        st.markdown(success_msg)
                        st.session_state.messages.append({"role": "assistant", "content": success_msg})
                        return
                    else:
                        new_stage = "failed"
                
                # Atualizar estágio
                st.session_state.identification_stage = new_stage
                
                # Gerar pergunta de afunilamento apropriada
                funnel_response = generate_funnel_question(prompt, new_stage, context)
                st.markdown(funnel_response)
                
                # Adicionar resposta ao histórico
                st.session_state.messages.append({"role": "assistant", "content": funnel_response})
