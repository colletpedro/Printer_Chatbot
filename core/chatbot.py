#!/usr/bin/env python3

import json
import time
import re
import unicodedata
import os
from collections import Counter
from difflib import SequenceMatcher
from google import genai

# Configurações da API
os.environ['GOOGLE_API_KEY'] = 'AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk'
client = genai.Client()

# Controle otimizado para respostas mais longas
last_request_time = 0
MIN_REQUEST_INTERVAL = 4  # Aumentado para respostas mais longas
request_times = []
MAX_REQUESTS_PER_MINUTE = 8  # Reduzido para dar mais espaço

knowledge_base = []

# Base de dados de metadados das impressoras
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
        'features': ['multifuncional', 'wifi', 'ecotank', 'tanque', 'duplex', 'adf'],
        'series': 'L4000',
        'description': 'Multifuncional colorida com sistema EcoTank, duplex e ADF'
    },
    'impressoraL4260': {
        'full_name': 'Epson L4260',
        'aliases': ['l4260', '4260', 'l 4260', 'epson l4260', 'epson 4260'],
        'type': 'colorida',
        'features': ['multifuncional', 'wifi', 'ecotank', 'tanque', 'duplex', 'adf'],
        'series': 'L4000',
        'description': 'Multifuncional colorida com sistema EcoTank, duplex e ADF'
    }
}

def normalize_text(text):
    """Normaliza texto removendo acentos e convertendo para minúsculas"""
    if not text:
        return ""
    # Remove acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower()

def calculate_similarity(text1, text2):
    """Calcula similaridade entre duas strings (0-1)"""
    return SequenceMatcher(None, normalize_text(text1), normalize_text(text2)).ratio()

def is_cosmetic_difference(user_input, target_name):
    """Verifica se a diferença entre strings é apenas cosmética (espaços, maiúsculas, etc.)"""
    # Normaliza ambas as strings removendo espaços, acentos e convertendo para minúsculas
    def deep_normalize(text):
        normalized = normalize_text(text)
        # Remove espaços, hífens, underscores e outros caracteres de formatação
        normalized = re.sub(r'[^\w]', '', normalized)
        return normalized
    
    user_clean = deep_normalize(user_input)
    target_clean = deep_normalize(target_name)
    
    # Se após limpeza completa são idênticas, é diferença cosmética
    if user_clean == target_clean:
        return True
    
    # Verifica se uma string contém a outra (para casos como "L3150" vs "impressoraL3150")
    if user_clean in target_clean or target_clean in user_clean:
        # Calcula a proporção de caracteres em comum
        shorter = min(len(user_clean), len(target_clean))
        longer = max(len(user_clean), len(target_clean))
        if shorter / longer >= 0.8:  # 80% dos caracteres em comum
            return True
    
    return False

def find_similar_printers(user_input, threshold=0.6, knowledge_base=None):
    """Encontra impressoras similares baseado no input do usuário"""
    user_input_norm = normalize_text(user_input)
    matches = []
    
    # Busca primeiro nos metadados estáticos
    for printer_id, metadata in PRINTER_METADATA.items():
        # Verifica nome completo
        full_name_similarity = calculate_similarity(user_input_norm, metadata['full_name'])
        if full_name_similarity >= threshold:
            matches.append((printer_id, metadata, full_name_similarity, 'nome_completo'))
        
        # Verifica aliases
        for alias in metadata['aliases']:
            alias_similarity = calculate_similarity(user_input_norm, alias)
            if alias_similarity >= threshold:
                matches.append((printer_id, metadata, alias_similarity, 'alias'))
        
        # Verifica se contém partes do nome
        for part in user_input_norm.split():
            if len(part) >= 3:  # Evita matches em palavras muito curtas
                for alias in metadata['aliases']:
                    if part in alias or alias in part:
                        matches.append((printer_id, metadata, 0.7, 'parcial'))
    
    # Busca adicional em modelos disponíveis que não estão no PRINTER_METADATA
    if knowledge_base:
        available_models = get_available_printer_models(knowledge_base)
        for model_id in available_models:
            if model_id not in PRINTER_METADATA:
                # Gera metadados dinamicamente para este modelo
                try:
                    dynamic_metadata = get_printer_metadata_dynamic(model_id, knowledge_base)
                    if dynamic_metadata:
                        # Verifica nome completo
                        full_name_similarity = calculate_similarity(user_input_norm, dynamic_metadata['full_name'])
                        if full_name_similarity >= threshold:
                            matches.append((model_id, dynamic_metadata, full_name_similarity, 'nome_completo'))
                        
                        # Verifica aliases
                        for alias in dynamic_metadata.get('aliases', []):
                            alias_similarity = calculate_similarity(user_input_norm, alias)
                            if alias_similarity >= threshold:
                                matches.append((model_id, dynamic_metadata, alias_similarity, 'alias'))
                        
                        # Verifica se contém partes do nome
                        for part in user_input_norm.split():
                            if len(part) >= 3:
                                for alias in dynamic_metadata.get('aliases', []):
                                    if part in alias or alias in part:
                                        matches.append((model_id, dynamic_metadata, 0.7, 'parcial'))
                except Exception:
                    # Se falhar na geração dinâmica, continua
                    pass
    
    # Remove duplicatas e ordena por similaridade
    unique_matches = {}
    for printer_id, metadata, similarity, match_type in matches:
        if printer_id not in unique_matches or unique_matches[printer_id][2] < similarity:
            unique_matches[printer_id] = (printer_id, metadata, similarity, match_type)
    
    return sorted(unique_matches.values(), key=lambda x: x[2], reverse=True)

def ask_filtering_questions(available_printers):
    """Faz perguntas para filtrar impressoras quando há múltiplas opções"""
    
    # Pergunta 1: Tipo (mono/colorida)
    types = set(PRINTER_METADATA[p]['type'] for p in available_printers)
    if len(types) > 1:
        print("\nSua impressora é colorida? (sim/não/não sei)")
        while True:
            choice = input("Resposta: ").strip().lower()
            if choice in ['sim', 's', 'yes', 'y']:
                available_printers = [p for p in available_printers if PRINTER_METADATA[p]['type'] == 'colorida']
                break
            elif choice in ['nao', 'não', 'n', 'no']:
                available_printers = [p for p in available_printers if PRINTER_METADATA[p]['type'] == 'monocromatica']
                break
            elif choice in ['nao sei', 'não sei', 'ns', 'n/s', '', 'nsei']:
                # Se não sabe, mantém todas as opções
                break
            else:
                print("Por favor, responda com 'sim', 'não' ou 'não sei'")
        
        if len(available_printers) == 1:
            return available_printers[0]
    
    # Pergunta 2: Características especiais - Duplex
    if len(available_printers) > 1:
        # Verifica se há impressoras com duplex
        duplex_printers = [p for p in available_printers if 'duplex' in PRINTER_METADATA[p]['features']]
        if duplex_printers and len(duplex_printers) < len(available_printers):
            print("\nSua impressora imprime frente e verso automaticamente (duplex)? (sim/não/não sei)")
            while True:
                choice = input("Resposta: ").strip().lower()
                if choice in ['sim', 's', 'yes', 'y']:
                    available_printers = duplex_printers
                    break
                elif choice in ['nao', 'não', 'n', 'no']:
                    available_printers = [p for p in available_printers if 'duplex' not in PRINTER_METADATA[p]['features']]
                    break
                elif choice in ['nao sei', 'não sei', 'ns', 'n/s', '', 'nsei']:
                    # Se não sabe, pula essa pergunta
                    break
                else:
                    print("Por favor, responda com 'sim', 'não' ou 'não sei'")
            
            if len(available_printers) == 1:
                return available_printers[0]
    
    # Pergunta 3: Características especiais - ADF (Alimentador Automático de Documentos)
    if len(available_printers) > 1:
        # Verifica se há impressoras com ADF
        adf_printers = [p for p in available_printers if 'adf' in PRINTER_METADATA[p]['features']]
        if adf_printers and len(adf_printers) < len(available_printers):
            print("\nSua impressora tem alimentador automático de documentos (ADF) na parte superior?")
            print("O ADF é uma bandeja onde você coloca várias folhas para digitalizar/copiar automaticamente.")
            print("(sim/não/não sei)")
            while True:
                choice = input("Resposta: ").strip().lower()
                if choice in ['sim', 's', 'yes', 'y']:
                    available_printers = adf_printers
                    break
                elif choice in ['nao', 'não', 'n', 'no']:
                    available_printers = [p for p in available_printers if 'adf' not in PRINTER_METADATA[p]['features']]
                    break
                elif choice in ['nao sei', 'não sei', 'ns', 'n/s', '', 'nsei']:
                    # Se não sabe, pula essa pergunta
                    break
                else:
                    print("Por favor, responda com 'sim', 'não' ou 'não sei'")
            
            if len(available_printers) == 1:
                return available_printers[0]
    
    # Pergunta 4: Pergunta visual sobre o tamanho/formato
    if len(available_printers) > 1:
        # Agrupa por características visuais aproximadas
        compact_models = ['impressoraL3110', 'impressoraL3150', 'impressoraL375']  # Modelos mais compactos
        larger_models = ['impressoraL3250_L3251', 'impressoraL4150', 'impressoraL4260']  # Modelos maiores
        
        compact_available = [p for p in available_printers if p in compact_models]
        larger_available = [p for p in available_printers if p in larger_models]
        
        if compact_available and larger_available:
            print("\nComo você descreveria o tamanho da sua impressora?")
            print("1. Mais compacta/pequena (ocupa menos espaço na mesa)")
            print("2. Maior/robusta (mais funcionalidades, ocupa mais espaço)")
            print("3. Não sei")
            
            while True:
                choice = input("Digite o número (1-3): ").strip()
                if choice == '1':
                    available_printers = compact_available
                    break
                elif choice == '2':
                    available_printers = larger_available
                    break
                elif choice == '3':
                    # Se não sabe, mantém todas as opções
                    break
                else:
                    print("Por favor, digite 1, 2 ou 3")
            
            if len(available_printers) == 1:
                return available_printers[0]
    
    # Pergunta 5: Série da impressora (ÚLTIMA pergunta, só se necessário)
    if len(available_printers) > 1:
        series = set(PRINTER_METADATA[p]['series'] for p in available_printers)
        if len(series) > 1:
            print("\nComo última opção, você consegue identificar a série da sua impressora?")
            print("(Geralmente está escrita na frente da impressora)")
            series_list = sorted(list(series))
            for i, serie in enumerate(series_list, 1):
                printers_in_series = [p for p in available_printers if PRINTER_METADATA[p]['series'] == serie]
                example = PRINTER_METADATA[printers_in_series[0]]['full_name']
                print(f"{i}. Série {serie} (ex: {example})")
            print(f"{len(series_list) + 1}. Não sei/Não consigo ver")
            
            while True:
                try:
                    choice = int(input(f"Digite o número (1-{len(series_list) + 1}): ").strip())
                    if 1 <= choice <= len(series_list):
                        selected_series = series_list[choice - 1]
                        available_printers = [p for p in available_printers if PRINTER_METADATA[p]['series'] == selected_series]
                        break
                    elif choice == len(series_list) + 1:
                        # Não sabe a série, pula para lista final
                        break
                    else:
                        print(f"Por favor, digite um número entre 1 e {len(series_list) + 1}")
                except ValueError:
                    print("Por favor, digite um número válido")
            
            if len(available_printers) == 1:
                return available_printers[0]
    
    # Se ainda há múltiplas opções, encerra o atendimento
    if len(available_printers) > 1:
        print("\n❌ Não foi possível identificar sua impressora com precisão.")
        print("Para um atendimento mais eficaz, recomendamos que você:")
        print("• Verifique o modelo exato da impressora (geralmente está na frente do equipamento)")
        print("• Tente novamente informando o modelo específico (ex: L3150, L4260, etc.)")
        print("\nAtendimento encerrado. Obrigado!")
        return None
    
    return available_printers[0] if available_printers else None

def smart_printer_detection(query, available_models, max_attempts=3):
    """Sistema inteligente de detecção de impressora"""
    attempt = 0
    
    while attempt < max_attempts:
        if attempt == 0:
            # Primeira tentativa: usar a query original
            user_input = query
            print("Analisando sua pergunta para identificar a impressora...")
        else:
            # Tentativas subsequentes: pedir input específico
            print(f"\nTentativa {attempt + 1}/{max_attempts}")
            print("Digite o modelo da sua impressora Epson:")
            print("Exemplos: L3250, L4150, L375, L3150")
            user_input = input("Modelo: ").strip()
        
        if not user_input:
            attempt += 1
            continue
        
        # 1. Busca exata (método original)
        for model in available_models:
            if normalize_text(model) in normalize_text(user_input):
                metadata = get_printer_metadata_dynamic(model, knowledge_base)
                print(f"Impressora identificada: {metadata['full_name']}")
                return model
        
        # 2. Busca por similaridade
        similar_printers = find_similar_printers(user_input, 0.6, knowledge_base)
        
        if similar_printers:
            if len(similar_printers) == 1:
                printer_id, metadata, similarity, match_type = similar_printers[0]
                
                # Verifica se é diferença cosmética - aceita automaticamente
                if is_cosmetic_difference(user_input, metadata['full_name']) or \
                   any(is_cosmetic_difference(user_input, alias) for alias in metadata['aliases']):
                    print(f"Impressora identificada: {metadata['full_name']}")
                    return printer_id
                elif similarity >= 0.85:  # Alta confiança
                    print(f"Impressora identificada: {metadata['full_name']} (confiança: {similarity:.0%})")
                    return printer_id
                else:
                    # Confirma com o usuário
                    print(f"Você quis dizer '{metadata['full_name']}'? (sim/não)")
                    choice = input("Resposta: ").strip().lower()
                    if choice in ['sim', 's', 'yes', 'y']:
                        print(f"Impressora confirmada: {metadata['full_name']}")
                        return printer_id
            else:
                # Múltiplas opções similares - usar sistema de filtragem
                print(f"Encontrei {len(similar_printers)} impressoras similares.")
                potential_printers = [p[0] for p in similar_printers if p[2] >= 0.5]
                result = ask_filtering_questions(potential_printers)
                if result:
                    result_metadata = get_printer_metadata_dynamic(result, knowledge_base)
                    print(f"Impressora identificada: {result_metadata['full_name']}")
                    return result
        
        # 3. Se não encontrou nada similar, usar sistema de filtragem com todas as impressoras
        if attempt == 0:  # Só faz isso na primeira tentativa
            print("Não consegui identificar a impressora pela sua pergunta.")
            print("\nVocê sabe o modelo da sua impressora? (sim/não/não sei)")
            choice = input("Resposta: ").strip().lower()
            
            if choice in ['nao sei', 'não sei', 'ns', 'n/s', '', 'nsei']:
                print("\nSem problemas! Vou fazer algumas perguntas para identificar sua impressora:")
            elif choice in ['sim', 's', 'yes', 'y']:
                print("\nQual é o modelo?")
                model_input = input("Modelo: ").strip()
                
                # Remove caracteres não alfanuméricos para comparação
                clean_input = re.sub(r'[^a-zA-Z0-9]', '', model_input.lower())
                
                # Primeiro tenta match exato com os modelos disponíveis
                for model_id, metadata in PRINTER_METADATA.items():
                    model_aliases = [re.sub(r'[^a-zA-Z0-9]', '', alias.lower()) for alias in metadata['aliases']]
                    if clean_input in model_aliases:
                        print(f"Impressora identificada: {metadata['full_name']}")
                        return model_id
                
                # Se não encontrou match exato, procura por similaridade
                similar_printers = find_similar_printers(model_input, 0.6, knowledge_base)
                if similar_printers:
                    printer_id, metadata, similarity, match_type = similar_printers[0]
                    # Agora só aceita automaticamente se for MUITO similar
                    if similarity >= 0.9:
                        print(f"Impressora identificada: {metadata['full_name']}")
                        return printer_id
                    else:
                        # Modelo não encontrado - mensagem genérica
                        print(f"\nDesculpe, não encontrei uma impressora '{model_input}'.")
                        print("Vou fazer algumas perguntas para identificar sua impressora corretamente.")
            
            # Se não souber o modelo ou não encontrou, vai para as perguntas de filtragem
            print("\nVou fazer algumas perguntas para identificar sua impressora:")
            result = ask_filtering_questions(available_models)
            if result:
                result_metadata = get_printer_metadata_dynamic(result, knowledge_base)
                print(f"Impressora identificada: {result_metadata['full_name']}")
                return result
            else:
                # Se ask_filtering_questions retornou None, significa que o atendimento foi encerrado
                # Não continua com tentativas adicionais
                return None
        
        attempt += 1
        if attempt < max_attempts:
            print(f"Modelo não reconhecido. Você tem mais {max_attempts - attempt} tentativa(s).")
    
    # Se esgotar as tentativas
    print("\nNão foi possível identificar sua impressora.")
    print("Impressoras disponíveis em nossa base de dados:")
    for model in available_models:
        if model in PRINTER_METADATA:
            metadata = PRINTER_METADATA[model]
            print(f"  • {metadata['full_name']} - {metadata['description']}")
    
    return None

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

def enhanced_search(query, filtered_knowledge_base=None):
    """Busca melhorada com múltiplos critérios e normalização"""
    if filtered_knowledge_base is None:
        filtered_knowledge_base = knowledge_base
    
    if not filtered_knowledge_base:
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
    
    for section in filtered_knowledge_base:
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

def detect_printer_model(query, available_models):
    """Detecta o modelo de impressora mencionado na pergunta, se houver"""
    query_norm = normalize_text(query)
    for model in available_models:
        if model.lower() in query_norm:
            return model
    return None

def get_available_printer_models(knowledge_base):
    """Extract available printer models from knowledge base"""
    if not knowledge_base:
        return []
    
    models = set()
    for section in knowledge_base:
        model = section.get('printer_model', '').strip()
        if model:
            models.add(model)
    
    return sorted(list(models))

def auto_generate_printer_metadata(model_name):
    """
    Automatically generate basic metadata for unknown printer models
    """
    # Extract model number/name from the model_name
    model_clean = model_name.replace('impressora', '').upper()
    
    # Try to extract series information
    series = 'Unknown'
    if 'L3' in model_clean:
        series = 'L3000'
    elif 'L4' in model_clean:
        series = 'L4000'
    elif 'L5' in model_clean:
        series = 'L5000'
    elif 'L6' in model_clean:
        series = 'L6000'
    
    # Generate basic aliases
    aliases = []
    # Try to extract the model number (e.g., L4260 from impressoraL4260)
    import re
    model_match = re.search(r'L?\d{4,5}', model_clean)
    if model_match:
        model_num = model_match.group()
        aliases.extend([
            model_num.lower(),
            model_num,
            f'l {model_num[-4:]}',
            f'epson {model_num.lower()}',
            f'epson {model_num}'
        ])
    
    return {
        'full_name': f'Epson {model_clean}',
        'aliases': aliases,
        'type': 'colorida',  # Default assumption for newer models
        'features': ['multifuncional', 'wifi', 'ecotank', 'tanque'],  # Common features
        'series': series,
        'description': f'Impressora multifuncional Epson {model_clean} com sistema EcoTank'
    }

def get_printer_metadata_dynamic(model_name, knowledge_base):
    """
    Get printer metadata, generating it automatically if not found in PRINTER_METADATA
    """
    # First check if we have predefined metadata
    if model_name in PRINTER_METADATA:
        return PRINTER_METADATA[model_name]
    
    # If not found, generate metadata automatically
    print(f"🔧 Gerando metadados automaticamente para: {model_name}")
    auto_metadata = auto_generate_printer_metadata(model_name)
    
    # Temporarily add to PRINTER_METADATA for this session
    PRINTER_METADATA[model_name] = auto_metadata
    
    return auto_metadata

def check_question_relevance(query):
    """Verifica se a pergunta tem relação com impressoras usando a API"""
    global last_request_time, request_times
    
    context = f"""Você é um analisador de contexto especializado em impressoras Epson.

Sua única função é determinar se uma pergunta tem relação com impressoras, especificamente com:
- Impressoras Epson
- Impressão, digitalização, cópia
- Problemas de impressão
- Configuração de impressoras
- Cartuchos, tinta, papel
- Conectividade (WiFi, USB, drivers)
- Manutenção de impressoras
- Software de impressão

Responda APENAS com:
- "RELEVANTE" - se a pergunta for sobre impressoras ou relacionada
- "IRRELEVANTE" - se a pergunta não tiver relação com impressoras

Exemplos:
- "Como trocar a tinta?" → RELEVANTE
- "Como limpar o cabeçote?" → RELEVANTE
- "Como configurar WiFi na impressora?" → RELEVANTE
- "Como acelerar meu carro?" → IRRELEVANTE
- "Como limpar o para-brisa do Palio?" → IRRELEVANTE
- "Qual a receita de bolo?" → IRRELEVANTE

PERGUNTA: {query}

RESPOSTA:"""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=context
        )
        
        result = response.text.strip().upper() if response.text else "IRRELEVANTE"
        last_request_time = time.time()
        request_times.append(last_request_time)
        return "RELEVANTE" in result
        
    except Exception as e:
        return True  # Em caso de erro, assume que é relevante para não bloquear

def reload_knowledge_base_if_updated():
    """
    Recarrega a base de conhecimento se detectar que foi atualizada
    """
    global knowledge_base
    
    try:
        # Verifica se há atualizações
        is_updated, status = check_and_reload_manual()
        
        if is_updated:
            print("\n🔄 Detectada atualização na base de conhecimento!")
            print("   Recarregando manual...")
            
            # Recarrega o manual
            manual_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'manual_complete.json')
            with open(manual_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            old_count = len(knowledge_base)
            knowledge_base = data['sections']
            new_count = len(knowledge_base)
            
            print(f"   ✅ Base atualizada: {old_count} → {new_count} seções")
            
            # Atualiza modelos disponíveis
            available_models = get_available_printer_models(knowledge_base)
            print(f"   📱 Modelos disponíveis: {len(available_models)}")
            
            return True, "Base de conhecimento atualizada com sucesso"
        
        return False, status
        
    except Exception as e:
        return False, f"Erro ao recarregar base: {e}"

def check_and_reload_manual():
    """
    Verifica se o manual foi atualizado recentemente e recarrega se necessário
    """
    try:
        # Verifica se existe arquivo de atividade do webhook
        webhook_activity_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'webhook_activity.json')
        if not os.path.exists(webhook_activity_path):
            return False, "Nenhuma atividade de webhook encontrada"
        
        # Carrega atividades do webhook
        with open(webhook_activity_path, 'r', encoding='utf-8') as f:
            activities = json.load(f)
        
        # Procura pela última atualização bem-sucedida
        last_update = None
        for activity in reversed(activities):
            if activity.get('type') == 'update_success':
                last_update = activity.get('timestamp')
                break
        
        if not last_update:
            return False, "Nenhuma atualização encontrada nos logs do webhook"
        
        # Verifica quando o manual foi carregado pela última vez
        manual_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'manual_complete.json')
        if not os.path.exists(manual_path):
            return False, "Manual não encontrado"
        
        # Compara timestamps
        from datetime import datetime
        
        # Timestamp da última atualização do webhook
        webhook_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
        
        # Timestamp de modificação do arquivo
        manual_mod_time = datetime.fromtimestamp(os.path.getmtime(manual_path))
        
        # Se o webhook foi executado após a última modificação do arquivo, pode haver uma atualização
        time_diff = (webhook_time - manual_mod_time).total_seconds()
        
        if abs(time_diff) < 300:  # 5 minutos de tolerância
            return True, f"✅ Manual atualizado recentemente ({webhook_time.strftime('%H:%M:%S')})"
        else:
            return False, f"Manual carregado em {manual_mod_time.strftime('%H:%M:%S')}, última atualização: {webhook_time.strftime('%H:%M:%S')}"
            
    except Exception as e:
        return False, f"Erro ao verificar atualizações: {e}"

def check_webhook_status():
    """Check if webhook system is active and show status"""
    try:
        # Check if webhook files exist
        webhook_files = ['webhook_channels.json', 'webhook_activity.json']
        webhook_active = any(os.path.exists(f) for f in webhook_files)
        
        if not webhook_active:
            return False, "Webhook não configurado"
        
        # Check webhook channels
        webhook_channels_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'webhook_channels.json')
        if os.path.exists(webhook_channels_path):
            with open(webhook_channels_path, 'r') as f:
                channels = json.load(f)
            
            active_channels = [c for c in channels if c.get('status') == 'active']
            
            if active_channels:
                # Get the latest channel
                latest = max(active_channels, key=lambda x: x.get('created_at', ''))
                
                # Check expiration
                expiration = latest.get('expiration')
                if expiration:
                    exp_time = __import__('datetime').datetime.fromtimestamp(int(expiration)/1000)
                    now = __import__('datetime').datetime.now()
                    time_left = exp_time - now
                    
                    if time_left.total_seconds() > 0:
                        hours_left = time_left.total_seconds() / 3600
                        if hours_left < 24:
                            return True, f"⚠️ Webhook ativo (expira em {hours_left:.1f}h) - RENOVAR LOGO!"
                        elif hours_left < 48:
                            return True, f"⚠️ Webhook ativo (expira em {hours_left:.1f}h) - Considere renovar"
                        else:
                            days_left = time_left.days
                            return True, f"✅ Webhook ativo (expira em {days_left} dia{'s' if days_left != 1 else ''})"
                    else:
                        return False, "❌ Webhook EXPIRADO - Execute: python renew_webhook.py"
                
                return True, "✅ Webhook ativo"
            else:
                return False, "❌ Nenhum webhook ativo"
        
        return False, "Status desconhecido"
        
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

def call_api_detailed(query, manual_sections, mode='detalhado', printer_model=None):
    """Chama API com contexto para respostas em dois modos"""
    global last_request_time, request_times
    
    # Extrai o nome amigável da impressora se disponível
    printer_name = "impressora"
    if printer_model and printer_model in PRINTER_METADATA:
        printer_name = PRINTER_METADATA[printer_model]['full_name']
    
    if mode == 'rapido':
        # Modo rápido - resposta concisa
        context = f"""Você é um especialista técnico em impressoras EPSON, com profundo conhecimento de toda a linha EcoTank. Forneça uma resposta CONCISA e DIRETA.

INSTRUÇÕES PARA MODO RÁPIDO:
- Adapte a resposta especificamente para o modelo {printer_model} identificado
- Considere as características específicas deste modelo (ex: se tem duplex, wifi, etc)
- Responda de forma BREVE e PRÁTICA em 3-4 passos
- Use linguagem simples e direta
- Foque nas particularidades do modelo em questão
- Evite informações genéricas que não se aplicam ao modelo
- IMPORTANTE: Use APENAS o modelo identificado ({printer_model}). NÃO mencione outros modelos de impressora
- NÃO invente ou cite modelos que não foram especificamente identificados

MANUAL DA IMPRESSORA:
"""
        max_tokens = 200
        temperature = 0.3
    else:
        # Modo detalhado - resposta completa
        context = f"""Você é um especialista técnico em impressoras EPSON, com profundo conhecimento de toda a linha EcoTank. Analise as seções do manual e forneça uma resposta detalhada e específica.

INSTRUÇÕES PARA MODO DETALHADO:
- Você está respondendo sobre a {printer_name}
- Considere todas as características específicas deste modelo:
  • Recursos disponíveis (duplex, wifi, etc)
  • Limitações técnicas
  • Particularidades de operação
- Forneça uma resposta COMPLETA e EXPLICATIVA com:
  • Passos numerados e detalhados
  • Explicação do porquê de cada procedimento
  • Dicas específicas para este modelo
  • Alertas sobre possíveis erros comuns
- Use APENAS informações relevantes para este modelo específico
- Evite informações genéricas que não se aplicam
- Evite escrever em formato markdown ou similar, ou abusar de smbolos de pontuação. Mantenha uma linguagem natural e formatada.
- IMPORTANTE: Responda EXCLUSIVAMENTE sobre o modelo {printer_model}. NÃO mencione outros modelos
- NÃO invente, cite ou compare com modelos que não foram especificamente identificados

MANUAL DA IMPRESSORA:
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

RESPOSTA {'CONCISA' if mode == 'rapido' else 'DETALHADA'} (para Epson):"""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=context
        )
        
        last_request_time = time.time()
        request_times.append(last_request_time)
        
        # Validação para evitar confusão entre modelos
        response_text = response.text
        if printer_model:
            # Remove menções a modelos incorretos que não sejam o identificado
            import re
            # Padrão para encontrar menções a modelos L seguidos de números
            pattern = r'L\d{4}'
            matches = re.findall(pattern, response_text)
            
            # Verifica se há menções a modelos diferentes do identificado
            correct_model_numbers = []
            if 'L3250' in printer_model or 'L3251' in printer_model:
                correct_model_numbers = ['L3250', 'L3251']
            elif 'L' in printer_model:
                # Extrai o número do modelo correto
                model_match = re.search(r'L\d{4}', printer_model)
                if model_match:
                    correct_model_numbers = [model_match.group()]
            
            # Remove menções a modelos incorretos
            for match in matches:
                if match not in correct_model_numbers:
                    # Substitui menção incorreta pelo modelo correto
                    if correct_model_numbers:
                        response_text = response_text.replace(match, correct_model_numbers[0])
                    else:
                        # Remove a menção incorreta completamente
                        response_text = re.sub(rf'\b{match}\b.*?não corresponde.*?manual[^.]*\.?', '', response_text)
        
        return True, response_text
        
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
    
    print("Carregando base de manuais Epson...")
    
    knowledge_base = load_complete_manual()
    if not knowledge_base:
        print("Erro: Manual não encontrado")
        return
    
    available_models = get_available_printer_models(knowledge_base)
    print("CHATBOT EPSON - Sistema Inteligente de Suporte")
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
    print("• 'reload' - Verifica e recarrega a base de conhecimento")
    print("• 'sair' - Encerra o programa")
    print("="*60)
    
    question_count = 0  # Contador para verificações automáticas
    
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
                # Se o sistema de afunilamento não conseguiu identificar, encerra o programa
                break
            
            # Filtrar base pelo modelo
            filtered_knowledge_base = [s for s in knowledge_base if s.get('printer_model') == printer_model]
            if not filtered_knowledge_base:
                print(f"❌ Não há informações para o modelo '{printer_model}'.")
                continue
            # Busca no manual filtrado
            print(f"Buscando no manual do modelo {printer_model}...")
            manual_sections = enhanced_search(query, filtered_knowledge_base)
            # O restante do fluxo segue igual, usando manual_sections
            # Rate limiting
            can_req, msg = can_make_request()
            if not can_req:
                print(f"{msg}")
                continue
            
            # Verifica relevância baseada na busca no manual
            if manual_sections:
                high_score_sections = [section for section in manual_sections if section[1] >= 80]
                if high_score_sections:
                    print(f"Encontrado {len(manual_sections)} seção(ões) relevante(s)!")
                    show_search_details(manual_sections)
                    modo_texto = "RÁPIDA" if modo_atual == 'rapido' else "DETALHADA"
                    print(f"Gerando resposta {modo_texto}...")
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
                    if not check_question_relevance(query):
                        print("\nEsta pergunta não tem relação com impressoras disponíveis.")
                        print("Posso ajudar com dúvidas sobre impressão, digitalização, conectividade, cartuchos, papel ou manutenção destas impressoras.")
                        continue
                    else:
                        print("Nenhuma informação específica encontrada no manual")
            else:
                print("Analisando relevância da pergunta...")
                if not check_question_relevance(query):
                    print("\nEsta pergunta não tem relação com impressoras disponíveis.")
                    print("Posso ajudar com dúvidas sobre impressão, digitalização, conectividade, cartuchos, papel ou manutenção destas impressoras.")
                    continue
                else:
                    print("Nenhuma informação encontrada no manual")

            # Incrementa contador de perguntas (apenas para perguntas válidas)
            question_count += 1
                
        except KeyboardInterrupt:
            print("\n\nAté logo!")
            break
        except Exception as e:
            print(f"\nErro: {e}")

if __name__ == "__main__":
    main()
