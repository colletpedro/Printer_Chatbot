#!/usr/bin/env python3
"""
Chatbot Epson com ChromaDB - Versão Moderna
Sistema exclusivamente ChromaDB com busca semântica avançada

CARACTERÍSTICAS:
- Busca semântica exclusiva via ChromaDB (sem fallback JSON)
- Falha rápida se ChromaDB não disponível
- API Key segura via variáveis de ambiente
- Interface moderna e limpa
- Detecção inteligente de impressoras
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
from dotenv import load_dotenv
import google.generativeai as genai

# Carrega variáveis de ambiente
load_dotenv()

# Adiciona path para importar ChromaDB integration e sync
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Configurações da API Gemini
# Chave da API Gemini (hardcoded para facilitar uso)
GEMINI_API_KEY = "AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk"
genai.configure(api_key=GEMINI_API_KEY)
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
    'impressoral3250_l3251': {
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
    },
    'impressoral5190': {
        'full_name': 'Epson L5190',
        'aliases': ['l5190', '5190', 'l 5190', 'epson l5190', 'epson 5190'],
        'type': 'colorida',
        'features': ['multifuncional', 'wifi', 'ecotank', 'tanque', 'duplex', 'adf', 'fax'],
        'series': 'L5000',
        'description': 'Multifuncional colorida com sistema EcoTank, duplex, ADF e fax'
    },
    'impressoral6490': {
        'full_name': 'Epson L6490',
        'aliases': ['l6490', '6490', 'l 6490', 'epson l6490', 'epson 6490'],
        'type': 'colorida',
        'features': ['multifuncional', 'wifi', 'ecotank', 'tanque', 'duplex', 'adf', 'fax', 'a3'],
        'series': 'L6000',
        'description': 'Multifuncional colorida A3 com sistema EcoTank, duplex, ADF e fax'
    },
    'impressoraL1300': {
        'full_name': 'Epson L1300',
        'aliases': ['l1300', '1300', 'l 1300', 'epson l1300', 'epson 1300'],
        'type': 'colorida',
        'features': ['ecotank', 'tanque', 'a3'],
        'series': 'L1000',
        'description': 'Impressora colorida A3 com sistema EcoTank (só imprime)'
    }
}

# Sistema ChromaDB
chromadb_search = None
using_chromadb = False

def sync_printer_metadata_from_chromadb():
    """
    Sincroniza PRINTER_METADATA com TODOS os modelos disponíveis no ChromaDB.
    Garante que qualquer impressora na base seja reconhecida automaticamente.
    """
    global PRINTER_METADATA
    
    try:
        from printer_metadata_sync import build_complete_printer_metadata
        
        # Obtém metadados completos do ChromaDB
        dynamic_metadata = build_complete_printer_metadata()
        
        if dynamic_metadata:
            # Atualiza PRINTER_METADATA com os dados dinâmicos
            PRINTER_METADATA.update(dynamic_metadata)
            print(f"   📱 {len(dynamic_metadata)} modelos sincronizados do ChromaDB")
            return True
        else:
            print("   ⚠️ Nenhum modelo encontrado para sincronizar")
            return False
            
    except Exception as e:
        print(f"   ⚠️ Erro na sincronização de metadados: {e}")
        # Continua com metadados estáticos se falhar
        return False

def init_chromadb():
    """Inicializa ChromaDB - OBRIGATÓRIO (sem fallback)"""
    global chromadb_search, using_chromadb
    
    try:
        from chromadb_integration_example import ChromaDBSearch
        chromadb_search = ChromaDBSearch()
        using_chromadb = True
        print("✅ ChromaDB carregado - sistema de busca semântica ativo!")
        return True
    except Exception as e:
        print("❌ ERRO CRÍTICO: ChromaDB não disponível")
        print(f"   Detalhes: {e}")
        print("\n💡 SOLUÇÕES:")
        print("   1. Execute: python scripts/sync_drive_chromadb.py")
        print("   2. Verifique se o ChromaDB foi inicializado corretamente")
        print("   3. Verifique as dependências: pip install chromadb")
        print("\n🚫 Este chatbot funciona EXCLUSIVAMENTE com ChromaDB")
        sys.exit(1)

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

def enhanced_search_chromadb(query, printer_model=None):
    """
    Busca semântica exclusiva via ChromaDB.
    Retorna lista de tuplas (documento, score).
    """
    if not (using_chromadb and chromadb_search):
        print("❌ ERRO CRÍTICO: ChromaDB não inicializado")
        sys.exit(1)

    try:
        print("🔍 Executando busca semântica...")

        # Expande consulta para melhorar busca de tinta
        expanded_query = expand_ink_query(query)
        if expanded_query != query:
            print(f"   🔍 Consulta expandida: '{expanded_query}'")

        results = chromadb_search.semantic_search(
            query=expanded_query,
            printer_model=printer_model,
            n_results=15,
            min_similarity=0.2
        )

        if results:
            print(f"   ✅ Encontrados {len(results)} resultados relevantes")
            return results
        else:
            print("   ⚠️  Nenhum resultado encontrado")
            return []

    except Exception as e:
        print(f"❌ ERRO na busca ChromaDB: {e}")
        print("💡 Verifique se o ChromaDB está funcionando corretamente")
        sys.exit(1)

# FUNÇÕES UTILITÁRIAS (mantidas para detecção de impressoras)

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
    try:
        is_updated, status = check_and_reload_manual()
        
        if is_updated:
            print("\n🔄 Detectada atualização na base de conhecimento!")
            # Atualiza modelos diretamente do ChromaDB (modo somente ChromaDB)
            try:
                available_models = chromadb_search.get_available_printer_models()
            except Exception:
                available_models = []
            print(f"   📱 Modelos disponíveis: {len(available_models)}")
            
            return True, "Base de conhecimento atualizada com sucesso"
        
        return False, status
        
    except Exception as e:
        return False, f"Erro ao recarregar base: {e}"

def auto_update_chromadb_if_needed():
    """Atualiza ChromaDB automaticamente se detectar mudanças na base de conhecimento"""
    global chromadb_search
    
    try:
        # Verifica se há atualizações pendentes
        is_updated, status = check_and_reload_manual()
        
        if is_updated:
            print("\nATUALIZAÇÃO AUTOMÁTICA INICIADA")
            print("=" * 50)
            print("Detectadas mudanças na base de conhecimento!")
            print("Atualizando ChromaDB automaticamente...")
            print("(Isso pode demorar alguns minutos)")
            print("")
            
            # Importa e executa a migração
            import subprocess
            import sys
            
            # Caminho para o script de migração direta (sem JSON)
            migrate_script = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'migrate_from_drive_to_chromadb.py')
            
            print("Executando migração para ChromaDB...")
            print("Por favor, aguarde...")
            
            # Executa o script de migração
            result = subprocess.run([
                sys.executable, migrate_script
            ], capture_output=True, text=True, cwd=os.path.dirname(migrate_script))
            
            if result.returncode == 0:
                print("\nATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
                print("=" * 50)
                print("ChromaDB foi atualizado com os novos dados.")
                print("Reinicializando sistema ChromaDB...")
                
                # Reinicializa o ChromaDB
                init_chromadb()
                
                return True, "ChromaDB atualizado automaticamente"
            else:
                print(f"\nERRO na atualização automática:")
                print(f"Código de erro: {result.returncode}")
                if result.stderr:
                    print(f"Erro: {result.stderr}")
                print("\nContinuando com a base atual...")
                return False, "Erro na atualização automática do ChromaDB"
        
        return False, "Nenhuma atualização necessária"
        
    except Exception as e:
        print(f"\nErro na atualização automática: {e}")
        print("Continuando com a base atual...")
        return False, f"Erro na atualização automática: {e}"

def check_and_reload_manual():
    """Verifica se o manual foi atualizado recentemente"""
    try:
        webhook_activity_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'webhook_activity.json')
        chroma_log_path = os.path.join(os.path.dirname(__file__), '..', 'chromadb_storage', 'migration_log.json')
        
        if not os.path.exists(webhook_activity_path):
            return False, "Atividade de webhook não encontrada"
        
        # Verifica timestamp do webhook
        with open(webhook_activity_path, 'r', encoding='utf-8') as f:
            webhook_data = json.load(f)

        # Normaliza o formato: aceita tanto lista quanto dict com chave 'activities'
        if isinstance(webhook_data, dict):
            activities = webhook_data.get('activities', [])
            # Se não houver chave 'activities' mas o dict se parecer com uma activity única
            if not activities:
                activities = [webhook_data]
        elif isinstance(webhook_data, list):
            activities = webhook_data
        else:
            return False, "Formato inesperado de webhook_activity.json"

        # Filtra somente dicts válidos
        activities = [a for a in activities if isinstance(a, dict)]
        if not activities:
            return False, "Nenhuma atividade de webhook encontrada"

        # Busca a última activity com timestamp; preferir update_success quando existir
        def is_update_success(act):
            et = act.get('type') or act.get('event_type')
            return et == 'update_success'

        # Ordena por timestamp na cauda (mantém ordem original, mas tentamos priorizar update_success)
        last_activity = next((a for a in reversed(activities) if is_update_success(a)), activities[-1])
        last_update_time = last_activity.get('timestamp', '')
        
        # Pega timestamp do último ingestion/migration do ChromaDB
        migration_dt = None
        if os.path.exists(chroma_log_path):
            try:
                with open(chroma_log_path, 'r', encoding='utf-8') as f:
                    mig = json.load(f)
                mig_ts = mig.get('migration_date') or mig.get('date')
                if mig_ts:
                    migration_dt = __import__('datetime').datetime.fromisoformat(mig_ts.replace('Z', '+00:00'))
            except Exception:
                migration_dt = None
        
        # Se não existe log de migração ainda, e há activity de webhook, pedimos atualização
        if migration_dt is None and last_update_time:
            return True, f"Atualização necessária (sem histórico de migração; webhook: {last_update_time})"
        
        # Se o webhook é mais recente que a migração atual, precisa atualizar
        # Tenta comparar de forma robusta usando datetime quando possível
        try:
            from datetime import datetime
            # webhook usa ISO 8601
            webhook_dt = None
            if last_update_time:
                # Suporta 'Z' no final
                iso = last_update_time.replace('Z', '+00:00')
                webhook_dt = datetime.fromisoformat(iso)
            if webhook_dt and migration_dt and webhook_dt > migration_dt:
                return True, f"Atualização disponível (webhook: {last_update_time} > migração: {migration_dt.isoformat()})"
        except Exception:
            # Fallback: comparação por string (menos precisa, mas evita quebra)
            if last_update_time:
                return False, "Não foi possível comparar timestamps com precisão"
        
        return False, "ChromaDB está atualizado"
        
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

        # Normaliza formato: aceita dict com 'channels' ou lista direta
        if isinstance(channels_data, dict):
            channels = channels_data.get('channels', [])
            if not channels:
                # Pode ser um dict de um único canal
                channels = [channels_data]
        elif isinstance(channels_data, list):
            channels = channels_data
        else:
            return False, "Formato inesperado de webhook_channels.json"

        # Filtra canais válidos e ativos
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

def ask_filtering_questions(available_printers):
    """Faz perguntas para filtrar impressoras quando há múltiplas opções, com segurança para modelos desconhecidos"""
    
    # Garante que todos os modelos tenham metadados (gera dinamicamente quando faltar)
    normalized_printers = []
    for model in available_printers:
        if model not in PRINTER_METADATA:
            try:
                meta = get_printer_metadata_dynamic(model, None)
                if meta:
                    PRINTER_METADATA[model] = meta
            except Exception:
                pass
        normalized_printers.append(model)
    
    # Trabalha apenas com modelos que temos algum metadado após a normalização
    available_printers = [p for p in normalized_printers if p in PRINTER_METADATA]
    if not available_printers:
        print("\n❌ Não foi possível identificar sua impressora com precisão.")
        print("Modelos fornecidos não possuem metadados conhecidos nesta versão.")
        return None
    
    # Pergunta 1: Tipo (mono/colorida)
    types = set(PRINTER_METADATA[p]['type'] for p in available_printers if p in PRINTER_METADATA)
    if len(types) > 1:
        print("\nSua impressora é colorida? (sim/não/não sei)")
        while True:
            choice = input("Resposta: ").strip().lower()
            if choice in ['sim', 's', 'yes', 'y']:
                previous = list(available_printers)
                filtered = [p for p in available_printers if p in PRINTER_METADATA and PRINTER_METADATA[p]['type'] == 'colorida']
                available_printers = filtered or previous
                break
            elif choice in ['nao', 'não', 'n', 'no']:
                previous = list(available_printers)
                filtered = [p for p in available_printers if p in PRINTER_METADATA and PRINTER_METADATA[p]['type'] == 'monocromatica']
                available_printers = filtered or previous
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
        duplex_printers = [p for p in available_printers if p in PRINTER_METADATA and 'duplex' in PRINTER_METADATA[p]['features']]
        if duplex_printers and len(duplex_printers) < len(available_printers):
            print("\nSua impressora imprime frente e verso automaticamente (duplex)? (sim/não/não sei)")
            while True:
                choice = input("Resposta: ").strip().lower()
                if choice in ['sim', 's', 'yes', 'y']:
                    available_printers = duplex_printers
                    break
                elif choice in ['nao', 'não', 'n', 'no']:
                    previous = list(available_printers)
                    filtered = [p for p in available_printers if p in PRINTER_METADATA and 'duplex' not in PRINTER_METADATA[p]['features']]
                    available_printers = filtered or previous
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
        adf_printers = [p for p in available_printers if p in PRINTER_METADATA and 'adf' in PRINTER_METADATA[p]['features']]
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
                    previous = list(available_printers)
                    filtered = [p for p in available_printers if p in PRINTER_METADATA and 'adf' not in PRINTER_METADATA[p]['features']]
                    available_printers = filtered or previous
                    break
                elif choice in ['nao sei', 'não sei', 'ns', 'n/s', '', 'nsei']:
                    # Se não sabe, pula essa pergunta
                    break
                else:
                    print("Por favor, responda com 'sim', 'não' ou 'não sei'")
            
            if len(available_printers) == 1:
                return available_printers[0]
    
    # Pergunta 3.1: Formato de papel - A3
    if len(available_printers) > 1:
        a3_printers = [p for p in available_printers if 'a3' in PRINTER_METADATA[p].get('features', [])]
        if a3_printers and len(a3_printers) < len(available_printers):
            print("\nSua impressora imprime em tamanho A3? (sim/não/não sei)")
            while True:
                choice = input("Resposta: ").strip().lower()
                if choice in ['sim', 's', 'yes', 'y']:
                    available_printers = a3_printers
                    break
                elif choice in ['nao', 'não', 'n', 'no']:
                    previous = list(available_printers)
                    filtered = [p for p in available_printers if p not in a3_printers]
                    available_printers = filtered or previous
                    break
                elif choice in ['nao sei', 'não sei', 'ns', 'n/s', '', 'nsei']:
                    break
                else:
                    print("Por favor, responda com 'sim', 'não' ou 'não sei'")
            if len(available_printers) == 1:
                return available_printers[0]
    
    # Pergunta 3.2: Possui FAX
    if len(available_printers) > 1:
        fax_printers = [p for p in available_printers if 'fax' in PRINTER_METADATA[p].get('features', [])]
        if fax_printers and len(fax_printers) < len(available_printers):
            print("\nSua impressora possui função de fax? (sim/não/não sei)")
            while True:
                choice = input("Resposta: ").strip().lower()
                if choice in ['sim', 's', 'yes', 'y']:
                    available_printers = fax_printers
                    break
                elif choice in ['nao', 'não', 'n', 'no']:
                    previous = list(available_printers)
                    filtered = [p for p in available_printers if p not in fax_printers]
                    available_printers = filtered or previous
                    break
                elif choice in ['nao sei', 'não sei', 'ns', 'n/s', '', 'nsei']:
                    break
                else:
                    print("Por favor, responda com 'sim', 'não' ou 'não sei'")
            if len(available_printers) == 1:
                return available_printers[0]
    
    # Pergunta 3.3: Porta Ethernet (rede cabeada)
    if len(available_printers) > 1:
        eth_printers = [p for p in available_printers if 'ethernet' in PRINTER_METADATA[p].get('features', [])]
        if eth_printers and len(eth_printers) < len(available_printers):
            print("\nSua impressora tem porta de rede (Ethernet)? (sim/não/não sei)")
            while True:
                choice = input("Resposta: ").strip().lower()
                if choice in ['sim', 's', 'yes', 'y']:
                    available_printers = eth_printers
                    break
                elif choice in ['nao', 'não', 'n', 'no']:
                    previous = list(available_printers)
                    filtered = [p for p in available_printers if p not in eth_printers]
                    available_printers = filtered or previous
                    break
                elif choice in ['nao sei', 'não sei', 'ns', 'n/s', '', 'nsei']:
                    break
                else:
                    print("Por favor, responda com 'sim', 'não' ou 'não sei'")
            if len(available_printers) == 1:
                return available_printers[0]
    
    # Pergunta 4: Pergunta visual sobre o tamanho/formato
    if len(available_printers) > 1:
        # Agrupa por características visuais aproximadas
        compact_models = ['impressoraL3110', 'impressoraL3150', 'impressoraL375']  # Modelos mais compactos (base)
        larger_models = ['impressoral3250_l3251', 'impressoraL4150', 'impressoraL4260']  # Modelos maiores (base)
        # Heurística: modelos com ADF ou A3 tendem a ser maiores
        for p in available_printers:
            feats = PRINTER_METADATA[p].get('features', [])
            if ('adf' in feats or 'a3' in feats) and p not in larger_models:
                larger_models.append(p)
        
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
                    available_printers = compact_available or available_printers
                    break
                elif choice == '2':
                    available_printers = larger_available or available_printers
                    break
                elif choice == '3':
                    # Se não sabe, mantém todas as opções
                    break
                else:
                    print("Por favor, digite 1, 2 ou 3")
            
            if len(available_printers) == 1:
                return available_printers[0]
    
    # Pergunta 5: Série da impressora (pode ser pulada se usuário não souber)
    if len(available_printers) > 1:
        series = set(PRINTER_METADATA[p]['series'] for p in available_printers if p in PRINTER_METADATA)
        if len(series) > 1:
            print("\nComo última opção, você consegue identificar a série da sua impressora?")
            print("(Geralmente está escrita na frente da impressora)")
            series_list = sorted(list(series))
            for i, serie in enumerate(series_list, 1):
                printers_in_series = [p for p in available_printers if p in PRINTER_METADATA and PRINTER_METADATA[p]['series'] == serie]
                if printers_in_series:
                    example = PRINTER_METADATA[printers_in_series[0]]['full_name']
                    print(f"{i}. Série {serie} (ex: {example})")
                else:
                    print(f"{i}. Série {serie}")
            print(f"{len(series_list) + 1}. Não sei/Não consigo ver")
            
            while True:
                try:
                    choice = int(input(f"Digite o número (1-{len(series_list) + 1}): ").strip())
                    if 1 <= choice <= len(series_list):
                        selected_series = series_list[choice - 1]
                        previous = list(available_printers)
                        filtered = [p for p in available_printers if p in PRINTER_METADATA and PRINTER_METADATA[p]['series'] == selected_series]
                        available_printers = filtered or previous
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
    
    # Se ainda há múltiplas opções, tenta última diferenciação por conectividade Wi-Fi
    if len(available_printers) > 1:
        wifi_printers = [p for p in available_printers if 'wifi' in PRINTER_METADATA[p].get('features', [])]
        if wifi_printers and len(wifi_printers) < len(available_printers):
            print("\nSua impressora tem Wi‑Fi? (sim/não/não sei)")
            while True:
                choice = input("Resposta: ").strip().lower()
                if choice in ['sim', 's', 'yes', 'y']:
                    available_printers = wifi_printers
                    break
                elif choice in ['nao', 'não', 'n', 'no']:
                    previous = list(available_printers)
                    filtered = [p for p in available_printers if p not in wifi_printers]
                    available_printers = filtered or previous
                    break
                elif choice in ['nao sei', 'não sei', 'ns', 'n/s', '', 'nsei']:
                    break
                else:
                    print("Por favor, responda com 'sim', 'não' ou 'não sei'")
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
                metadata = get_printer_metadata_dynamic(model, None)
                print(f"Impressora identificada: {metadata['full_name']}")
                return model
        
        # 2. Busca por similaridade
        similar_printers = find_similar_printers(user_input, 0.6, None)
        
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
                    result_metadata = get_printer_metadata_dynamic(result, None)
                    print(f"Impressora identificada: {result_metadata['full_name']}")
                    return result
        
        # 3. Se não encontrou nada similar, usar sistema de filtragem com todas as impressoras
        if attempt == 0:  # Só faz isso na primeira tentativa
            print("Não consegui identificar a impressora pela sua pergunta.")
            print("\nVocê sabe o modelo da sua impressora?")
            print("1. Sim, sei o modelo")
            print("2. Não sei o modelo")
            choice = input("Digite o número (1-2): ").strip()
            
            if choice in ['nao sei', 'não sei', 'ns', 'n/s', '', 'nsei', '2']:
                print("\nSem problemas! Vou fazer algumas perguntas para identificar sua impressora:")
            elif choice in ['sim', 's', 'yes', 'y', '1']:
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
                similar_printers = find_similar_printers(model_input, 0.6, None)
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
                result_metadata = get_printer_metadata_dynamic(result, None)
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

def check_printer_context(query):
    """Verifica se a pergunta é relacionada a impressoras"""
    try:
        # Prepara o prompt para verificar contexto
        context = """Você é um assistente especializado em identificar se perguntas são relacionadas a impressoras ou não.

ANALISE A SEGUINTE PERGUNTA e responda APENAS com "SIM" ou "NÃO":
- Responda "SIM" se a pergunta é sobre:
  • Impressoras (qualquer marca ou modelo)
  • Problemas de impressão
  • Configuração de impressoras
  • Tintas, cartuchos, papel ou suprimentos
  • Qualidade de impressão
  • Conexão de impressoras (USB, Wi-Fi, rede)
  • Drivers ou software de impressora
  • Manutenção de impressoras
  • Erros de impressão
  • Scanner, cópia ou funções relacionadas a multifuncionais

- Responda "NÃO" se a pergunta é sobre:
  • Assuntos gerais não relacionados a impressoras
  • Outros dispositivos eletrônicos (computadores, celulares, etc)
  • Software não relacionado a impressão
  • Questões pessoais ou conversas gerais
  • Matemática, ciência, história, etc.
  • Programação (exceto se for sobre drivers de impressora)

PERGUNTA: """

        # Chama a API para verificar contexto
        prompt = f"{context}\"{query}\"\n\nResposta (apenas SIM ou NÃO):"
        
        # Rate limiting
        global last_request_time
        current_time = time.time()
        if current_time - last_request_time < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - (current_time - last_request_time))
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.9,
                max_output_tokens=10
            )
        )
        
        # Atualiza tempo da última requisição
        last_request_time = time.time()
        
        # Verifica a resposta
        if response and response.text:
            result = response.text.strip().upper()
            return "SIM" in result
        
        # Se não conseguir determinar, assume que é sobre impressoras para evitar falsos negativos
        return True
        
    except Exception as e:
        print(f"Erro ao verificar contexto: {e}")
        # Em caso de erro, assume que é sobre impressoras para não bloquear o usuário
        return True

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
    """Função principal moderna - ChromaDB exclusivo"""
    
    print("🚀 INICIALIZANDO CHATBOT EPSON MODERNO")
    print("=" * 50)
    
    # Verifica e atualiza ChromaDB automaticamente se necessário
    print("🔍 Verificando atualizações na base de conhecimento...")
    update_result, update_message = auto_update_chromadb_if_needed()
    
    if update_result:
        print("   ✅ Sistema atualizado e pronto!")
    else:
        if "Nenhuma atualização necessária" not in update_message:
            print(f"   ⚠️  {update_message}")
    
    # Inicializa ChromaDB (obrigatório)
    print("🔧 Inicializando sistema ChromaDB...")
    init_chromadb()
    
    # Sincroniza metadados de impressoras do ChromaDB
    print("🔄 Sincronizando modelos de impressoras...")
    sync_printer_metadata_from_chromadb()
    
    # Obtém modelos disponíveis do ChromaDB
    try:
        available_models = chromadb_search.get_available_printer_models()
        print(f"   📱 {len(available_models)} modelos de impressora disponíveis")
    except Exception as e:
        print(f"❌ ERRO ao listar modelos: {e}")
        sys.exit(1)
    
    # Interface moderna
    print("\n" + "=" * 50)
    print("🤖 CHATBOT EPSON - SISTEMA CHROMADB")
    print("✨ Busca semântica inteligente ativa!")
    print("=" * 50)
    
    # Seleção do modo
    print("\n🎯 Escolha o modo de resposta:")
    print("1. 🚀 Modo RÁPIDO - Respostas concisas (3-4 passos)")
    print("2. 📖 Modo DETALHADO - Respostas completas (explicações)")
    
    while True:
        modo_escolha = input("\nEscolha o modo (1 ou 2): ").strip()
        if modo_escolha == '1':
            modo_atual = 'rapido'
            print("✅ Modo RÁPIDO ativado")
            break
        elif modo_escolha == '2':
            modo_atual = 'detalhado'
            print("✅ Modo DETALHADO ativado")
            break
        else:
            print("💡 Digite 1 para rápido ou 2 para detalhado")
    
    print("\n💬 Comandos especiais:")
    print("• 'modo rapido' - Alterna para respostas rápidas")
    print("• 'modo detalhado' - Alterna para respostas completas") 
    print("• 'reload' - Verifica atualizações na base")
    print("• 'sair' - Encerra o programa")
    print("=" * 50)
    
    question_count = 0
    
    while True:
        try:
            # Verifica atualizações a cada 5 perguntas
            if question_count > 0 and question_count % 5 == 0:
                print("\n🔍 Verificando atualizações automáticas...")
                reload_success, reload_msg = reload_knowledge_base_if_updated()
                if reload_success:
                    try:
                        available_models = chromadb_search.get_available_printer_models()
                    except Exception:
                        available_models = []
            
            query = input("\nSua pergunta: ").strip()
            
            # Comandos especiais
            if query.lower() in ['sair', 'exit', 'quit']:
                print("\n👋 Até logo!")
                break
            elif query.lower() == 'modo rapido':
                modo_atual = 'rapido'
                print("✅ Alterado para modo RÁPIDO")
                continue
            elif query.lower() == 'modo detalhado':
                modo_atual = 'detalhado'
                print("✅ Alterado para modo DETALHADO")
                continue
            elif query.lower() == 'reload':
                print("🔄 Verificando atualizações...")
                upd_success, upd_msg = auto_update_chromadb_if_needed()
                print(f"   {upd_msg}")
                try:
                    available_models = chromadb_search.get_available_printer_models()
                    print(f"   📱 {len(available_models)} modelos disponíveis")
                except Exception:
                    available_models = []
                continue
            
            if not query or len(query) < 3:
                print("💡 Digite uma pergunta mais específica (mínimo 3 caracteres)")
                continue
            
            # Sistema inteligente de detecção de impressora
            printer_model = smart_printer_detection(query, available_models, max_attempts=3)
            if not printer_model:
                break
            
            # Busca exclusivamente no ChromaDB
            printer_name = get_printer_metadata_dynamic(printer_model, None)['full_name']
            print(f"\n🔍 Buscando informações para: {printer_name}")
            
            # Busca semântica no ChromaDB
            manual_sections = enhanced_search_chromadb(query, printer_model)
            
            # Processa resultados da busca ChromaDB
            if manual_sections:
                show_search_details(manual_sections)
                
                # Rate limiting
                can_req, msg = can_make_request()
                if not can_req:
                    print(f"{msg}")
                    continue
                
                # Gera resposta
                modo_texto = "RÁPIDA" if modo_atual == 'rapido' else "DETALHADA"
                print(f"🤖 Gerando resposta {modo_texto}...")
                
                success, response = call_api_detailed(query, manual_sections, modo_atual, printer_model)
                
                if success:
                    print(f"\n📋 RESPOSTA {modo_texto}:")
                    print("=" * 50)
                    formatted_response = format_response(response)
                    print(formatted_response)
                    print(f"\n📚 Fonte: {len(manual_sections)} seção(ões) do manual oficial")
                else:
                    print(f"❌ {response}")
            else:
                print("❌ Nenhuma informação relevante encontrada")
                print("💡 Dicas:")
                print("   • Tente reformular sua pergunta")
                print("   • Use termos mais específicos")
                print("   • Verifique se o modelo da impressora está correto")
            
            question_count += 1
            
        except KeyboardInterrupt:
            print("\n\n👋 Encerrando chatbot...")
            break
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            print("🔄 Continuando...")

if __name__ == "__main__":
    main()