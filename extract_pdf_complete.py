#!/usr/bin/env python3
"""
Extrator PDF Completo - Para manual de 200 páginas
"""

import PyPDF2
import json
import re
import time
from collections import defaultdict

def extract_pdf_text(pdf_path):
    """Extrai texto completo do PDF"""
    print(f"📖 Extraindo texto de {pdf_path}...")
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)
            print(f"📄 Total de páginas: {total_pages}")
            
            text = ""
            for i, page in enumerate(reader.pages, 1):
                if i % 20 == 0:
                    print(f"   Processando página {i}/{total_pages}...")
                try:
                    page_text = page.extract_text()
                    text += f"\n--- PÁGINA {i} ---\n{page_text}\n"
                except:
                    print(f"   ⚠️ Erro na página {i}, pulando...")
                    
            return text
    except Exception as e:
        print(f"❌ Erro ao ler PDF: {e}")
        return None

def clean_text(text):
    """Limpa texto"""
    text = re.sub(r'\n\s*\n', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    return text.strip()

def identify_section_type(text):
    """Identifica tipo de seção"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['problema', 'erro', 'solução', 'não funciona']):
        return 'solução_problemas'
    elif any(word in text_lower for word in ['papel', 'carregamento', 'bandeja']):
        return 'papel'
    elif any(word in text_lower for word in ['cartucho', 'tinta', 'toner']):
        return 'cartuchos'
    elif any(word in text_lower for word in ['wifi', 'wireless', 'rede']):
        return 'conectividade'
    elif any(word in text_lower for word in ['configurar', 'setup', 'instalar']):
        return 'configuração'
    else:
        return 'geral'

def extract_meaningful_chunks(text, chunk_size=600):
    """Divide em chunks"""
    pages = text.split('--- PÁGINA')
    chunks = []
    current_chunk = ""
    
    for page_content in pages[1:]:
        lines = page_content.split('\n')[1:]  # Pula número da página
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if len(current_chunk + line) > chunk_size:
                if len(current_chunk) > 50:
                    chunks.append({
                        'content': clean_text(current_chunk),
                        'type': identify_section_type(current_chunk)
                    })
                current_chunk = line + " "
            else:
                current_chunk += line + " "
    
    if len(current_chunk) > 50:
        chunks.append({
            'content': clean_text(current_chunk),
            'type': identify_section_type(current_chunk)
        })
    
    return chunks

def extract_keywords(text):
    """Extrai keywords"""
    keywords = []
    text_lower = text.lower()
    
    # Palavras-chave mais abrangentes
    keyword_map = {
        # Problemas e soluções
        'problema': ['problema', 'erro', 'error', 'falha', 'não funciona', 'preso', 'travado'],
        'solução': ['solução', 'resolver', 'solucionar', 'corrigir'],
        
        # Papel e alimentação
        'papel': ['papel', 'paper', 'folha', 'bandeja', 'tray', 'carregamento', 'alimentar'],
        'carregar': ['carregar', 'colocar', 'inserir', 'load'],
        
        # Cartuchos e tinta
        'cartucho': ['cartucho', 'cartridge', 'substituir', 'trocar', 'instalar'],
        'tinta': ['tinta', 'ink', 'nível', 'recarregar', 'refill'],
        
        # Conectividade
        'wifi': ['wifi', 'wi-fi', 'wireless', 'sem fio', 'rede'],
        'conectar': ['conectar', 'connect', 'conexão', 'configurar'],
        'rede': ['rede', 'network', 'ethernet', 'internet'],
        
        # Configuração
        'configurar': ['configurar', 'config', 'setup', 'instalar', 'instalação'],
        'driver': ['driver', 'software', 'programa'],
        
        # Impressão
        'imprimir': ['imprimir', 'print', 'impressão', 'printing'],
        'qualidade': ['qualidade', 'quality', 'resolução', 'dpi'],
        'duplex': ['duplex', 'dois lados', 'frente e verso', 'frente', 'verso'],
        
        # Cópia e digitalização
        'cópia': ['cópia', 'copy', 'copiar', 'cópia'],
        'digitalizar': ['digitalizar', 'scan', 'scanner', 'digitalização'],
        
        # Limpeza e manutenção
        'limpar': ['limpar', 'clean', 'limpeza', 'cleaning'],
        'manutenção': ['manutenção', 'maintenance', 'cuidado', 'conservação'],
        'cabeçote': ['cabeçote', 'cabeça', 'printhead', 'head'],
        
        # Interface
        'painel': ['painel', 'panel', 'botão', 'button', 'display'],
        'menu': ['menu', 'opção', 'configuração', 'setting']
    }
    
    # Mapeia todas as variações para a palavra-chave principal
    for main_keyword, variations in keyword_map.items():
        for variation in variations:
            if variation in text_lower:
                keywords.append(main_keyword)
                break  # Evita duplicatas da mesma categoria
    
    return list(set(keywords))  # Remove duplicatas

def create_title(content, section_type):
    """Cria título baseado no conteúdo"""
    content_lower = content.lower()
    
    if section_type == 'papel':
        if 'carregar' in content_lower:
            return "Como Carregar Papel"
        else:
            return "Configuração de Papel"
    elif section_type == 'cartuchos':
        if 'trocar' in content_lower:
            return "Como Trocar Cartuchos"
        else:
            return "Gerenciamento de Cartuchos"
    elif section_type == 'conectividade':
        return "Configuração de Rede"
    elif section_type == 'solução_problemas':
        return "Solução de Problemas"
    else:
        words = content.split()[:8]
        return f"Seção: {' '.join(words)[:50]}..."

def main():
    pdf_path = "impressora.pdf"
    
    print("🚀 PROCESSANDO PDF COMPLETO")
    print("=" * 50)
    
    # Extrai texto
    raw_text = extract_pdf_text(pdf_path)
    if not raw_text:
        return
    
    print(f"📝 {len(raw_text):,} caracteres extraídos")
    
    # Cria chunks
    chunks = extract_meaningful_chunks(raw_text)
    print(f"📑 {len(chunks)} chunks criados")
    
    # Organiza por tipo
    by_type = defaultdict(list)
    for chunk in chunks:
        by_type[chunk['type']].append(chunk)
    
    # Seleciona os melhores de cada tipo
    final_sections = []
    for section_type in ['solução_problemas', 'papel', 'cartuchos', 'conectividade', 'configuração', 'geral']:
        type_chunks = by_type[section_type][:20]  # Max 20 por tipo
        
        for i, chunk in enumerate(type_chunks):
            section = {
                'id': f'{section_type}_{i}',
                'title': create_title(chunk['content'], section_type),
                'content': chunk['content'][:800],
                'type': section_type,
                'keywords': extract_keywords(chunk['content'])
            }
            final_sections.append(section)
    
    # Salva resultado
    output = {
        'manual_info': {
            'source': pdf_path,
            'total_sections': len(final_sections),
            'processed_at': time.strftime('%Y-%m-%d %H:%M:%S')
        },
        'sections': final_sections[:80]  # Limita a 80 seções
    }
    
    with open('manual_complete.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {len(output['sections'])} seções salvas em manual_complete.json")
    
    # Stats
    type_counts = defaultdict(int)
    for section in output['sections']:
        type_counts[section['type']] += 1
    
    print("\n📊 Por categoria:")
    for stype, count in type_counts.items():
        print(f"   {stype}: {count}")

if __name__ == "__main__":
    main()
