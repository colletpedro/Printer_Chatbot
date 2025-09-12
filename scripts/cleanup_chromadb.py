#!/usr/bin/env python3
"""
Script para remover do ChromaDB as seções de PDFs que foram removidos do Google Drive.

Este script trabalha DIRETAMENTE com o ChromaDB, garantindo que os dados
sejam permanentemente removidos da base de dados vetorial.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

# Adicionar o diretório core ao path para importar funções
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / "core"))
sys.path.append(str(PROJECT_ROOT / "scripts"))

# Google Drive imports
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ChromaDB imports
import chromadb
from sentence_transformers import SentenceTransformer

# CONFIGURAÇÕES
DRIVE_FOLDER_ID = '1B-Xsgvy4W392yfLP4ilrzrtl8zzmEgTl'
CREDENTIALS_FILE = PROJECT_ROOT / "core" / "key.json"
CHROMADB_PATH = PROJECT_ROOT / "chromadb_storage"
COLLECTION_NAME = "epson_manuals"
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"

def get_drive_service():
    """Conecta ao Google Drive API"""
    try:
        creds = service_account.Credentials.from_service_account_file(
            str(CREDENTIALS_FILE),
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
    """Extrai o modelo do nome do arquivo"""
    base = os.path.basename(filename)
    model = re.sub(r'\.pdf$', '', base, flags=re.IGNORECASE)
    # Remove espaços mas mantém a capitalização original
    # para corresponder com o formato no ChromaDB
    model = re.sub(r'\s+', '', model)
    return model

def get_chromadb_client():
    """Conecta ao ChromaDB"""
    try:
        client = chromadb.PersistentClient(path=str(CHROMADB_PATH))
        return client
    except Exception as e:
        print(f"❌ Erro ao conectar ao ChromaDB: {e}")
        return None

def get_models_in_chromadb(collection):
    """Lista todos os modelos únicos no ChromaDB"""
    try:
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
        print(f"❌ Erro ao listar modelos no ChromaDB: {e}")
        return {}

def find_orphaned_models(chromadb_models, drive_models):
    """Identifica modelos órfãos (existem no ChromaDB mas não no Drive)"""
    orphaned = {}
    
    # Cria um set com os modelos do Drive em minúsculas para comparação
    drive_models_lower = {m.lower() for m in drive_models}
    
    for model, count in chromadb_models.items():
        # Compara ignorando maiúsculas/minúsculas
        if model.lower() not in drive_models_lower:
            orphaned[model] = count
    
    return orphaned

def display_orphaned_models(orphaned_models):
    """Exibe os modelos órfãos encontrados"""
    if not orphaned_models:
        print("\n✅ Nenhum modelo órfão encontrado!")
        print("   A base ChromaDB está sincronizada com o Google Drive.")
        return
    
    print(f"\n📋 MODELOS ÓRFÃOS ENCONTRADOS NO CHROMADB:")
    print("="*60)
    
    total_sections = 0
    for i, (model, count) in enumerate(orphaned_models.items(), 1):
        print(f"\n🖨️  {i}. Modelo: {model}")
        print(f"   📄 Seções no ChromaDB: {count}")
        total_sections += count
    
    print(f"\n📊 RESUMO:")
    print(f"   • Modelos órfãos: {len(orphaned_models)}")
    print(f"   • Total de seções órfãs: {total_sections}")

def confirm_removal(orphaned_models):
    """Pergunta ao usuário quais modelos remover"""
    print(f"\n🤔 ESCOLHA O QUE REMOVER:")
    print("="*60)
    
    models_to_remove = []
    
    for model, count in orphaned_models.items():
        print(f"\n❓ Remover todas as {count} seções do modelo '{model}'? (s/n): ", end='')
        response = input().strip().lower()
        
        if response == 's':
            models_to_remove.append(model)
            print(f"   ✅ Marcado para remoção")
        else:
            print(f"   ⏭️  Mantendo o modelo")
    
    return models_to_remove

def remove_from_chromadb(collection, models_to_remove):
    """Remove os modelos do ChromaDB"""
    total_removed = 0
    
    for model in models_to_remove:
        try:
            # Busca todos os IDs com este modelo
            results = collection.get(
                where={"printer_model": model},
                include=['metadatas']
            )
            
            if results['ids']:
                # Remove todos os documentos deste modelo
                collection.delete(ids=results['ids'])
                removed_count = len(results['ids'])
                total_removed += removed_count
                print(f"   ✅ Removidas {removed_count} seções do modelo '{model}'")
            else:
                print(f"   ⚠️  Nenhuma seção encontrada para o modelo '{model}'")
                
        except Exception as e:
            print(f"   ❌ Erro ao remover modelo '{model}': {e}")
    
    return total_removed

def verify_removal(collection, models_removed):
    """Verifica se a remoção foi bem-sucedida"""
    print(f"\n🔍 Verificando remoção...")
    
    all_success = True
    for model in models_removed:
        results = collection.get(
            where={"printer_model": model},
            limit=1
        )
        
        if results['ids']:
            print(f"   ❌ Modelo '{model}' ainda tem {len(results['ids'])} seções!")
            all_success = False
        else:
            print(f"   ✅ Modelo '{model}' removido completamente")
    
    return all_success

def main():
    print("🧹 LIMPEZA DO CHROMADB - REMOÇÃO PERMANENTE")
    print("="*60)
    print("Este script remove PERMANENTEMENTE do ChromaDB as seções")
    print("de PDFs que não existem mais no Google Drive.\n")
    
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
        model = extract_model_from_filename(pdf['name'])
        current_drive_models.add(model)
        print(f"   📄 {pdf['name']} → {model}")
    
    # Conecta ao ChromaDB
    print(f"\n🔌 Conectando ao ChromaDB...")
    client = get_chromadb_client()
    if not client:
        return
    
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
        print(f"   ✅ Coleção '{COLLECTION_NAME}' carregada")
    except Exception as e:
        print(f"❌ Erro ao carregar coleção: {e}")
        return
    
    # Lista modelos no ChromaDB
    print(f"\n📊 Analisando ChromaDB...")
    chromadb_models = get_models_in_chromadb(collection)
    
    if not chromadb_models:
        print("⚠️  ChromaDB vazio ou erro ao listar modelos.")
        return
    
    print(f"   ✅ {len(chromadb_models)} modelos encontrados no ChromaDB")
    for model, count in chromadb_models.items():
        print(f"      • {model}: {count} seções")
    
    # Identifica modelos órfãos
    print(f"\n🔍 Procurando modelos órfãos...")
    orphaned_models = find_orphaned_models(chromadb_models, current_drive_models)
    
    # Mostra resultado
    display_orphaned_models(orphaned_models)
    
    if not orphaned_models:
        return
    
    # Pergunta ao usuário o que remover
    models_to_remove = confirm_removal(orphaned_models)
    
    if not models_to_remove:
        print("\n⏭️  Nenhum modelo selecionado para remoção. Saindo...")
        return
    
    # Confirmação final
    total_sections_to_remove = sum(orphaned_models[model] for model in models_to_remove)
    total_sections_current = sum(chromadb_models.values())
    
    print(f"\n⚠️  CONFIRMAÇÃO FINAL:")
    print(f"   🗑️  Modelos a remover: {', '.join(models_to_remove)}")
    print(f"   📄 Total de seções a remover: {total_sections_to_remove}")
    print(f"   📊 Seções atuais no ChromaDB: {total_sections_current}")
    print(f"   📊 Seções após remoção: {total_sections_current - total_sections_to_remove}")
    
    confirm = input(f"\n❓ Confirma a remoção PERMANENTE do ChromaDB? (digite 'CONFIRMO'): ")
    
    if confirm != 'CONFIRMO':
        print("\n❌ Remoção cancelada. Nenhuma alteração foi feita.")
        return
    
    # Remove do ChromaDB
    print(f"\n🗑️  Removendo do ChromaDB...")
    removed_count = remove_from_chromadb(collection, models_to_remove)
    
    # Verifica se a remoção foi bem-sucedida
    if verify_removal(collection, models_to_remove):
        print(f"\n✅ LIMPEZA DO CHROMADB CONCLUÍDA COM SUCESSO!")
        print(f"   🗑️  Seções removidas permanentemente: {removed_count}")
        print(f"   📄 Seções restantes: {total_sections_current - removed_count}")
        print(f"   💾 Base ChromaDB atualizada em: {CHROMADB_PATH}")
        
        # Recomendações
        print(f"\n💡 RECOMENDAÇÕES:")
        print(f"   🔄 O chatbot já estará usando a base atualizada")
        print(f"   📝 As seções removidas não estarão mais disponíveis")
        print(f"   🚀 Não é necessário reiniciar o chatbot")
    else:
        print(f"\n⚠️  Algumas remoções podem ter falhado. Verifique os logs acima.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Operação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
