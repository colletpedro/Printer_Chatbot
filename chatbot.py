#!/usr/bin/env python3
"""
ChatBot Explicativo - RAG com Manual Completo de 232 páginas
Respostas detalhadas e explicativas baseadas no manual completo
"""

import requests
import json
import time
import re
import unicodedata

# Configurações da API
API_KEY = 'AIzaSyAsVV0aUR-xz7reTOk-rFTdCQ-x3Z5NQuI'
API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'

# Controle otimizado para respostas mais longas
last_request_time = 0
MIN_REQUEST_INTERVAL = 4  # Aumentado para respostas mais longas
request_times = []
MAX_REQUESTS_PER_MINUTE = 8  # Reduzido para dar mais espaço

knowledge_base = []

def normalize_text(text):
    """Normaliza texto removendo acentos e convertendo para minúsculas"""
    if not text:
        return ""
    # Remove acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower()

def get_word_variations(word):
    """Gera variações de uma palavra para busca mais inteligente"""
    word_normalized = normalize_text(word)
    variations = [word_normalized]
    
    # Dicionário de variações específicas para impressoras
    word_variations = {
        'digitalizar': ['digitalizar', 'digitalizacao', 'digitalizaçao', 'digitalização', 'scan', 'scanner', 'escanear'],
        'digitalização': ['digitalizar', 'digitalizacao', 'digitalizaçao', 'digitalização', 'scan', 'scanner'],
        'digitalizacao': ['digitalizar', 'digitalizacao', 'digitalizaçao', 'digitalização', 'scan', 'scanner'],
        'imprimir': ['imprimir', 'impressao', 'impressão', 'print', 'printing'],
        'impressao': ['imprimir', 'impressao', 'impressão', 'print', 'printing'],
        'impressão': ['imprimir', 'impressao', 'impressão', 'print', 'printing'],
        'copia': ['copia', 'copiar', 'copy', 'copying'],
        'copiar': ['copia', 'copiar', 'copy', 'copying'],
        'limpar': ['limpar', 'limpeza', 'clean', 'cleaning'],
        'limpeza': ['limpar', 'limpeza', 'clean', 'cleaning'],
        'cartucho': ['cartucho', 'cartridge', 'tinta', 'ink'],
        'tinta': ['tinta', 'ink', 'cartucho', 'cartridge', 'tanque'],
        'papel': ['papel', 'paper', 'folha', 'bandeja'],
        'wifi': ['wifi', 'wi-fi', 'wireless', 'sem fio'],
        'rede': ['rede', 'network', 'wifi', 'wi-fi', 'wireless'],
        'conectar': ['conectar', 'connect', 'conexao', 'conexão'],
        'configurar': ['configurar', 'config', 'configuracao', 'configuração', 'setup'],
        'problema': ['problema', 'erro', 'error', 'falha', 'nao funciona'],
        'trocar': ['trocar', 'substituir', 'replace', 'mudar'],
        'instalar': ['instalar', 'install', 'instalacao', 'instalação'],
        'duplex': ['duplex', 'frente e verso', 'dois lados', 'frente', 'verso']
    }
    
    # Adiciona variações conhecidas
    if word_normalized in word_variations:
        variations.extend(word_variations[word_normalized])
    
    # Adiciona variações automáticas
    if word_normalized.endswith('ção'):
        base = word_normalized[:-4]
        variations.extend([base + 'cao', base + 'car'])
    elif word_normalized.endswith('cao'):
        base = word_normalized[:-3]
        variations.extend([base + 'ção', base + 'car'])
    elif word_normalized.endswith('ar'):
        base = word_normalized[:-2]
        variations.extend([base + 'ção', base + 'cao'])
    
    return list(set(variations))  # Remove duplicatas

def enhanced_search(query):
    """Busca melhorada com múltiplos critérios e normalização"""
    if not knowledge_base:
        return None
    
    query_normalized = normalize_text(query)
    # Remove pontuação para extrair palavras corretamente
    query_cleaned = re.sub(r'[^\w\s]', ' ', query_normalized)
    query_words = [w for w in query_cleaned.split() if len(w) > 2]
    
    # Gera todas as variações das palavras da busca
    all_variations = []
    for word in query_words:
        all_variations.extend(get_word_variations(word))
    all_variations = list(set(all_variations))  # Remove duplicatas
    
    matches = []
    
    for section in knowledge_base:
        score = 0
        section_title_normalized = normalize_text(section['title'])
        section_content_normalized = normalize_text(section['content'])
        
        # Score alto para funcionalidades principais da L3250/L3251
        if any(var in all_variations for var in ['digitalizar', 'digitalizacao', 'scan']):
            if any(term in section_content_normalized for term in ['digitalizar', 'digitalizacao', 'scan', 'scanner', 'epson scan']):
                score += 40
        
        if any(var in all_variations for var in ['copia', 'copiar', 'copy']):
            if any(term in section_content_normalized for term in ['copia', 'copiar', 'copy', 'botao copia']):
                score += 35
        
        if any(var in all_variations for var in ['imprimir', 'impressao', 'print']):
            if any(term in section_content_normalized for term in ['imprimir', 'impressao', 'print']):
                score += 30
        
        if any(var in all_variations for var in ['frente', 'verso', 'duplex', 'dois lados']):
            if any(term in section_content_normalized for term in ['dois lados', 'duplex', 'frente', 'verso']):
                score += 35
        
        if any(var in all_variations for var in ['limpar', 'limpeza']):
            if any(term in section_content_normalized for term in ['limpar', 'limpeza', 'jatos', 'cabecote']):
                score += 30
        
        if any(var in all_variations for var in ['wifi', 'wireless', 'rede']):
            if any(term in section_content_normalized for term in ['wifi', 'wi-fi', 'wireless', 'rede']):
                score += 30
        
        if any(var in all_variations for var in ['cartucho', 'tinta']):
            if any(term in section_content_normalized for term in ['cartucho', 'tinta', 'tanque']):
                score += 30
        
        # Score por palavras-chave normalizadas
        for keyword in section.get('keywords', []):
            keyword_normalized = normalize_text(keyword)
            if any(var in keyword_normalized for var in all_variations):
                score += 15
        
        # Score por tipo de seção relevante
        section_type = section.get('type', '')
        if any(var in all_variations for var in ['problema', 'erro']):
            if section_type == 'solução_problemas':
                score += 20
        if any(var in all_variations for var in ['papel', 'carregar']):
            if section_type == 'papel':
                score += 20
        if any(var in all_variations for var in ['cartucho', 'tinta']):
            if section_type == 'cartuchos':
                score += 20
        if any(var in all_variations for var in ['wifi', 'rede']):
            if section_type == 'conectividade':
                score += 20
        
        # Score por variações no conteúdo
        content_matches = 0
        for variation in all_variations:
            if variation in section_content_normalized:
                content_matches += 1
                score += 5
        
        # Score por variações no título
        title_matches = 0
        for variation in all_variations:
            if variation in section_title_normalized:
                title_matches += 1
                score += 12
        
        # Bonus para múltiplas correspondências
        if title_matches > 0 and content_matches > 1:
            score += 10
        
        if score > 10:  # Threshold otimizado
            matches.append((section, score))
    
    if matches:
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:5]
    
    return None

def load_complete_manual():
    """Carrega manual completo processado"""
    try:
        with open('manual_complete.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Manual carregado: {data['manual_info']['source']}")
        print(f"Seções: {data['manual_info']['total_sections']}")
        print(f"Processado em: {data['manual_info']['processed_at']}")
        
        return data['sections']
    
    except FileNotFoundError:
        print("Arquivo manual_complete.json não encontrado")
        print("Execute: python3 extract_pdf_complete.py")
        return None
    except Exception as e:
        print(f"Erro ao carregar manual: {e}")
        return None

def call_api_detailed(query, manual_sections, mode='detalhado'):
    """Chama API com contexto para respostas em dois modos"""
    global last_request_time, request_times
    
    if mode == 'rapido':
        # Modo rápido - resposta concisa
        context = f"""Você é um especialista técnico na impressora EPSON L3250/L3251. Forneça uma resposta CONCISA e DIRETA.

INSTRUÇÕES PARA MODO RÁPIDO:
- Esta é uma impressora multifuncional Epson L3250/L3251
- Responda de forma BREVE e PRÁTICA
- Máximo 3-4 passos essenciais
- Foque no que é mais importante
- Use linguagem simples e direta
- NÃO inclua explicações longas

MANUAL DA EPSON L3250/L3251:
"""
        max_tokens = 200
        temperature = 0.3
    else:
        # Modo detalhado - resposta completa
        context = f"""Você é um especialista técnico na impressora EPSON L3250/L3251. Analise as seções do manual e forneça uma resposta prática e completa.

INSTRUÇÕES PARA MODO DETALHADO:
- Esta é uma impressora multifuncional Epson L3250/L3251
- Forneça uma resposta COMPLETA e EXPLICATIVA
- Inclua passos numerados detalhados
- Explique o porquê dos procedimentos
- Use as informações das seções para dar contexto
- Seja específico sobre a impressora

MANUAL DA EPSON L3250/L3251:
"""
        max_tokens = 600
        temperature = 0.5
    
    # Adiciona seções encontradas
    for i, (section, score) in enumerate(manual_sections, 1):
        context += f"""
SEÇÃO {i}: {section['title']} (Score: {score})
CATEGORIA: {section.get('type', 'geral')}
CONTEÚDO: {section['content']}
"""
    
    context += f"""
PERGUNTA: {query}

RESPOSTA {'CONCISA' if mode == 'rapido' else 'DETALHADA'} (para Epson L3250/L3251):"""
    
    request_body = {
        "contents": [{"parts": [{"text": context}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "topK": 30,
            "topP": 0.9
        }
    }
    
    try:
        response = requests.post(
            f"{API_URL}?key={API_KEY}",
            headers={"Content-Type": "application/json"},
            json=request_body,
            timeout=45
        )
        
        if not response.ok:
            return False, f"Erro HTTP {response.status_code}"
        
        data = response.json()
        
        if data.get('candidates') and data['candidates'][0].get('content'):
            last_request_time = time.time()
            request_times.append(last_request_time)
            return True, data['candidates'][0]['content']['parts'][0]['text']
        
        return False, "Resposta inválida da API"
        
    except Exception as e:
        return False, f"Erro: {str(e)}"

def can_make_request():
    """Verifica rate limiting"""
    global request_times
    
    now = time.time()
    request_times = [t for t in request_times if now - t < 60]
    
    if len(request_times) >= MAX_REQUESTS_PER_MINUTE:
        return False, "Limite por minuto atingido"
    
    if now - last_request_time < MIN_REQUEST_INTERVAL:
        wait = MIN_REQUEST_INTERVAL - (now - last_request_time)
        return False, f"Aguarde {wait:.1f}s"
    
    return True, None

def format_response(response_text):
    """Formata resposta para melhor leitura"""
    # Adiciona espaçamento em listas
    response_text = re.sub(r'(\d+\.)', r'\n\1', response_text)
    
    # Adiciona espaçamento em marcadores
    response_text = re.sub(r'([•*-])', r'\n\1', response_text)
    
    # Remove linhas vazias excessivas
    response_text = re.sub(r'\n\s*\n\s*\n', '\n\n', response_text)
    
    return response_text.strip()

def show_search_details(manual_sections):
    """Mostra resumo conciso da busca realizada"""
    categories = {}
    for section, score in manual_sections:
        cat = section.get('type', 'geral')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(score)
    
    print(f"Seções encontradas:")
    for category, scores in categories.items():
        avg_score = sum(scores) / len(scores)
        print(f"  {category}: {len(scores)} seção(ões) (relevância: {avg_score:.0f})")
    print()

def main():
    """Função principal com dois modos de resposta"""
    global knowledge_base
    
    print("Carregando manual da Epson L3250/L3251...")
    
    knowledge_base = load_complete_manual()
    if not knowledge_base:
        print("Erro: Manual não encontrado")
        return
    
    print(f"CHATBOT EPSON L3250/L3251")
    print(f"Manual carregado: {len(knowledge_base)} seções indexadas")
    
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
    print("• 'sair' - Encerra o programa")
    print("="*60)
    
    while True:
        try:
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
            
            if not query or len(query) < 3:
                print("Digite uma pergunta mais específica")
                continue
            
            # Rate limiting
            can_req, msg = can_make_request()
            if not can_req:
                print(f"{msg}")
                continue
            
            # Busca no manual
            print("Buscando...")
            manual_sections = enhanced_search(query)
            
            if manual_sections:
                print(f"Encontrado {len(manual_sections)} seção(ões) relevante(s)!")
                
                # Mostra resumo da busca
                show_search_details(manual_sections)
                
                # Gera resposta no modo selecionado
                modo_texto = "RÁPIDA" if modo_atual == 'rapido' else "DETALHADA"
                print(f"Gerando resposta {modo_texto}...")
                success, response = call_api_detailed(query, manual_sections, modo_atual)
                
                if success:
                    print(f"\nRESPOSTA {modo_texto}:")
                    print("="*50)
                    formatted_response = format_response(response)
                    print(formatted_response)
                    
                    print(f"\nFontes: {len(manual_sections)} seção(ões) do manual oficial")
                else:
                    print(response)
            else:
                print("Nenhuma informação encontrada no manual")
                print("Tente termos como: 'tinta', 'papel', 'wifi', 'digitalizar'")
                
        except KeyboardInterrupt:
            print("\n\nAté logo!")
            break
        except Exception as e:
            print(f"\nErro: {e}")

if __name__ == "__main__":
    main()
