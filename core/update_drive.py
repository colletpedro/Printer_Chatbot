#!/usr/bin/env python3
"""
Atualiza a base de conhecimento (manual_complete.json) baixando PDFs do Google Drive e processando cada um.
"""
import sys
import os
# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))
import json
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from extract_pdf_complete import process_pdf_to_sections, get_pdf_hash

# CONFIGURAÇÕES

DRIVE_FOLDER_ID = '1B-Xsgvy4W392yfLP4ilrzrtl8zzmEgTl'
# Caminhos baseados na localização do script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, 'key.json')
OUTPUT_JSON = os.path.join(PROJECT_ROOT, 'data', 'manual_complete.json')
DOWNLOAD_DIR = os.path.join(PROJECT_ROOT, 'pdfs_downloaded')

# Autenticação Google Drive
def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    return build('drive', 'v3', credentials=creds)

def list_pdfs_in_folder(service, folder_id):
    results = service.files().list(
        q=f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false",
        fields="files(id, name, modifiedTime)",
        pageSize=100
    ).execute()
    return results.get('files', [])

def download_pdf(service, file_id, filename):
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(filename, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.close()

def extract_model_from_filename(filename):
    # Exemplo: impressora2.pdf -> impressora2
    base = os.path.basename(filename)
    model = re.sub(r'\.pdf$', '', base, flags=re.IGNORECASE)
    return model

def sanitize_filename(filename):
    # Substitui /, \, e outros caracteres inválidos por _
    return re.sub(r'[\\/<>:"|?*]', '_', filename)

def load_existing_json():
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_json(data):
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    service = get_drive_service()
    pdf_files = list_pdfs_in_folder(service, DRIVE_FOLDER_ID)
    print(f"Encontrados {len(pdf_files)} PDFs na pasta do Drive.")

    # Carrega base existente
    existing = load_existing_json()
    existing_sections = existing['sections'] if existing else []
    existing_hashes = {s['printer_model']: s['pdf_hash'] for s in existing_sections if 'printer_model' in s and 'pdf_hash' in s}
    new_sections = []
    updated_models = set()

    for pdf in pdf_files:
        pdf_name = pdf['name']
        pdf_id = pdf['id']
        safe_pdf_name = sanitize_filename(pdf_name)
        local_path = os.path.join(DOWNLOAD_DIR, safe_pdf_name)
        print(f"\nProcessando: {pdf_name}")
        # Baixar PDF
        download_pdf(service, pdf_id, local_path)
        # Extrair modelo
        model = extract_model_from_filename(safe_pdf_name)
        # Calcular hash
        pdf_hash = get_pdf_hash(local_path)
        # Verificar se já existe e se mudou
        if model in existing_hashes and existing_hashes[model] == pdf_hash:
            print(f"  - PDF não mudou, mantendo seções existentes.")
            # Manter seções antigas
            new_sections.extend([s for s in existing_sections if s.get('printer_model') == model])
        else:
            print(f"  - PDF novo ou alterado, processando...")
            sections = process_pdf_to_sections(local_path, printer_model=model)
            new_sections.extend(sections)
            updated_models.add(model)

    # Adicionar seções de modelos não atualizados
    for s in existing_sections:
        if s.get('printer_model') not in updated_models and s.get('printer_model') not in [extract_model_from_filename(sanitize_filename(pdf['name'])) for pdf in pdf_files]:
            new_sections.append(s)

    # Atualizar metadados
    output = {
        'manual_info': {
            'source': f"Google Drive folder {DRIVE_FOLDER_ID}",
            'total_sections': len(new_sections),
            'processed_at': __import__('time').strftime('%Y-%m-%d %H:%M:%S')
        },
        'sections': new_sections
    }
    save_json(output)
    print(f"\n✅ Base de conhecimento atualizada com {len(new_sections)} seções.")
    print(f"Modelos processados: {', '.join(updated_models) if updated_models else 'Nenhum novo.'}")

if __name__ == "__main__":
    main() 