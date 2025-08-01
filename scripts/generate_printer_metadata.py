#!/usr/bin/env python3
"""
Gerador Automático de Metadados de Impressoras
Analisa a base de conhecimento e gera/atualiza automaticamente os metadados das impressoras
"""

import json
import re
import os
from datetime import datetime
from collections import Counter

def load_knowledge_base():
    """Carrega a base de conhecimento"""
    try:
        # Caminho correto para o arquivo
        manual_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'manual_complete.json')
        with open(manual_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['sections']
    except FileNotFoundError:
        print("❌ Arquivo manual_complete.json não encontrado")
        return None
    except Exception as e:
        print(f"❌ Erro ao carregar base: {e}")
        return None

def extract_printer_features(sections, printer_model):
    """Extrai características de uma impressora específica das seções"""
    features = set()
    content_combined = ""
    
    # Combina todo o conteúdo relacionado à impressora
    for section in sections:
        if section.get('printer_model') == printer_model:
            content_combined += " " + section.get('content', '').lower()
            content_combined += " " + section.get('title', '').lower()
    
    # Detecta características baseado no conteúdo
    feature_keywords = {
        'multifuncional': ['multifuncional', 'multifunction', 'scanner', 'copia', 'digitalizar'],
        'wifi': ['wifi', 'wi-fi', 'wireless', 'sem fio', 'rede'],
        'ecotank': ['ecotank', 'eco tank', 'tanque', 'tank'],
        'duplex': ['duplex', 'frente e verso', 'dois lados', 'automatic duplex'],
        'adf': ['adf', 'alimentador', 'automatic document feeder', 'alimentador automatico'],
        'ethernet': ['ethernet', 'cabo de rede', 'lan'],
        'usb': ['usb', 'cabo usb'],
        'mobile': ['mobile', 'smartphone', 'android', 'ios', 'app'],
        'cloud': ['cloud', 'nuvem', 'google drive', 'dropbox', 'onedrive']
    }
    
    for feature, keywords in feature_keywords.items():
        if any(keyword in content_combined for keyword in keywords):
            features.add(feature)
    
    return list(features)

def detect_printer_type(sections, printer_model):
    """Detecta se a impressora é colorida ou monocromática"""
    content_combined = ""
    
    for section in sections:
        if section.get('printer_model') == printer_model:
            content_combined += " " + section.get('content', '').lower()
    
    # Palavras que indicam impressão colorida
    color_keywords = ['colorida', 'color', 'cores', 'ciano', 'magenta', 'amarelo', 'cyan', 'yellow']
    mono_keywords = ['monocromatica', 'preto e branco', 'mono', 'black only']
    
    color_count = sum(content_combined.count(keyword) for keyword in color_keywords)
    mono_count = sum(content_combined.count(keyword) for keyword in mono_keywords)
    
    # Se encontrou mais referências a cor, considera colorida
    if color_count > mono_count:
        return 'colorida'
    elif mono_count > 0:
        return 'monocromatica'
    else:
        # Padrão para impressoras Epson modernas
        return 'colorida'

def generate_printer_aliases(model_name):
    """Gera aliases automáticos para um modelo de impressora"""
    aliases = []
    
    # Remove 'impressora' do nome se presente
    model_clean = model_name.replace('impressora', '').replace('Impressora', '')
    
    # Extrai número do modelo (ex: L4260, L3250, etc.)
    model_match = re.search(r'L?\d{4,5}', model_clean)
    if model_match:
        model_num = model_match.group()
        
        # Variações do número do modelo
        aliases.extend([
            model_num.lower(),
            model_num.upper(),
            f'l {model_num[-4:]}',
            f'L {model_num[-4:]}',
            f'epson {model_num.lower()}',
            f'epson {model_num.upper()}',
            f'Epson {model_num.upper()}'
        ])
        
        # Para modelos duplos como L3250_L3251
        if '_' in model_clean:
            parts = model_clean.split('_')
            for part in parts:
                part_match = re.search(r'L?\d{4,5}', part)
                if part_match:
                    part_num = part_match.group()
                    aliases.extend([
                        part_num.lower(),
                        part_num.upper(),
                        f'epson {part_num.lower()}',
                        f'epson {part_num.upper()}'
                    ])
    
    # Remove duplicatas e ordena
    return sorted(list(set(aliases)))

def determine_printer_series(model_name):
    """Determina a série da impressora baseado no modelo"""
    model_upper = model_name.upper()
    
    if 'L1' in model_upper:
        return 'L1000'
    elif 'L2' in model_upper:
        return 'L2000'
    elif 'L3' in model_upper:
        return 'L3000'
    elif 'L4' in model_upper:
        return 'L4000'
    elif 'L5' in model_upper:
        return 'L5000'
    elif 'L6' in model_upper:
        return 'L6000'
    else:
        return 'Unknown'

def generate_printer_description(model_name, printer_type, features):
    """Gera descrição automática da impressora"""
    model_clean = model_name.replace('impressora', '').upper()
    
    # Termos base
    base_desc = f"Impressora"
    
    # Adiciona tipo
    if printer_type == 'colorida':
        base_desc += " multifuncional colorida"
    else:
        base_desc += " monocromática"
    
    # Adiciona características principais
    feature_descriptions = []
    if 'ecotank' in features:
        feature_descriptions.append("sistema EcoTank")
    if 'duplex' in features:
        feature_descriptions.append("impressão duplex")
    if 'adf' in features:
        feature_descriptions.append("ADF")
    if 'wifi' in features:
        feature_descriptions.append("Wi-Fi")
    
    if feature_descriptions:
        base_desc += f" com {', '.join(feature_descriptions)}"
    
    return f"Epson {model_clean} - {base_desc}"

def generate_metadata_for_model(sections, printer_model):
    """Gera metadados completos para um modelo específico"""
    
    # Extrai informações
    features = extract_printer_features(sections, printer_model)
    printer_type = detect_printer_type(sections, printer_model)
    aliases = generate_printer_aliases(printer_model)
    series = determine_printer_series(printer_model)
    description = generate_printer_description(printer_model, printer_type, features)
    
    # Nome amigável
    model_clean = printer_model.replace('impressora', '').upper()
    full_name = f"Epson {model_clean}"
    
    metadata = {
        'full_name': full_name,
        'aliases': aliases,
        'type': printer_type,
        'features': features,
        'series': series,
        'description': description,
        'auto_generated': True,
        'generated_at': datetime.now().isoformat()
    }
    
    return metadata

def load_existing_metadata():
    """Carrega metadados existentes do chatbot.py"""
    try:
        # Caminho correto para o arquivo
        chatbot_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'chatbot.py')
        with open(chatbot_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extrai o dicionário PRINTER_METADATA usando regex
        pattern = r'PRINTER_METADATA\s*=\s*\{(.*?)\}'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            # Isso é uma simplificação - em produção usaria AST
            print("⚠️  Metadados existentes encontrados no chatbot.py")
            print("   (Para evitar conflitos, manteremos separados)")
            return True
        return False
        
    except Exception as e:
        print(f"⚠️  Erro ao ler metadados existentes: {e}")
        return False

def save_metadata_to_file(all_metadata, filename=None):
    if filename is None:
        filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'printer_metadata_generated.json')
    """Salva metadados em arquivo JSON separado"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_models': len(all_metadata),
                'metadata': all_metadata
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Metadados salvos em: {filename}")
        return True, filename
        
    except Exception as e:
        print(f"❌ Erro ao salvar metadados: {e}")
        return False, None

def analyze_coverage(sections, all_metadata):
    """Analisa a cobertura dos metadados gerados"""
    models_in_kb = set()
    for section in sections:
        model = section.get('printer_model', '')
        if model:
            models_in_kb.add(model)
    
    models_with_metadata = set(all_metadata.keys())
    
    print(f"\n📊 Análise de Cobertura:")
    print(f"   • Modelos na base de conhecimento: {len(models_in_kb)}")
    print(f"   • Modelos com metadados gerados: {len(models_with_metadata)}")
    
    missing = models_in_kb - models_with_metadata
    if missing:
        print(f"   • Modelos sem metadados: {len(missing)}")
        for model in sorted(missing):
            print(f"     - {model}")
    else:
        print(f"   ✅ Todos os modelos têm metadados!")

def main():
    """Função principal"""
    print("🤖 Gerador Automático de Metadados de Impressoras")
    print("=" * 60)
    
    # Carrega base de conhecimento
    print("📁 Carregando base de conhecimento...")
    sections = load_knowledge_base()
    if not sections:
        return
    
    # Encontra todos os modelos únicos
    print("🔍 Analisando modelos disponíveis...")
    models = set()
    for section in sections:
        model = section.get('printer_model', '')
        if model:
            models.add(model)
    
    print(f"   Modelos encontrados: {len(models)}")
    for model in sorted(models):
        print(f"   • {model}")
    
    # Verifica metadados existentes
    print("\n🔍 Verificando metadados existentes...")
    has_existing = load_existing_metadata()
    
    # Gera metadados para cada modelo
    print(f"\n⚙️  Gerando metadados para {len(models)} modelos...")
    all_metadata = {}
    
    for model in sorted(models):
        print(f"   🔧 Processando: {model}")
        
        try:
            metadata = generate_metadata_for_model(sections, model)
            all_metadata[model] = metadata
            
            # Mostra preview
            print(f"      Nome: {metadata['full_name']}")
            print(f"      Tipo: {metadata['type']}")
            print(f"      Características: {', '.join(metadata['features'][:3])}{'...' if len(metadata['features']) > 3 else ''}")
            print(f"      Aliases: {len(metadata['aliases'])} variações")
            
        except Exception as e:
            print(f"      ❌ Erro: {e}")
    
    # Salva metadados
    print(f"\n💾 Salvando metadados...")
    success, saved_filename = save_metadata_to_file(all_metadata)
    if success:
        
        # Análise de cobertura
        analyze_coverage(sections, all_metadata)
        
        print(f"\n🎉 Processo concluído!")
        print(f"   • Arquivo gerado: {os.path.basename(saved_filename)}")
        print(f"   • Modelos processados: {len(all_metadata)}")
        
        # Instruções de uso
        print(f"\n📖 Como usar:")
        print(f"   1. Os metadados foram salvos em '{os.path.basename(saved_filename)}'")
        print(f"   2. O chatbot já usa geração automática de metadados")
        print(f"   3. Para novas impressoras, os metadados serão gerados automaticamente")
        
        if has_existing:
            print(f"\n⚠️  Nota: Metadados manuais em chatbot.py serão mantidos como prioritários")

if __name__ == "__main__":
    main() 