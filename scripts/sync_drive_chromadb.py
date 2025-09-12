#!/usr/bin/env python3
"""
Sincronização Direta Google Drive → ChromaDB
===========================================

Script manual para sincronizar PDFs do Google Drive diretamente com ChromaDB,
detectando adições, remoções e modificações sem usar JSON intermediário.

Características:
- Detecção automática de mudanças no Drive
- Sincronização direta sem JSON intermediário
- Sem fallback em caso de erro
- Atualização incremental eficiente
- Log detalhado das operações

Uso:
    python3 sync_drive_chromadb.py

Requisitos:
    - ChromaDB funcionando
    - Credenciais do Google Drive (core/key.json)
    - Dependências: google-api-python-client, chromadb, sentence-transformers
"""

import os
import sys
import json
import hashlib
import io
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

# Adiciona paths do projeto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / "core"))
sys.path.append(str(PROJECT_ROOT / "scripts"))

# Google Drive imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ChromaDB imports
import chromadb
from sentence_transformers import SentenceTransformer

# Imports locais
from extract_pdf_complete import process_pdf_to_sections, get_pdf_hash
from migrate_to_chromadb import (
    get_model_type, 
    apply_document_prefix,
    RECOMMENDED_MODELS
)

# Configurações
DRIVE_FOLDER_ID = "1B-Xsgvy4W392yfLP4ilrzrtl8zzmEgTl"
CREDENTIALS_PATH = PROJECT_ROOT / "core" / "key.json"
CHROMADB_PATH = PROJECT_ROOT / "chromadb_storage"
COLLECTION_NAME = "epson_manuals"
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
BATCH_SIZE = 128
TEMP_DIR = PROJECT_ROOT / "temp_sync"

class DriveChromaSync:
    """Classe principal para sincronização Drive → ChromaDB"""
    
    def __init__(self):
        self.drive_service = None
        self.chromadb_client = None
        self.collection = None
        self.embedding_model = None
        self.model_type = None
        
        # Estatísticas da operação
        self.stats = {
            'pdfs_found': 0,
            'pdfs_added': 0,
            'pdfs_updated': 0,
            'pdfs_removed': 0,
            'pdfs_skipped': 0,  # PDFs não modificados (downloads evitados)
            'sections_added': 0,
            'sections_updated': 0,
            'sections_removed': 0,
            'errors': []
        }
        
        print("Inicializando sincronização direta Drive → ChromaDB")
        self._setup()
    
    def _setup(self):
        """Configura todos os serviços necessários"""
        print("\nConfigurando serviços...")
        
        # Cria diretório temporário
        TEMP_DIR.mkdir(exist_ok=True)
        
        # Configura Google Drive
        self._setup_drive()
        
        # Configura ChromaDB
        self._setup_chromadb()
        
        # Carrega modelo de embedding
        self._setup_embedding_model()
        
        print("Configuração concluída!")
    
    def _setup_drive(self):
        """Configura serviço do Google Drive"""
        print("Configurando Google Drive...")
        
        if not CREDENTIALS_PATH.exists():
            raise FileNotFoundError(f"Credenciais não encontradas: {CREDENTIALS_PATH}")
        
        credentials = service_account.Credentials.from_service_account_file(
            str(CREDENTIALS_PATH),
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        
        self.drive_service = build('drive', 'v3', credentials=credentials)
        print("Google Drive configurado")
    
    def _setup_chromadb(self):
        """Configura ChromaDB"""
        print("Configurando ChromaDB...")
        
        CHROMADB_PATH.mkdir(exist_ok=True)
        
        self.chromadb_client = chromadb.PersistentClient(path=str(CHROMADB_PATH))
        
        try:
            # Tenta obter coleção existente
            self.collection = self.chromadb_client.get_collection(COLLECTION_NAME)
            print(f"Coleção '{COLLECTION_NAME}' encontrada")
        except Exception:
            # Cria nova coleção se não existir
            print(f"Criando nova coleção '{COLLECTION_NAME}'")
            self.collection = self.chromadb_client.create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "Manuais Epson - Sincronização Direta"}
            )
            print("Coleção criada")
    
    def _setup_embedding_model(self):
        """Carrega modelo de embedding"""
        print(f"Carregando modelo de embedding: {EMBEDDING_MODEL}")
        
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.model_type = get_model_type(EMBEDDING_MODEL)
        
        if self.model_type != "standard":
            print(f"Modelo {self.model_type.upper()} detectado - prefixos automáticos ativados")
        
        print("Modelo carregado")
    
    def get_drive_pdfs(self) -> List[Dict]:
        """Lista todos os PDFs no Google Drive"""
        print(f"\nListando PDFs no Drive (pasta: {DRIVE_FOLDER_ID})...")
        
        try:
            query = f"'{DRIVE_FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
            results = self.drive_service.files().list(
                q=query,
                fields="files(id,name,modifiedTime,md5Checksum,size)"
            ).execute()
            
            pdfs = results.get('files', [])
            self.stats['pdfs_found'] = len(pdfs)
            
            print(f"Encontrados {len(pdfs)} PDFs no Drive")
            
            for pdf in pdfs:
                hash_info = f" - Hash: {pdf.get('md5Checksum', 'N/A')[:8]}..." if pdf.get('md5Checksum') else ""
                print(f"   {pdf['name']} ({pdf.get('size', '?')} bytes){hash_info}")
            
            return pdfs
            
        except Exception as e:
            error_msg = f"Erro ao listar PDFs do Drive: {e}"
            print(f"Erro: {error_msg}")
            self.stats['errors'].append(error_msg)
            return []
    
    def get_chromadb_state(self) -> Dict[str, Dict]:
        """Obtém estado atual do ChromaDB (PDFs e seus hashes)"""
        print("\nVerificando estado atual do ChromaDB...")
        
        try:
            # Busca todos os documentos para verificar estado atual
            results = self.collection.get(
                include=['metadatas']
            )
            
            chromadb_state = {}
            
            if results['metadatas']:
                for metadata in results['metadatas']:
                    printer_model = metadata.get('printer_model')
                    pdf_hash = metadata.get('pdf_hash')
                    
                    if printer_model and pdf_hash:
                        if printer_model not in chromadb_state:
                            chromadb_state[printer_model] = {
                                'pdf_hash': pdf_hash,
                                'section_count': 0
                            }
                        chromadb_state[printer_model]['section_count'] += 1
            
            print(f"ChromaDB contém {len(chromadb_state)} modelos:")
            for model, info in chromadb_state.items():
                print(f"   {model}: {info['section_count']} seções (hash: {info['pdf_hash'][:8]}...)")
            
            return chromadb_state
            
        except Exception as e:
            error_msg = f"Erro ao verificar estado do ChromaDB: {e}"
            print(f"Erro: {error_msg}")
            self.stats['errors'].append(error_msg)
            return {}
    
    def extract_model_from_filename(self, filename: str) -> str:
        """Extrai modelo da impressora do nome do arquivo"""
        # Remove extensão e caracteres especiais
        base = os.path.splitext(filename)[0]
        base = re.sub(r'[^\w]', '', base.lower())
        
        # Mapeia nomes conhecidos
        model_mapping = {
            'impressoral805': 'impressoraL805',
            'impressoral1300': 'impressoraL1300', 
            'impressoral3110': 'impressoraL3110',
            'impressoral3150': 'impressoraL3150',
            'impressoral3250l3251': 'impressoraL3250_L3251',
            'impressoral375': 'impressoraL375',
            'impressoral396': 'impressoraL396',
            'impressoral4150': 'impressoraL4150',
            'impressoral4260': 'impressoraL4260',
            'impressoral5190': 'impressoraL5190',
            'impressoral5290': 'impressoraL5290',
            'impressoral6490': 'impressoraL6490'
        }
        
        return model_mapping.get(base, base)
    
    def download_pdf(self, pdf_info: Dict) -> Optional[Path]:
        """Baixa PDF do Drive para processamento temporário"""
        pdf_name = pdf_info['name']
        pdf_id = pdf_info['id']
        
        # Nome seguro para arquivo local
        safe_name = re.sub(r'[^\w\-_\.]', '_', pdf_name)
        local_path = TEMP_DIR / safe_name
        
        print(f"Baixando: {pdf_name}")
        
        try:
            request = self.drive_service.files().get_media(fileId=pdf_id)
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            # Salva arquivo
            with open(local_path, 'wb') as f:
                f.write(file_io.getvalue())
            
            print(f"Baixado: {local_path}")
            return local_path
            
        except Exception as e:
            error_msg = f"Erro ao baixar {pdf_name}: {e}"
            print(f"Erro: {error_msg}")
            self.stats['errors'].append(error_msg)
            return None
    
    def calculate_pdf_hash(self, pdf_path: Path) -> str:
        """Calcula hash MD5 do PDF"""
        return get_pdf_hash(str(pdf_path))
    
    def remove_model_from_chromadb(self, printer_model: str):
        """Remove todas as seções de um modelo do ChromaDB"""
        print(f"Removendo modelo {printer_model} do ChromaDB...")
        
        try:
            # Busca IDs de todas as seções do modelo
            results = self.collection.get(
                where={"printer_model": printer_model},
                include=['metadatas']
            )
            
            if results['ids']:
                # Remove seções
                self.collection.delete(ids=results['ids'])
                removed_count = len(results['ids'])
                
                print(f"Removidas {removed_count} seções do modelo {printer_model}")
                self.stats['sections_removed'] += removed_count
                
                return True
            else:
                print(f"Nenhuma seção encontrada para {printer_model}")
                return False
                
        except Exception as e:
            error_msg = f"Erro ao remover {printer_model}: {e}"
            print(f"Erro: {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
    
    def process_and_insert_pdf(self, pdf_path: Path, printer_model: str, drive_hash: str = None) -> bool:
        """Processa PDF e insere seções no ChromaDB"""
        print(f"Processando PDF: {printer_model}")
        
        try:
            # Processa PDF em seções
            sections = process_pdf_to_sections(str(pdf_path), printer_model=printer_model)
            
            if not sections:
                print(f"Nenhuma seção extraída de {printer_model}")
                return False
            
            print(f"Extraídas {len(sections)} seções")
            
            # Usa hash do Drive se fornecido, senão usa o hash das seções
            pdf_hash = drive_hash if drive_hash else sections[0].get('pdf_hash', '')
            
            # Prepara dados para inserção
            ids = []
            documents = []
            metadatas = []
            
            for section in sections:
                # ID único
                section_id = f"{printer_model}_{section['id']}"
                ids.append(section_id)
                
                # Texto combinado para embedding
                text_content = f"{section['title']} {section['content']}"
                documents.append(text_content)
                
                # Metadados
                metadata = {
                    'printer_model': printer_model,
                    'title': section['title'],
                    'type': section.get('type', 'geral'),
                    'keywords': ','.join(section.get('keywords', [])),
                    'pdf_hash': pdf_hash,  # Usa hash otimizado
                    'model_type': self.model_type,
                    'model_name': EMBEDDING_MODEL
                }
                metadatas.append(metadata)
            
            # Processa em batches
            for i in range(0, len(sections), BATCH_SIZE):
                batch_end = min(i + BATCH_SIZE, len(sections))
                
                batch_ids = ids[i:batch_end]
                batch_docs = documents[i:batch_end]
                batch_metas = metadatas[i:batch_end]
                
                # Aplica prefixos para documentos se necessário
                docs_with_prefix = apply_document_prefix(batch_docs, self.model_type)
                
                # Gera embeddings
                print(f"🧠 Gerando embeddings para batch {i//BATCH_SIZE + 1}")
                embeddings = self.embedding_model.encode(
                    docs_with_prefix, 
                    normalize_embeddings=True, 
                    show_progress_bar=False
                ).tolist()
                
                # Insere no ChromaDB
                self.collection.add(
                    ids=batch_ids,
                    documents=batch_docs,  # Documentos originais
                    metadatas=batch_metas,
                    embeddings=embeddings
                )
                
                print(f"Inseridas {len(batch_ids)} seções")
            
            self.stats['sections_added'] += len(sections)
            print(f"Modelo {printer_model} processado com sucesso!")
            return True
            
        except Exception as e:
            error_msg = f"Erro ao processar {printer_model}: {e}"
            print(f"Erro: {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
    
    def sync(self):
        """Executa sincronização completa"""
        print("\nINICIANDO SINCRONIZAÇÃO")
        print("=" * 50)
        
        start_time = datetime.now()
        
        try:
            # 1. Lista PDFs no Drive
            drive_pdfs = self.get_drive_pdfs()
            if not drive_pdfs:
                print("❌ Nenhum PDF encontrado no Drive ou erro na listagem")
                return False
            
            # 2. Verifica estado atual do ChromaDB
            chromadb_state = self.get_chromadb_state()
            
            # 3. Mapeia PDFs do Drive por modelo
            drive_models = {}
            for pdf in drive_pdfs:
                model = self.extract_model_from_filename(pdf['name'])
                drive_models[model] = pdf
            
            print(f"\nANÁLISE DE MUDANÇAS:")
            print(f"   Drive: {len(drive_models)} modelos")
            print(f"   ChromaDB: {len(chromadb_state)} modelos")
            
            # 4. Identifica mudanças necessárias
            models_to_add = set(drive_models.keys()) - set(chromadb_state.keys())
            models_to_remove = set(chromadb_state.keys()) - set(drive_models.keys())
            models_to_check = set(drive_models.keys()) & set(chromadb_state.keys())
            
            print(f"\nPLANO DE SINCRONIZAÇÃO:")
            print(f"   Adicionar: {len(models_to_add)} modelos")
            print(f"   Remover: {len(models_to_remove)} modelos") 
            print(f"   Verificar: {len(models_to_check)} modelos")
            
            if models_to_add:
                print(f"      Novos: {', '.join(models_to_add)}")
            if models_to_remove:
                print(f"      Remover: {', '.join(models_to_remove)}")
            
            # 5. Remove modelos que não existem mais no Drive
            for model in models_to_remove:
                if self.remove_model_from_chromadb(model):
                    self.stats['pdfs_removed'] += 1
            
            # 6. Processa modelos novos
            for model in models_to_add:
                pdf_info = drive_models[model]
                
                # Baixa PDF
                pdf_path = self.download_pdf(pdf_info)
                if not pdf_path:
                    continue
                
                # Processa e insere (usa hash do Drive se disponível)
                drive_hash = pdf_info.get('md5Checksum')
                if self.process_and_insert_pdf(pdf_path, model, drive_hash):
                    self.stats['pdfs_added'] += 1
                
                # Remove arquivo temporário
                pdf_path.unlink(missing_ok=True)
            
            # 7. Verifica modelos existentes por mudanças (usando hash do Drive - sem download)
            for model in models_to_check:
                pdf_info = drive_models[model]
                current_state = chromadb_state[model]
                
                # Usa hash MD5 do Google Drive (evita download desnecessário)
                drive_hash = pdf_info.get('md5Checksum', '')
                stored_hash = current_state['pdf_hash']
                
                if drive_hash and drive_hash != stored_hash:
                    print(f"PDF modificado detectado: {model}")
                    print(f"   Hash Drive: {drive_hash[:8]}...")
                    print(f"   Hash armazenado: {stored_hash[:8]}...")
                    
                    # Baixa apenas PDFs modificados
                    pdf_path = self.download_pdf(pdf_info)
                    if not pdf_path:
                        continue
                    
                    # Remove versão antiga
                    if self.remove_model_from_chromadb(model):
                        # Insere versão nova
                        if self.process_and_insert_pdf(pdf_path, model, drive_hash):
                            self.stats['pdfs_updated'] += 1
                    
                    # Remove arquivo temporário
                    pdf_path.unlink(missing_ok=True)
                elif drive_hash:
                    print(f"{model} não modificado (hash: {drive_hash[:8]}...)")
                    self.stats['pdfs_skipped'] += 1
                else:
                    # Fallback: se Drive não fornecer hash, baixa para verificar
                    print(f"Hash não disponível no Drive para {model}, verificando localmente...")
                    pdf_path = self.download_pdf(pdf_info)
                    if not pdf_path:
                        continue
                    
                    current_hash = self.calculate_pdf_hash(pdf_path)
                    
                    if current_hash != stored_hash:
                        print(f"PDF modificado detectado: {model}")
                        print(f"   Hash atual: {current_hash[:8]}...")
                        print(f"   Hash armazenado: {stored_hash[:8]}...")
                        
                        # Remove versão antiga
                        if self.remove_model_from_chromadb(model):
                            # Insere versão nova
                            if self.process_and_insert_pdf(pdf_path, model, current_hash):
                                self.stats['pdfs_updated'] += 1
                    else:
                        print(f"{model} não modificado")
                        self.stats['pdfs_skipped'] += 1
                    
                    # Remove arquivo temporário
                    pdf_path.unlink(missing_ok=True)
            
            # 8. Salva log da sincronização
            self._save_sync_log()
            
            return True
            
        except Exception as e:
            error_msg = f"Erro durante sincronização: {e}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
        
        finally:
            # Limpa arquivos temporários
            if TEMP_DIR.exists():
                for temp_file in TEMP_DIR.glob("*"):
                    temp_file.unlink(missing_ok=True)
                TEMP_DIR.rmdir()
            
            # Mostra estatísticas finais
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("\n" + "=" * 50)
            print("ESTATÍSTICAS DA SINCRONIZAÇÃO")
            print("=" * 50)
            print(f"Duração: {duration}")
            print(f"PDFs encontrados no Drive: {self.stats['pdfs_found']}")
            print(f"PDFs adicionados: {self.stats['pdfs_added']}")
            print(f"PDFs atualizados: {self.stats['pdfs_updated']}")
            print(f"PDFs removidos: {self.stats['pdfs_removed']}")
            print(f"PDFs não modificados (ignorados): {self.stats['pdfs_skipped']}")
            print(f"Seções adicionadas: {self.stats['sections_added']}")
            print(f"Seções removidas: {self.stats['sections_removed']}")
            
            if self.stats['errors']:
                print(f"Erros: {len(self.stats['errors'])}")
                for error in self.stats['errors']:
                    print(f"   • {error}")
            else:
                print("Nenhum erro encontrado")
            
            print("=" * 50)
    
    def _save_sync_log(self):
        """Salva log detalhado da sincronização"""
        log_path = PROJECT_ROOT / "data" / "sync_log.json"
        log_path.parent.mkdir(exist_ok=True)
        
        log_data = {
            "sync_date": datetime.now().isoformat(),
            "sync_type": "direct_drive_chromadb",
            "statistics": self.stats,
            "configuration": {
                "drive_folder_id": DRIVE_FOLDER_ID,
                "chromadb_path": str(CHROMADB_PATH),
                "collection_name": COLLECTION_NAME,
                "embedding_model": EMBEDDING_MODEL,
                "batch_size": BATCH_SIZE
            }
        }
        
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            print(f"Log salvo: {log_path}")
        except Exception as e:
            print(f"Erro ao salvar log: {e}")


def main():
    """Função principal"""
    print("SINCRONIZAÇÃO DIRETA GOOGLE DRIVE → CHROMADB")
    print("=" * 60)
    print("Este script sincroniza PDFs do Google Drive diretamente com ChromaDB")
    print("sem usar arquivos JSON intermediários.")
    print()
    
    # Verifica dependências
    print("Verificando dependências...")
    
    required_files = [
        CREDENTIALS_PATH,
        PROJECT_ROOT / "core" / "extract_pdf_complete.py",
        PROJECT_ROOT / "scripts" / "migrate_to_chromadb.py"
    ]
    
    missing_files = [f for f in required_files if not f.exists()]
    if missing_files:
        print("Arquivos necessários não encontrados:")
        for f in missing_files:
            print(f"   • {f}")
        return False
    
    try:
        # Cria instância e executa sincronização
        syncer = DriveChromaSync()
        success = syncer.sync()
        
        if success:
            print("\nSINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!")
            return True
        else:
            print("\nSINCRONIZAÇÃO FALHOU")
            return False
            
    except KeyboardInterrupt:
        print("\nSincronização interrompida pelo usuário")
        return False
    except Exception as e:
        print(f"\nErro fatal: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

