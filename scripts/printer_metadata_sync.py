#!/usr/bin/env python3
"""
Sistema de sincronização automática de metadados de impressoras.
Garante que TODOS os modelos no ChromaDB sejam reconhecidos pelo chatbot.
"""

import chromadb
from collections import defaultdict
import re

def get_all_printer_models_from_chromadb(chromadb_path="./chromadb_storage", 
                                         collection_name="epson_manuals"):
    """
    Obtém todos os modelos de impressora únicos do ChromaDB.
    
    Returns:
        dict: Dicionário com modelo como chave e contagem de seções como valor
    """
    try:
        client = chromadb.PersistentClient(path=chromadb_path)
        collection = client.get_collection(name=collection_name)
        
        # Pega todos os metadados
        all_data = collection.get(include=['metadatas'])
        
        # Agrupa por modelo
        models = defaultdict(int)
        for metadata in all_data['metadatas']:
            if metadata and 'printer_model' in metadata:
                model = metadata['printer_model']
                models[model] += 1
        
        return dict(models)
    except Exception as e:
        print(f"Erro ao obter modelos do ChromaDB: {e}")
        return {}

def generate_printer_metadata(model_key):
    """
    Gera metadados automáticos para um modelo de impressora baseado no nome.
    
    Args:
        model_key: Chave do modelo (ex: 'impressoraL396')
    
    Returns:
        dict: Metadados gerados automaticamente
    """
    # Remove prefixos comuns
    base_name = model_key.replace('impressora', '').replace('Impressora', '').replace('imoresora', '')
    
    # Extrai número do modelo
    match = re.search(r'[lL]?(\d+)', base_name)
    model_number = match.group(1) if match else ''
    
    # Nome completo formatado
    if model_number:
        full_name = f'Epson L{model_number}'
        # Se tem underscore, é modelo duplo
        if '_' in base_name:
            parts = base_name.split('_')
            numbers = [re.search(r'\d+', p).group() for p in parts if re.search(r'\d+', p)]
            full_name = f'Epson L{"/L".join(numbers)}'
    else:
        full_name = f'Epson {base_name.upper()}'
    
    # Gera aliases inteligentes
    aliases = []
    if model_number:
        aliases.extend([
            f'l{model_number}',
            f'{model_number}',
            f'l {model_number}',
            f'epson l{model_number}',
            f'epson {model_number}'
        ])
        # Se tem dois números (ex: L3250/L3251)
        if '_' in base_name:
            parts = base_name.split('_')
            for part in parts:
                num = re.search(r'\d+', part)
                if num:
                    aliases.extend([
                        f'l{num.group()}',
                        f'{num.group()}',
                        f'epson l{num.group()}'
                    ])
    
    # Remove duplicatas e converte para lowercase
    aliases = list(set([a.lower() for a in aliases]))
    
    # Detecta características baseadas no número do modelo
    features = ['ecotank', 'tanque']  # Todas têm tanque de tinta
    
    if model_number:
        num = int(model_number[:1])  # Primeiro dígito indica série
        
        # Série L3000+ geralmente são multifuncionais
        if num >= 3:
            features.append('multifuncional')
            features.append('wifi')
        
        # Série L4000+ geralmente têm duplex
        if num >= 4:
            features.append('duplex')
        
        # Série L5000+ geralmente têm ADF
        if num >= 5:
            features.append('adf')
        
        # Série L6000+ são top de linha
        if num >= 6:
            features.append('fax')
        
        # L1300 é A3
        if model_number == '1300':
            features.append('a3')
    
    # Determina série
    series = 'L1000'  # padrão
    if model_number:
        first_digit = model_number[0]
        series = f'L{first_digit}000'
    
    # Gera descrição
    feature_desc = []
    if 'multifuncional' in features:
        feature_desc.append('Multifuncional')
    if 'a3' in features:
        feature_desc.append('formato A3')
    if 'duplex' in features:
        feature_desc.append('impressão duplex')
    if 'adf' in features:
        feature_desc.append('ADF')
    if 'fax' in features:
        feature_desc.append('fax')
    
    if feature_desc:
        description = f'Impressora colorida com sistema EcoTank, {", ".join(feature_desc)}'
    else:
        description = 'Impressora colorida com sistema EcoTank'
    
    return {
        'full_name': full_name,
        'aliases': aliases,
        'type': 'colorida',
        'features': features,
        'series': series,
        'description': description
    }

def build_complete_printer_metadata():
    """
    Constrói um dicionário completo de metadados para TODAS as impressoras no ChromaDB.
    
    Returns:
        dict: Dicionário completo de metadados
    """
    # Obtém todos os modelos do ChromaDB
    chromadb_models = get_all_printer_models_from_chromadb()
    
    if not chromadb_models:
        print("⚠️ Nenhum modelo encontrado no ChromaDB")
        return {}
    
    print(f"📊 {len(chromadb_models)} modelos encontrados no ChromaDB")
    
    # Gera metadados para cada modelo
    complete_metadata = {}
    for model_key in chromadb_models:
        metadata = generate_printer_metadata(model_key)
        complete_metadata[model_key] = metadata
        print(f"  ✅ {model_key} → {metadata['full_name']}")
    
    return complete_metadata

if __name__ == "__main__":
    # Teste do sistema
    metadata = build_complete_printer_metadata()
    
    print("\n📋 Metadados gerados:")
    for key, data in metadata.items():
        print(f"\n{key}:")
        print(f"  Nome: {data['full_name']}")
        print(f"  Aliases: {', '.join(data['aliases'][:5])}...")
        print(f"  Features: {', '.join(data['features'])}")
        print(f"  Série: {data['series']}")
