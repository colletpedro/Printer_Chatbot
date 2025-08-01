#!/usr/bin/env python3
"""
Script para remover da base de conhecimento (manual_complete.json) 
as seções de PDFs que foram removidos do Google Drive.

Este script deve ser executado MANUALMENTE quando você remove um PDF 
do Drive e quer removê-lo também da base de conhecimento.
"""

import os
import sys
import json
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Adicionar o diretório core ao path para importar funções
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

# CONFIGURAÇÕES
DRIVE_FOLDER_ID = '1B-Xsgvy4W392yfLP4ilrzrtl8zzmEgTl'
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), '..', 'core', 'key.json')
KNOWLEDGE_BASE_JSON = os.path.join(os.path.dirname(__file__), '..', 'data', 'manual_complete.json')

def get_drive_service():
    """Conecta ao Google Drive API"""
    try:
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ Erro ao conectar ao Google Drive: {e}")
        return None

def list_pdfs_in_drive(service):
    """Lista todos os PDFs atualmente no Google Drive"""
    try:
        results = service.files().list(
            q=f"'{DRIVE_FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false",
            fields="files(id, name, modifiedTime)",
            pageSize=100
        ).execute()
        return results.get('files', [])
    except Exception as e:
        print(f"❌ Erro ao listar PDFs do Drive: {e}")
        return []

def extract_model_from_filename(filename):
    """Extrai o modelo do nome do arquivo (mesmo padrão do update_drive.py)"""
    base = os.path.basename(filename)
    model = re.sub(r'\.pdf$', '', base, flags=re.IGNORECASE)
    return model

def sanitize_filename(filename):
    """Remove caracteres inválidos do filename (mesmo padrão do update_drive.py)"""
    return re.sub(r'[\\/<>:"|?*]', '_', filename)

def load_knowledge_base():
    """Carrega a base de conhecimento atual"""
    try:
        if not os.path.exists(KNOWLEDGE_BASE_JSON):
            print(f"❌ Arquivo da base de conhecimento não encontrado: {KNOWLEDGE_BASE_JSON}")
            return None
            
        with open(KNOWLEDGE_BASE_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar base de conhecimento: {e}")
        return None

def save_knowledge_base(data):
    """Salva a base de conhecimento atualizada"""
    try:
        with open(KNOWLEDGE_BASE_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar base de conhecimento: {e}")
        return False

def find_orphaned_sections(knowledge_base, current_drive_models):
    """Identifica seções órfãs (sem PDF correspondente no Drive)"""
    if not knowledge_base or 'sections' not in knowledge_base:
        return {}
    
    orphaned_models = {}
    sections = knowledge_base['sections']
    
    for section in sections:
        if 'printer_model' not in section:
            continue
            
        model = section['printer_model']
        
        # Verifica se o modelo tem PDF correspondente no Drive
        if model not in current_drive_models:
            if model not in orphaned_models:
                orphaned_models[model] = []
            orphaned_models[model].append(section)
    
    return orphaned_models

def display_orphaned_sections(orphaned_models):
    """Exibe as seções órfãs encontradas"""
    if not orphaned_models:
        print("✅ Nenhuma seção órfã encontrada! Todos os modelos na base têm PDFs correspondentes no Drive.")
        return
    
    print("\n📋 SEÇÕES ÓRFÃS ENCONTRADAS:")
    print("="*60)
    
    for model, sections in orphaned_models.items():
        print(f"\n🖨️  Modelo: {model}")
        print(f"   📄 Seções: {len(sections)}")
        
        # Mostra algumas seções como exemplo
        print("   📝 Exemplos de seções:")
        for i, section in enumerate(sections[:3]):  # Mostra só 3 exemplos
            title = section.get('title', 'Sem título')[:50] + '...' if len(section.get('title', '')) > 50 else section.get('title', 'Sem título')
            print(f"      {i+1}. {title}")
        
        if len(sections) > 3:
            print(f"      ... e mais {len(sections) - 3} seções")

def confirm_removal(orphaned_models):
    """Permite ao usuário escolher quais modelos remover"""
    models_to_remove = []
    
    print("\n🤔 ESCOLHA O QUE REMOVER:")
    print("="*60)
    
    for model in orphaned_models.keys():
        while True:
            response = input(f"\n❓ Remover todas as seções do modelo '{model}'? (s/n/info): ").lower().strip()
            
            if response in ['s', 'sim', 'y', 'yes']:
                models_to_remove.append(model)
                print(f"   ✅ Modelo '{model}' marcado para remoção")
                break
            elif response in ['n', 'nao', 'não', 'no']:
                print(f"   ⏭️  Modelo '{model}' será mantido")
                break
            elif response in ['info', 'i']:
                sections = orphaned_models[model]
                print(f"\n   📊 Informações detalhadas do modelo '{model}':")
                print(f"      📄 Total de seções: {len(sections)}")
                print(f"      📝 Títulos das seções:")
                for i, section in enumerate(sections[:10], 1):  # Mostra até 10
                    title = section.get('title', 'Sem título')
                    print(f"         {i}. {title}")
                if len(sections) > 10:
                    print(f"         ... e mais {len(sections) - 10} seções")
                print()
            else:
                print("   ❌ Resposta inválida. Use 's' (sim), 'n' (não) ou 'info' (mais informações)")
    
    return models_to_remove

def remove_sections(knowledge_base, models_to_remove):
    """Remove as seções dos modelos especificados"""
    if not models_to_remove:
        return knowledge_base, 0
    
    original_sections = knowledge_base['sections']
    removed_count = 0
    
    # Filtra seções, mantendo apenas as que NÃO estão na lista de remoção
    new_sections = []
    for section in original_sections:
        if section.get('printer_model') in models_to_remove:
            removed_count += 1
        else:
            new_sections.append(section)
    
    # Atualiza a base de conhecimento
    knowledge_base['sections'] = new_sections
    knowledge_base['manual_info']['total_sections'] = len(new_sections)
    knowledge_base['manual_info']['processed_at'] = __import__('time').strftime('%Y-%m-%d %H:%M:%S')
    
    return knowledge_base, removed_count

def main():
    print("🧹 LIMPEZA DA BASE DE CONHECIMENTO")
    print("="*50)
    print("Este script remove seções de PDFs que não existem mais no Google Drive.\n")
    
    # Conecta ao Google Drive
    print("🔄 Conectando ao Google Drive...")
    service = get_drive_service()
    if not service:
        return
    
    # Lista PDFs atuais no Drive
    print("📁 Listando PDFs atuais no Drive...")
    drive_pdfs = list_pdfs_in_drive(service)
    if not drive_pdfs:
        print("❌ Nenhum PDF encontrado no Drive ou erro ao listar.")
        return
    
    # Extrai modelos dos PDFs do Drive
    current_drive_models = set()
    print(f"\n📋 PDFs encontrados no Drive ({len(drive_pdfs)}):")
    for pdf in drive_pdfs:
        safe_name = sanitize_filename(pdf['name'])
        model = extract_model_from_filename(safe_name)
        current_drive_models.add(model)
        print(f"   📄 {pdf['name']} → {model}")
    
    # Carrega base de conhecimento
    print(f"\n📖 Carregando base de conhecimento...")
    knowledge_base = load_knowledge_base()
    if not knowledge_base:
        return
    
    total_sections = len(knowledge_base.get('sections', []))
    print(f"   ✅ {total_sections} seções carregadas")
    
    # Identifica seções órfãs
    print(f"\n🔍 Procurando seções órfãs...")
    orphaned_models = find_orphaned_sections(knowledge_base, current_drive_models)
    
    # Mostra resultado
    display_orphaned_sections(orphaned_models)
    
    if not orphaned_models:
        return
    
    # Pergunta ao usuário o que remover
    models_to_remove = confirm_removal(orphaned_models)
    
    if not models_to_remove:
        print("\n⏭️  Nenhum modelo selecionado para remoção. Saindo...")
        return
    
    # Confirmação final
    total_sections_to_remove = sum(len(orphaned_models[model]) for model in models_to_remove)
    print(f"\n⚠️  CONFIRMAÇÃO FINAL:")
    print(f"   🗑️  Modelos a remover: {', '.join(models_to_remove)}")
    print(f"   📄 Total de seções a remover: {total_sections_to_remove}")
    print(f"   📊 Seções restantes: {total_sections - total_sections_to_remove}")
    
    confirm = input(f"\n❓ Confirma a remoção? Esta ação NÃO PODE ser desfeita! (digite 'CONFIRMO'): ")
    
    if confirm != 'CONFIRMO':
        print("\n❌ Remoção cancelada. Nenhuma alteração foi feita.")
        return
    
    # Remove seções
    print(f"\n🗑️  Removendo seções...")
    updated_knowledge_base, removed_count = remove_sections(knowledge_base, models_to_remove)
    
    # Salva base atualizada
    print(f"💾 Salvando base de conhecimento atualizada...")
    if save_knowledge_base(updated_knowledge_base):
        print(f"\n✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
        print(f"   🗑️  Seções removidas: {removed_count}")
        print(f"   📄 Seções restantes: {len(updated_knowledge_base['sections'])}")
        print(f"   📁 Arquivo atualizado: {KNOWLEDGE_BASE_JSON}")
        
        # Restart sugerido
        print(f"\n💡 RECOMENDAÇÃO:")
        print(f"   🔄 Reinicie o chatbot para que ele carregue a base atualizada")
        print(f"   📝 As seções removidas não estarão mais disponíveis nas consultas")
    else:
        print(f"\n❌ Erro ao salvar a base de conhecimento!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Operação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}") 