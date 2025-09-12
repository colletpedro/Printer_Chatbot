#!/usr/bin/env python3
"""
Migração direta do Google Drive para ChromaDB (sem JSON intermediário)

Fluxo:
 1) Lista PDFs no Drive
 2) Baixa/atualiza cópias locais em pdfs_downloaded/
 3) Extrai seções com metadados (printer_model, pdf_hash, etc.)
 4) Recria a coleção no ChromaDB e insere embeddings

Uso:
  python3 scripts/migrate_from_drive_to_chromadb.py \
    --folder-id <FOLDER_ID> \
    --db ./chromadb_storage \
    --collection epson_manuals \
    --model-preset multilingual-e5-base

Requisitos:
  - google-api-python-client, google-auth, google-auth-oauthlib, google-auth-httplib2
  - chromadb, sentence-transformers, torch
"""

import argparse
import os
import re
import sys
import io
import json
from datetime import datetime

# Garante import dos módulos locais do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# Google Drive
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Extração de seções dos PDFs
from core.extract_pdf_complete import process_pdf_to_sections

# Reuso de funções do migrador para ChromaDB
from scripts.migrate_to_chromadb import (
    RECOMMENDED_MODELS,
    get_model_type,
    process_items,
    create_chromadb_collection,
    insert_embeddings,
    save_migration_log,
)


def sanitize_filename(filename: str) -> str:
    return re.sub(r'[\\/<>:"|?*]', '_', filename)


def extract_model_from_filename(filename: str) -> str:
    base = os.path.basename(filename)
    return re.sub(r'\.pdf$', '', base, flags=re.IGNORECASE)


def get_drive_service(credentials_file: str):
    creds = service_account.Credentials.from_service_account_file(
        credentials_file,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    return build('drive', 'v3', credentials=creds)


def list_pdfs_in_folder(service, folder_id: str):
    results = service.files().list(
        q=f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false",
        fields="files(id, name, modifiedTime)",
        pageSize=200
    ).execute()
    return results.get('files', [])


def download_pdf(service, file_id: str, dest_path: str):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    request = service.files().get_media(fileId=file_id)
    with io.FileIO(dest_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()


def build_items_from_pdfs(pdfs_dir: str):
    items = []
    for name in sorted(os.listdir(pdfs_dir)):
        if not name.lower().endswith('.pdf'):
            continue
        pdf_path = os.path.join(pdfs_dir, name)
        model = extract_model_from_filename(name)
        sections = process_pdf_to_sections(pdf_path, printer_model=model)
        # sections já possuem: id, title, content, type, keywords, printer_model, pdf_hash
        items.extend(sections)
    return items


def main():
    parser = argparse.ArgumentParser(
        description="Migração direta do Google Drive para ChromaDB (sem JSON)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Entradas do Drive/Projeto
    parser.add_argument('--folder-id', default='1B-Xsgvy4W392yfLP4ilrzrtl8zzmEgTl',
                        help='ID da pasta no Google Drive contendo os PDFs')
    parser.add_argument('--credentials', default=os.path.join(PROJECT_ROOT, 'core', 'key.json'),
                        help='Caminho do arquivo de credenciais de serviço do Google')

    # Saída local dos PDFs
    parser.add_argument('--pdfs-dir', default=os.path.join(PROJECT_ROOT, 'pdfs_downloaded'),
                        help='Diretório local para armazenar os PDFs baixados')

    # Configurações do ChromaDB / modelo
    parser.add_argument('--db', default=os.path.join(PROJECT_ROOT, 'chromadb_storage'),
                        help='Diretório para o banco ChromaDB')
    parser.add_argument('--collection', default='epson_manuals',
                        help='Nome da coleção no ChromaDB')
    parser.add_argument('--model-preset', choices=list(RECOMMENDED_MODELS.keys()),
                        default='multilingual-e5-base',
                        help='Preset de modelo de embeddings')
    parser.add_argument('--model', help='Modelo customizado (overrides preset)')
    parser.add_argument('--batch', type=int, help='Tamanho do batch para inserção')

    args = parser.parse_args()

    print('🚀 MIGRAÇÃO DIRETA: Google Drive → ChromaDB (sem JSON)')
    print('=' * 60)

    # 1) Conecta ao Drive
    print('🔐 Autenticando no Google Drive...')
    service = get_drive_service(args.credentials)

    # 2) Lista e baixa PDFs
    print('📂 Listando PDFs na pasta do Drive...')
    pdf_files = list_pdfs_in_folder(service, args.folder_id)
    print(f'   • Encontrados {len(pdf_files)} PDFs')

    for pdf in pdf_files:
        safe_name = sanitize_filename(pdf['name'])
        dest_path = os.path.join(args.pdfs_dir, safe_name)
        print(f"⬇️  Baixando/atualizando: {pdf['name']} → {safe_name}")
        download_pdf(service, pdf['id'], dest_path)

    # 3) Extrai seções a partir dos PDFs locais
    print('🧩 Extraindo seções dos PDFs...')
    items = build_items_from_pdfs(args.pdfs_dir)
    print(f'   • Total de seções extraídas: {len(items)}')

    if not items:
        print('❌ Nenhuma seção extraída. Abortando migração.')
        sys.exit(1)

    # 4) Processa items e injeta no ChromaDB
    # Configuração de modelo
    if args.model:
        model_name = args.model
        batch_size = args.batch or 128
    else:
        preset = RECOMMENDED_MODELS[args.model_preset]
        model_name = preset['name']
        batch_size = args.batch or preset['batch_size']

    print('⚙️  Preparando itens para ChromaDB...')
    processed_items = process_items(items)
    if not processed_items:
        print('❌ Nenhum item válido após processamento. Abortando.')
        sys.exit(1)

    client, collection = create_chromadb_collection(args.db, args.collection)
    insert_embeddings(collection, processed_items, model_name, batch_size)

    # 5) Log
    stats = {
        'total_items': len(items),
        'migrated_items': len(processed_items),
        'model_used': model_name,
        'batch_size': batch_size,
        'source': 'google_drive_pdfs',
        'migration_type': 'direct_no_json',
        'date': datetime.now().isoformat(),
    }
    save_migration_log(args.db, args.collection, stats)

    print('\n' + '=' * 60)
    print('✅ CHROMADB ATUALIZADO DIRETAMENTE A PARTIR DO GOOGLE DRIVE!')
    print(f"🗄️  Banco: {args.db}")
    print(f"📁 Coleção: {args.collection}")


if __name__ == '__main__':
    main()


