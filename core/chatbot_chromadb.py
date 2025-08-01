#!/usr/bin/env python3
"""
Chatbot Epson com ChromaDB - Versão com busca semântica avançada
Baseado no chatbot.py original mas usando ChromaDB para busca semântica

NOVIDADES:
- Busca semântica com modelo E5 Base
- Fallback automático para sistema JSON se ChromaDB não disponível
- Compatibilidade total com sistema anterior
- Melhoria significativa na qualidade das respostas
"""

import json
import time
import re
import unicodedata
import os
import sys
from collections import Counter
from difflib import SequenceMatcher
import google.generativeai as genai

# Adiciona path para importar ChromaDB integration
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Configurações da API
genai.configure(api_key='AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk')
model = genai.GenerativeModel('gemini-1.5-flash')

# Controle otimizado para respostas mais longas
last_request_time = 0
MIN_REQUEST_INTERVAL = 4
request_times = []
MAX_REQUESTS_PER_MINUTE = 8

knowledge_base = []

# Base de dados de metadados das impressoras (mantida do original)
PRINTER_METADATA = {
    'impressoraL3110': {
        'full_name': 'Epson L3110',
        'aliases': ['l3110', '3110', 'l 3110', 'epson l3110', 'epson 3110'],
        'type': 'colorida',
        'features': ['multifuncional', 'wifi', 'ecotank', 'tanque'],
        'series': 'L3000',
        'description': 'Multifuncional colorida com sistema EcoTank'
    },
    'impressoraL3150': {
        'full_name': 'Epson L3150',
        'aliases': ['l3150', '3150', 'l 3150', 'epson l3150', 'epson 3150'],
        'type': 'colorida',
        'features': ['multifuncional', 'wifi', 'ecotank', 'tanque'],
        'series': 'L3000',
        'description': 'Multifuncional colorida com sistema EcoTank'
    },
    'impressoraL3250_L3251': {
        'full_name': 'Epson L3250/L3251',
        'aliases': ['l3250', 'l3251', '3250', '3251', 'l 3250', 'l 3251', 'epson l3250', 'epson l3251', 'epson 3250', 'epson 3251'],
        'type': 'colorida',
        'features': ['multifuncional', 'wifi', 'ecotank', 'tanque', 'duplex'],
        'series': 'L3000',
        'description': 'Multifuncional colorida com sistema EcoTank e impressão duplex'
    },
    'impressoraL375': {
        'full_name': 'Epson L375',
        'aliases': ['l375', '375', 'l 375', 'epson l375', 'epson 375'],
        'type': 'colorida',
        'features': ['multifuncional', 'wifi', 'ecotank', 'tanque'],
        'series': 'L300',
        'description': 'Multifuncional colorida com sistema EcoTank'
    },
    'impressoraL4150': {
        'full_name': 'Epson L4150',
        'aliases': ['l4150', '4150', 'l 4150', 'epson l4150', 'epson 4150'],
        'type': 'colorida',
        'features': ['multifuncional', 'wifi', 'ecotank', 'tanque', 'duplex'],
        'series': 'L4000',
        'description': 'Multifuncional colorida com sistema EcoTank e impressão duplex'
    },
    'impressoraL4260': {
        'full_name': 'Epson L4260',
        'aliases': ['l4260', '4260', 'l 4260', 'epson l4260', 'epson 4260'],
        'type': 'colorida',
        'features': ['multifuncional', 'wifi', 'ecotank', 'tanque', 'fax'],
        'series': 'L4000',
        'description': 'Multifuncional colorida com sistema EcoTank e fax'
    },
    'impressoral5190': {
        'full_name': 'Epson L5190',
        'aliases': ['l5190', '5190', 'l 5190', 'epson l5190', 'epson 5190'],
        'type': 'colorida',
        'features': ['multifuncional', 'wifi', 'ecotank', 'tanque', 'duplex', 'fax'],
        'series': 'L5000',
        'description': 'Multifuncional colorida com sistema EcoTank, duplex e fax'
    },
    'impressoral6490': {
        'full_name': 'Epson L6490',
        'aliases': ['l6490', '6490', 'l 6490', 'epson l6490', 'epson 6490'],
        'type': 'colorida',
        'features': ['multifuncional', 'wifi', 'ecotank', 'tanque', 'duplex', 'fax', 'a3'],
        'series': 'L6000',
        'description': 'Multifuncional colorida A3 com sistema EcoTank, duplex e fax'
    },
    'impressoraL1300': {
        'full_name': 'Epson L1300',
        'aliases': ['l1300', '1300', 'l 1300', 'epson l1300', 'epson 1300'],
        'type': 'colorida',
        'features': ['tanque', 'a3'],
        'series': 'L1000',
        'description': 'Impressora colorida A3 com sistema de tanque'
    }
}

# Sistema ChromaDB
chromadb_search = None
using_chromadb = False

def init_chromadb():
    """Initializa ChromaDB se disponível"""
    global chromadb_search, using_chromadb
    
    try:
        from chromadb_integration_example import ChromaDBSearch
        chromadb_search = ChromaDBSearch()
        using_chromadb = True
        print("🤖 ChromaDB carregado - usando busca semântica avançada!")
        return True
    except Exception as e:
        print(f"⚠️  ChromaDB não disponível: {e}")
        print("💡 Usando sistema JSON como fallback")
        using_chromadb = False
        return False

def expand_ink_query(query):
    """Expande consultas sobre tinta para melhorar busca semântica"""
    query_lower = query.lower()
    
    # Mapeia termos relacionados à tinta
    ink_synonyms = {
        'trocar': ['recarregar', 'reabastecer', 'adicionar', 'inserir'],
        'tinta': ['tinta', 'cartucho', 'refil', 'suprimento'],
        'acabou': ['vazio', 'baixo', 'insuficiente', 'esgotado']
    }
    
    # Se a consulta é sobre tinta, adiciona sinônimos importantes
    if any(word in query_lower for word in ['tinta', 'cartucho', 'trocar', 'recarregar']):
        expanded_terms = []
        
        # Adiciona termos principais
        if 'trocar' in query_lower or 'troca' in query_lower:
            expanded_terms.extend(['recarregar', 'reabastecer'])
        if 'tinta' in query_lower:
            expanded_terms.extend(['garrafas de tinta', 'tanque de tinta'])
            
        if expanded_terms:
            return f"{query} {' '.join(expanded_terms)}"
    
    return query

def enhanced_search_hybrid(query, filtered_knowledge_base=None, printer_model=None):
    """
    Busca híbrida que usa ChromaDB se disponível, senão usa sistema JSON original
    
    Retorna formato compatível com sistema anterior: lista de tuplas (documento, score)
    """
    
    # Tenta usar ChromaDB primeiro
    if using_chromadb and chromadb_search:
        try:
            print("🔍 Usando busca semântica ChromaDB...")
            
            # Expande consulta para melhorar busca de tinta
            expanded_query = expand_ink_query(query)
            if expanded_query != query:
                print(f"🔍 Expandindo busca: '{expanded_query}'")
            
            results = chromadb_search.semantic_search(
                query=expanded_query, 
                printer_model=printer_model,
                n_results=15,  # Mais resultados
                min_similarity=0.2  # Mais permissivo ainda
            )
            
            if results:
                print(f"✅ ChromaDB encontrou {len(results)} resultados relevantes")
                return results
            else:
                print("⚠️  ChromaDB não encontrou resultados, usando fallback JSON...")
        
        except Exception as e:
            print(f"⚠️  Erro no ChromaDB: {e}")
            print("🔄 Usando sistema JSON como fallback...")
    
    # Fallback para sistema JSON original
    if filtered_knowledge_base:
        print("🔍 Usando busca textual JSON...")
        return enhanced_search_original(query, filtered_knowledge_base)
    
    return None

# FUNÇÕES ORIGINAIS DO CHATBOT (mantidas para compatibilidade e fallback)

def normalize_text(text):
    """Normaliza texto removendo acentos, maiúsculas e caracteres especiais"""
    if not text:
        return ""
    
    # Remove acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    
    # Converte para minúsculas
    text = text.lower()
    
    # Remove caracteres especiais, mantém apenas letras, números e espaços
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # Remove espaços múltiplos
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def get_word_variations(word):
    """Gera variações de uma palavra incluindo plural, singular, conjugações básicas"""
    if len(word) < 3:
        return [word]
    
    variations = [word]
    
    # Variações básicas de plural/singular
    if word.endswith('s') and len(word) > 3:
        variations.append(word[:-1])  # Remove 's' final
    else:
        variations.append(word + 's')  # Adiciona 's'
    
    # Variações com 'ç' e 'c'
    if 'ç' in word:
        variations.append(word.replace('ç', 'c'))
    if 'c' in word:
        variations.append(word.replace('c', 'ç'))
    
    # Variações verbais básicas
    if word.endswith('ar'):
        base = word[:-2]
        variations.extend([base + 'a', base + 'ado', base + 'ando'])
    elif word.endswith('er'):
        base = word[:-2]
        variations.extend([base + 'e', base + 'ido', base + 'endo'])
    elif word.endswith('ir'):
        base = word[:-2]
        variations.extend([base + 'e', base + 'ido', base + 'indo'])
    
    # Variações com sufixos comuns
    if word.endswith('cao'):
        base = word[:-3]
        variations.extend([base + 'ção', base + 'cao'])
    
    return list(set(variations))  # Remove duplicatas

def enhanced_search_original(query, filtered_knowledge_base=None):
    """Busca original do sistema JSON (mantida como fallback)"""
    if filtered_knowledge_base is None:
        filtered_knowledge_base = knowledge_base
    
    if not filtered_knowledge_base:
        return None
    
    query_normalized = normalize_text(query)
    query_cleaned = re.sub(r'[^\w\s]', ' ', query_normalized)
    query_words = [w for w in query_cleaned.split() if len(w) > 2]
    
    # Gera todas as variações das palavras da busca
    all_variations = []
    for word in query_words:
        all_variations.extend(get_word_variations(word))
    all_variations = list(set(all_variations))
    
    matches = []
    
    for section in filtered_knowledge_base:
        score = 0
        section_title_normalized = normalize_text(section['title'])
        section_content_normalized = normalize_text(section['content'])
        section_combined = f"{section_title_normalized} {section_content_normalized}"
        
        # Busca por variações das palavras
        for variation in all_variations:
            if variation in section_combined:
                # Peso maior para palavras no título
                title_matches = section_title_normalized.count(variation)
                content_matches = section_content_normalized.count(variation)
                
                score += title_matches * 15  # Título tem peso maior
                score += content_matches * 10
        
        # Busca por sequências de palavras (frases)
        if len(query_words) > 1:
            query_phrase = ' '.join(query_words)
            if query_phrase in section_combined:
                score += 25
        
        # Busca por palavras originais (sem variações)
        for word in query_words:
            if word in section_combined:
                score += 12
        
        # Bonus para seções com keywords relevantes
        section_keywords = section.get('keywords', [])
        if section_keywords:
            for keyword in section_keywords:
                keyword_normalized = normalize_text(keyword)
                for word in query_words:
                    if word in keyword_normalized or keyword_normalized in word:
                        score += 8
        
        if score > 0:
            matches.append((section, score))
    
    # Ordena por score decrescente
    matches.sort(key=lambda x: x[1], reverse=True)
    
    return matches[:15] if matches else None

# DEMAIS FUNÇÕES ORIGINAIS (copiadas do chatbot.py original)

def can_make_request():
    """Controla rate limiting da API"""
    global last_request_time, request_times
    
    current_time = time.time()
    
    # Remove requisições antigas (mais de 1 minuto)
    request_times = [t for t in request_times if current_time - t < 60]
    
    # Verifica limite de requisições por minuto
    if len(request_times) >= MAX_REQUESTS_PER_MINUTE:
        wait_time = 60 - (current_time - request_times[0])
        return False, f"⏳ Limite de requisições atingido. Aguarde {wait_time:.0f}s"
    
    # Verifica intervalo mínimo entre requisições
    if current_time - last_request_time < MIN_REQUEST_INTERVAL:
        wait_time = MIN_REQUEST_INTERVAL - (current_time - last_request_time)
        return False, f"⏳ Aguarde {wait_time:.1f}s antes da próxima pergunta"
    
    return True, "OK"

def check_question_relevance(query):
    """Verifica se a pergunta é relevante para impressoras"""
    try:
        relevant_keywords = [
            'impressora', 'imprimir', 'papel', 'tinta', 'cartucho', 'scanner', 'wifi',
            'configurar', 'instalar', 'problema', 'erro', 'qualidade', 'xerox', 'copia',
            'ecotank', 'tanque', 'refil', 'original', 'compativel', 'driver', 'software',
            'limpar', 'manutencao', 'calibrar', 'alinhar', 'obstrucao', 'emperrou',
            'conectar', 'rede', 'usb', 'wireless', 'bluetooth', 'duplex', 'frente', 'verso',
            'epson', 'l3110', 'l3150', 'l3250', 'l375', 'l4150', 'l4260', 'l5190', 'l6490', 'l1300'
        ]
        
        query_lower = normalize_text(query)
        
        # Verifica se contém pelo menos uma palavra relevante
        for keyword in relevant_keywords:
            if keyword in query_lower:
                return True
        
        # Se não encontrou keywords relevantes, considera irrelevante
        return False
        
    except Exception as e:
        print(f"Erro na verificação de relevância: {e}")
        return True  # Em caso de erro, assume que é relevante para não bloquear

def reload_knowledge_base_if_updated():
    """Recarrega a base de conhecimento se detectar que foi atualizada"""
    global knowledge_base
    
    try:
        is_updated, status = check_and_reload_manual()
        
        if is_updated:
            print("\n🔄 Detectada atualização na base de conhecimento!")
            print("   Recarregando manual...")
            
            manual_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'manual_complete.json')
            with open(manual_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            old_count = len(knowledge_base)
            knowledge_base = data['sections']
            new_count = len(knowledge_base)
            
            print(f"   ✅ Base atualizada: {old_count} → {new_count} seções")
            
            available_models = get_available_printer_models(knowledge_base)
            print(f"   📱 Modelos disponíveis: {len(available_models)}")
            
            return True, "Base de conhecimento atualizada com sucesso"
        
        return False, status
        
    except Exception as e:
        return False, f"Erro ao recarregar base: {e}"

def check_and_reload_manual():
    """Verifica se o manual foi atualizado recentemente"""
    try:
        webhook_activity_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'webhook_activity.json')
        manual_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'manual_complete.json')
        
        if not os.path.exists(webhook_activity_path) or not os.path.exists(manual_path):
            return False, "Arquivos de verificação não encontrados"
        
        # Verifica timestamp do webhook
        with open(webhook_activity_path, 'r', encoding='utf-8') as f:
            webhook_data = json.load(f)
        
        activities = webhook_data.get('activities', [])
        if not activities:
            return False, "Nenhuma atividade de webhook encontrada"
        
        last_activity = activities[-1] if isinstance(activities, list) else activities
        last_update_time = last_activity.get('timestamp', '') if isinstance(last_activity, dict) else ''
        
        # Verifica timestamp do manual
        manual_stat = os.path.getmtime(manual_path)
        manual_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(manual_stat))
        
        # Se o webhook é mais recente que o manual atual, precisa atualizar
        if last_update_time > manual_time:
            return True, f"Atualização disponível (webhook: {last_update_time})"
        
        return False, "Manual está atualizado"
        
    except Exception as e:
        return False, f"Erro ao verificar atualizações: {e}"

def check_webhook_status():
    """Verifica status do webhook"""
    try:
        webhook_channels_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'webhook_channels.json')
        
        if not os.path.exists(webhook_channels_path):
            return False, "Webhook não configurado"
        
        with open(webhook_channels_path, 'r', encoding='utf-8') as f:
            channels_data = json.load(f)
        
        channels = channels_data.get('channels', [])
        if not channels:
            return False, "Nenhum canal de webhook ativo"
        
        active_channels = [ch for ch in channels if isinstance(ch, dict) and ch.get('status') == 'active']
        
        if not active_channels:
            return False, "Nenhum canal ativo"
        
        return True, f"Webhook ativo ({len(active_channels)} canal(is))"
        
    except Exception as e:
        return False, f"Erro ao verificar webhook: {e}"

def load_complete_manual():
    """Carrega manual completo processado"""
    try:
        # Primeiro, verifica se há atualizações recentes
        print("🔍 Verificando atualizações recentes...")
        is_updated, update_status = check_and_reload_manual()
        print(f"   {update_status}")
        
        manual_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'manual_complete.json')
        with open(manual_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Manual carregado: {data['manual_info']['source']}")
        print(f"Seções: {data['manual_info']['total_sections']}")
        print(f"Processado em: {data['manual_info']['processed_at']}")
        
        # Check webhook status
        webhook_active, webhook_status = check_webhook_status()
        print(f"Status do webhook: {webhook_status}")
        
        return data['sections']
    
    except FileNotFoundError:
        print("Arquivo manual_complete.json não encontrado")
        print("Execute: python3 core/extract_pdf_complete.py")
        return None
    except Exception as e:
        print(f"Erro ao carregar manual: {e}")
        return None

def get_available_printer_models(knowledge_base):
    """Obtém lista de modelos disponíveis na base de conhecimento"""
    if not knowledge_base:
        return []
    
    models = set()
    for section in knowledge_base:
        if section.get('printer_model'):
            models.add(section['printer_model'])
    
    return sorted(list(models))

def smart_printer_detection(query, available_models):
    """Sistema inteligente de detecção de impressora"""
    
    # Normaliza query
    query_normalized = normalize_text(query)
    
    # Primeiro: busca direta por modelos mencionados na query
    detected_models = []
    
    for model in available_models:
        model_normalized = normalize_text(model)
        model_clean = model_normalized.replace('impressora', '').strip()
        
        if model_clean in query_normalized or model_normalized in query_normalized:
            detected_models.append(model)
            continue
        
        # Verifica aliases
        if model in PRINTER_METADATA:
            for alias in PRINTER_METADATA[model]['aliases']:
                if normalize_text(alias) in query_normalized:
                    detected_models.append(model)
                    break
    
    # Se encontrou modelo específico, usa ele
    if len(detected_models) == 1:
        print(f"🎯 Modelo detectado automaticamente: {detected_models[0]}")
        return detected_models[0]
    
    # Se encontrou múltiplos modelos, pede para escolher
    if len(detected_models) > 1:
        print(f"\n🔍 Múltiplos modelos detectados na sua pergunta:")
        for i, model in enumerate(detected_models, 1):
            full_name = PRINTER_METADATA.get(model, {}).get('full_name', model)
            print(f"   {i}. {full_name}")
        
        while True:
            try:
                choice = input(f"\nEscolha o modelo (1-{len(detected_models)}): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(detected_models):
                    selected_model = detected_models[int(choice) - 1]
                    print(f"✅ Modelo selecionado: {selected_model}")
                    return selected_model
                else:
                    print("Opção inválida. Tente novamente.")
            except KeyboardInterrupt:
                return None
    
    # Se não detectou modelo específico, mostra menu de seleção
    print(f"\n📱 Modelos disponíveis ({len(available_models)}):")
    print("="*50)
    
    for i, model in enumerate(available_models, 1):
        full_name = PRINTER_METADATA.get(model, {}).get('full_name', model)
        model_type = PRINTER_METADATA.get(model, {}).get('type', 'N/A')
        features = PRINTER_METADATA.get(model, {}).get('features', [])
        features_str = ', '.join(features[:3]) if features else 'N/A'
        
        print(f"{i:2d}. {full_name}")
        print(f"    Tipo: {model_type} | Recursos: {features_str}")
        print()
    
    print("0. Sair")
    print("="*50)
    
    while True:
        try:
            choice = input(f"Escolha seu modelo (0-{len(available_models)}): ").strip()
            
            if choice == '0':
                print("Encerrando...")
                return None
            
            if choice.isdigit() and 1 <= int(choice) <= len(available_models):
                selected_model = available_models[int(choice) - 1]
                full_name = PRINTER_METADATA.get(selected_model, {}).get('full_name', selected_model)
                print(f"\n✅ Modelo selecionado: {full_name}")
                return selected_model
            else:
                print("Opção inválida. Tente novamente.")
                
        except KeyboardInterrupt:
            print("\nEncerrando...")
            return None

def call_api_detailed(query, manual_sections, mode='detalhado', printer_model=None):
    """Chama API do Gemini com contexto dos manuais"""
    global last_request_time, request_times
    
    try:
        # Prepara contexto dos manuais
        context_parts = []
        for section, score in manual_sections[:5]:  # Usa top 5 seções
            context_parts.append(f"SEÇÃO (Score: {score}):\nTÍTULO: {section['title']}\nCONTEÚDO: {section['content'][:1000]}...")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Determina sistema de instruções baseado no modo
        if mode == 'rapido':
            system_prompt = f"""Você é um especialista técnico em impressoras EPSON, com profundo conhecimento de toda a linha EcoTank. Forneça uma resposta CONCISA e DIRETA.

INSTRUÇÕES PARA MODO RÁPIDO:
- Adapte a resposta especificamente para o modelo {printer_model} identificado
- Considere as características específicas deste modelo (ex: se tem duplex, wifi, etc)
- Responda de forma BREVE e PRÁTICA em 3-4 passos
- Use linguagem simples e direta
- Foque nas particularidades do modelo em questão
- Evite informações genéricas que não se aplicam ao modelo
- IMPORTANTE: Use APENAS o modelo identificado ({printer_model}). NÃO mencione outros modelos de impressora
- NÃO invente ou cite modelos que não foram especificamente identificados
CONTEXTO DO MANUAL:
{context}"""
        else:
            system_prompt = f"""Você é um assistente técnico especializado em impressoras Epson.

IMPORTANTE: Forneça uma resposta COMPLETA e DETALHADA.

Baseie sua resposta nas seções do manual fornecidas abaixo. Se a informação não estiver no manual, diga que não encontrou a informação específica.

Modelo da impressora: {printer_model or 'Não especificado'}

Formato de resposta DETALHADA:
- Explicação do problema/situação
- Passos detalhados com explicações
- Dicas adicionais quando relevante
- Avisos importantes se aplicável
- Mantenha o formato de passo a passo, com dicas e explicações do por que de cada passo.

CONTEXTO DO MANUAL:
{context}"""
        
        # Registra tempo da requisição
        current_time = time.time()
        last_request_time = current_time
        request_times.append(current_time)
        
        # Combina system prompt com query do usuário (Gemini não suporta role system)
        combined_prompt = f"{system_prompt}\n\nPERGUNTA DO USUÁRIO: {query}"
        
        # Chama API
        response = model.generate_content(
            combined_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1500 if mode == 'rapido' else 2500,
                temperature=0.1,
            )
        )
        
        if response and response.text:
            return True, response.text
        else:
            return False, "❌ Erro: Não foi possível gerar resposta"
            
    except Exception as e:
        return False, f"❌ Erro na API: {e}"

def format_response(response_text):
    """Formata resposta para melhor legibilidade"""
    
    # Adiciona quebras de linha após pontos finais seguidos de número
    response_text = re.sub(r'(\.)(\s*)(\d+\.)', r'\1\n\n\3', response_text)
    
    # Melhora formatação de listas numeradas
    response_text = re.sub(r'^(\d+\.)', r'\n\1', response_text, flags=re.MULTILINE)
    
    # Melhora formatação de bullets
    response_text = re.sub(r'^(-|\*)', r'\n\1', response_text, flags=re.MULTILINE)
    
    # Remove múltiplas quebras de linha consecutivas
    response_text = re.sub(r'\n{3,}', '\n\n', response_text)
    
    return response_text.strip()

def show_search_details(manual_sections):
    """Mostra detalhes das seções encontradas"""
    if not manual_sections:
        return
    
    print(f"\n📋 SEÇÕES ENCONTRADAS ({len(manual_sections)}):")
    print("-" * 60)
    
    for i, (section, score) in enumerate(manual_sections[:5], 1):
        title = section['title'][:80] + "..." if len(section['title']) > 80 else section['title']
        print(f"{i}. Score: {score:3d} | {title}")
    
    if len(manual_sections) > 5:
        avg_score = sum(score for _, score in manual_sections[5:]) / len(manual_sections[5:])
        print(f"   ... e mais {len(manual_sections)-5} seções (score médio: {avg_score:.0f})")
    print()

def main():
    """Função principal com dois modos de resposta"""
    global knowledge_base
    
    print("Carregando base de manuais Epson...")
    
    # Inicializa ChromaDB
    print("🔄 Inicializando sistema de busca...")
    init_chromadb()
    
    # Carrega base JSON (sempre necessária para compatibilidade)
    knowledge_base = load_complete_manual()
    if not knowledge_base:
        print("Erro: Manual não encontrado")
        return
    
    available_models = get_available_printer_models(knowledge_base)
    
    # Header do sistema
    system_type = "ChromaDB + JSON" if using_chromadb else "JSON"
    print(f"\n🤖 CHATBOT EPSON - {system_type}")
    print(f"Manual carregado: {len(knowledge_base)} seções indexadas")
    
    if using_chromadb:
        print("✨ Busca semântica ativada - qualidade superior!")
    else:
        print("📝 Busca textual tradicional")
    
    # Seleção do modo inicial
    print("\nEscolha o modo de resposta:")
    print("1. Modo RÁPIDO - Respostas concisas (3-4 passos)")
    print("2. Modo DETALHADO - Respostas completas (explicações)")
    
    while True:
        modo_escolha = input("Escolha o modo (1 ou 2): ").strip()
        if modo_escolha == '1':
            modo_atual = 'rapido'
            print("Modo RÁPIDO selecionado")
            break
        elif modo_escolha == '2':
            modo_atual = 'detalhado'
            print("Modo DETALHADO selecionado")
            break
        else:
            print("Digite 1 para rápido ou 2 para detalhado")
    
    print("\nComandos especiais:")
    print("• 'modo rapido' - Alterna para respostas rápidas")
    print("• 'modo detalhado' - Alterna para respostas completas") 
    print("• 'reload' - Verifica e recarrega a base de conhecimento")
    print("• 'sair' - Encerra o programa")
    print("="*60)
    
    question_count = 0
    
    while True:
        try:
            # Verifica atualizações a cada 5 perguntas
            if question_count > 0 and question_count % 5 == 0:
                print("\n🔍 Verificando atualizações automáticas...")
                reload_success, reload_msg = reload_knowledge_base_if_updated()
                if reload_success:
                    available_models = get_available_printer_models(knowledge_base)
            
            query = input("\nSua pergunta: ").strip()
            
            if query.lower() in ['sair', 'exit', 'quit']:
                print("\nAté logo!")
                break
            elif query.lower() == 'modo rapido':
                modo_atual = 'rapido'
                print("Alterado para modo RÁPIDO")
                continue
            elif query.lower() == 'modo detalhado':
                modo_atual = 'detalhado'
                print("Alterado para modo DETALHADO")
                continue
            elif query.lower() == 'reload':
                print("🔄 Verificando atualizações manuais...")
                reload_success, reload_msg = reload_knowledge_base_if_updated()
                print(f"   {reload_msg}")
                if reload_success:
                    available_models = get_available_printer_models(knowledge_base)
                continue
            
            if not query or len(query) < 3:
                print("Digite uma pergunta mais específica")
                continue
            
            # Sistema inteligente de detecção de impressora
            printer_model = smart_printer_detection(query, available_models)
            if not printer_model:
                break
            
            # Busca híbrida (ChromaDB ou JSON)
            print(f"Buscando no manual do modelo {printer_model}...")
            
            # Para ChromaDB, não precisa filtrar beforehand
            if using_chromadb:
                manual_sections = enhanced_search_hybrid(query, None, printer_model)
            else:
                # Para JSON, filtra primeiro
                filtered_knowledge_base = [s for s in knowledge_base if s.get('printer_model') == printer_model]
                if not filtered_knowledge_base:
                    print(f"❌ Não há informações para o modelo '{printer_model}'.")
                    continue
                manual_sections = enhanced_search_hybrid(query, filtered_knowledge_base, printer_model)
            
            # Rate limiting
            can_req, msg = can_make_request()
            if not can_req:
                print(f"{msg}")
                continue
            
            # Verifica relevância baseada na busca
            if manual_sections:
                # Ajuste de threshold: ChromaDB usa similaridade 0-1, scores 50+ são bons
                high_score_sections = [section for section in manual_sections if section[1] >= 50]
                if high_score_sections:
                    print(f"Encontrado {len(manual_sections)} seção(ões) relevante(s)!")
                    show_search_details(manual_sections)
                    modo_texto = "RÁPIDA" if modo_atual == 'rapido' else "DETALHADA"
                    search_method = "semântica" if using_chromadb else "textual"
                    print(f"Gerando resposta {modo_texto} (busca {search_method})...")
                    success, response = call_api_detailed(query, manual_sections, modo_atual, printer_model)
                    if success:
                        print(f"\nRESPOSTA {modo_texto}:")
                        print("="*50)
                        formatted_response = format_response(response)
                        print(formatted_response)
                        print(f"\nFontes: {len(manual_sections)} seção(ões) do manual oficial")
                    else:
                        print(response)
                else:
                    print("Analisando relevância da pergunta...")
                    if check_question_relevance(query):
                        print("Gerando resposta com informações disponíveis...")
                        success, response = call_api_detailed(query, manual_sections[:3], modo_atual, printer_model)
                        if success:
                            modo_texto = "RÁPIDA" if modo_atual == 'rapido' else "DETALHADA"
                            print(f"\nRESPOSTA {modo_texto}:")
                            print("="*50)
                            formatted_response = format_response(response)
                            print(formatted_response)
                            print(f"\nFontes: Informações limitadas encontradas")
                        else:
                            print(response)
                    else:
                        print("❌ Pergunta não relacionada a impressoras. Tente perguntar sobre:")
                        print("   • Problemas de impressão")
                        print("   • Configurações")
                        print("   • Manutenção")
                        print("   • Instalação")
            else:
                print("❌ Não foram encontradas informações relevantes no manual.")
                print("💡 Tente reformular sua pergunta ou use termos mais específicos.")
            
            question_count += 1
            
        except KeyboardInterrupt:
            print("\n\nEncerrando...")
            break
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            print("Continuando...")

if __name__ == "__main__":
    main()