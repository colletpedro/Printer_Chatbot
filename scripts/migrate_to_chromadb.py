#!/usr/bin/env python3
"""
Script de migração da base de conhecimento JSON para ChromaDB
Customizado para o projeto GeminiMGI - Sistema de Chatbot Epson

Uso:
    python scripts/migrate_to_chromadb.py --json data/manual_complete.json
    
Funcionalidades:
- Combina title + content para busca semântica mais rica
- Preserva metadados específicos do projeto (printer_model, type, keywords, etc.)
- Validação de dados antes da inserção
- Processamento em batches otimizado
- Modelo de embeddings otimizado para português
"""

import argparse
import json
import uuid
import os
import sys
from datetime import datetime
import chromadb
from sentence_transformers import SentenceTransformer

# Configurações de modelos otimizados
RECOMMENDED_MODELS = {
    "multilingual-e5-small": {
        "name": "intfloat/multilingual-e5-small",
        "type": "e5",
        "description": "E5 Small - Rápido e eficiente para PT-BR",
        "batch_size": 256
    },
    "multilingual-e5-base": {
        "name": "intfloat/multilingual-e5-base", 
        "type": "e5",
        "description": "E5 Base - Melhor qualidade para PT-BR",
        "batch_size": 128
    },
    "bge-m3": {
        "name": "BAAI/bge-m3",
        "type": "bge",
        "description": "BGE-M3 - Estado da arte, suporte multimodal",
        "batch_size": 64
    },
    "paraphrase-multilingual": {
        "name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "type": "standard",
        "description": "MiniLM Multilingual - Padrão confiável",
        "batch_size": 128
    }
}

def get_model_type(model_name):
    """Detecta o tipo de modelo baseado no nome para aplicar prefixos corretos"""
    model_name_lower = model_name.lower()
    
    if "e5" in model_name_lower and "multilingual" in model_name_lower:
        return "e5"
    elif "bge" in model_name_lower:
        return "bge" 
    else:
        return "standard"

def apply_document_prefix(documents, model_type):
    """Aplica prefixos apropriados para documentos baseado no tipo de modelo"""
    if model_type == "e5":
        return [f"passage: {doc}" for doc in documents]
    elif model_type == "bge":
        return [f"passage: {doc}" for doc in documents]  # BGE também usa passage:
    else:
        return documents  # Modelos padrão não precisam de prefixo

def apply_query_prefix(query, model_type):
    """Aplica prefixos apropriados para consultas baseado no tipo de modelo"""
    if model_type == "e5":
        return f"query: {query}"
    elif model_type == "bge":
        return f"query: {query}"
    else:
        return query  # Modelos padrão não precisam de prefixo

def validate_item(item):
    """Valida se o item tem os campos obrigatórios"""
    required_fields = ["id", "printer_model"]
    missing_fields = [field for field in required_fields if not item.get(field)]
    
    if missing_fields:
        print(f"⚠️  Item {item.get('id', 'SEM_ID')} ignorado - campos obrigatórios ausentes: {missing_fields}")
        return False
    
    # Verifica se tem pelo menos title ou content
    if not item.get("title") and not item.get("content"):
        print(f"⚠️  Item {item['id']} ignorado - sem title nem content")
        return False
    
    return True

def prepare_text_content(item):
    """Combina title e content para busca semântica mais rica"""
    title = item.get("title", "").strip()
    content = item.get("content", "").strip()
    
    if title and content:
        # Limpa o title de caracteres especiais e repetições
        title_clean = title.replace("Seção: ", "").strip()
        if len(title_clean) > 100:
            title_clean = title_clean[:100] + "..."
        
        return f"TÍTULO: {title_clean}\n\nCONTEÚDO: {content}"
    elif title:
        return f"TÍTULO: {title}"
    elif content:
        return content
    else:
        return ""

def prepare_metadata(item):
    """Prepara metadados preservando campos específicos do projeto"""
    metadata = {
        "printer_model": item.get("printer_model"),
        "type": item.get("type", "geral"),
        "pdf_hash": item.get("pdf_hash"),
        "original_title": item.get("title", ""),
    }
    
    # Adiciona keywords como string (ChromaDB não aceita listas)
    keywords = item.get("keywords", [])
    if keywords:
        # Converte lista para string separada por vírgulas
        metadata["keywords"] = ", ".join(str(k) for k in keywords) if isinstance(keywords, list) else str(keywords)
    
    # Remove campos vazios
    metadata = {k: v for k, v in metadata.items() if v is not None and v != ""}
    
    return metadata

def load_knowledge_base(json_path):
    """Carrega a base de conhecimento do arquivo JSON"""
    print(f"📁 Carregando {json_path}...")
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Estrutura específica do projeto: {"manual_info": {...}, "sections": [...]}
        if isinstance(data, dict) and "sections" in data:
            items = data["sections"]
            manual_info = data.get("manual_info", {})
            
            print(f"📊 Informações do manual:")
            print(f"   • Fonte: {manual_info.get('source', 'N/A')}")
            print(f"   • Total de seções: {manual_info.get('total_sections', len(items))}")
            print(f"   • Processado em: {manual_info.get('processed_at', 'N/A')}")
            
        elif isinstance(data, list):
            items = data
        else:
            raise ValueError("Formato JSON não reconhecido. Esperado: {'sections': [...]} ou lista direta")
        
        print(f"✅ {len(items)} itens carregados do arquivo")
        return items
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo não encontrado: {json_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Erro ao decodificar JSON: {e}")

def process_items(items):
    """Processa e valida os itens para inserção no ChromaDB"""
    print("🔍 Processando e validando itens...")
    
    processed_items = []
    stats = {
        "total": len(items),
        "valid": 0,
        "invalid": 0,
        "printers": set(),
        "types": set()
    }
    
    for item in items:
        if not validate_item(item):
            stats["invalid"] += 1
            continue
        
        # Prepara o texto combinado
        text_content = prepare_text_content(item)
        if not text_content.strip():
            print(f"⚠️  Item {item['id']} ignorado - conteúdo de texto vazio")
            stats["invalid"] += 1
            continue
        
        # Prepara metadados
        metadata = prepare_metadata(item)
        
        processed_item = {
            "id": item["id"],
            "text": text_content,
            "metadata": metadata
        }
        
        processed_items.append(processed_item)
        stats["valid"] += 1
        stats["printers"].add(item["printer_model"])
        stats["types"].add(item.get("type", "geral"))
    
    print(f"📈 Estatísticas do processamento:")
    print(f"   • Itens válidos: {stats['valid']}/{stats['total']}")
    print(f"   • Itens inválidos: {stats['invalid']}")
    print(f"   • Modelos de impressora: {len(stats['printers'])}")
    print(f"   • Tipos de conteúdo: {sorted(stats['types'])}")
    print(f"   • Impressoras: {sorted(stats['printers'])}")
    
    return processed_items

def create_chromadb_collection(db_path, collection_name):
    """Cria ou obtém a coleção do ChromaDB"""
    print(f"🗄️  Inicializando ChromaDB em {db_path}...")
    
    # Cria o diretório se não existir
    os.makedirs(db_path, exist_ok=True)
    
    client = chromadb.PersistentClient(path=db_path)
    
    # Remove coleção existente se houver
    try:
        client.delete_collection(name=collection_name)
        print(f"🗑️  Coleção existente '{collection_name}' removida")
    except (ValueError, Exception) as e:
        # Coleção não existia ou outro erro - isso é normal na primeira execução
        if "does not exist" in str(e) or "not found" in str(e).lower():
            print(f"💡 Coleção '{collection_name}' não existia (primeira execução)")
        else:
            print(f"⚠️  Aviso ao remover coleção: {e}")
    
    # Cria nova coleção
    collection = client.create_collection(name=collection_name)
    print(f"✅ Coleção '{collection_name}' criada com sucesso")
    
    return client, collection

def insert_embeddings(collection, items, model_name, batch_size):
    """Insere os itens com embeddings na coleção"""
    print(f"🤖 Carregando modelo {model_name}...")
    model = SentenceTransformer(model_name)
    
    # Detecta tipo de modelo para aplicar prefixos
    model_type = get_model_type(model_name)
    if model_type != "standard":
        print(f"🏷️  Modelo {model_type.upper()} detectado - aplicando prefixos automáticos")
    
    print(f"📝 Inserindo {len(items)} itens em batches de {batch_size}...")
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        
        # Prepara dados do batch
        ids = [item["id"] for item in batch]
        documents = [item["text"] for item in batch]
        metadatas = [item["metadata"] for item in batch]
        
        # Aplica prefixos apropriados para documentos
        documents_with_prefix = apply_document_prefix(documents, model_type)
        
        # Gera embeddings com os documentos prefixados
        print(f"🔄 Processando batch {i//batch_size + 1}/{(len(items)-1)//batch_size + 1}...")
        embeddings = model.encode(documents_with_prefix, normalize_embeddings=True, show_progress_bar=False).tolist()
        
        # Salva metadados do modelo para uso posterior nas consultas
        for metadata in metadatas:
            metadata["model_type"] = model_type
            metadata["model_name"] = model_name
        
        # Insere no ChromaDB (documents originais sem prefixo para exibição)
        collection.add(
            ids=ids,
            documents=documents,  # Documentos originais para exibição
            metadatas=metadatas,
            embeddings=embeddings
        )
        
        print(f"   ✅ Inseridos {min(i+batch_size, len(items))}/{len(items)} itens")
    
    print("🎉 Inserção concluída com sucesso!")

def save_migration_log(db_path, collection_name, stats):
    """Salva log da migração"""
    log_data = {
        "migration_date": datetime.now().isoformat(),
        "collection_name": collection_name,
        "database_path": db_path,
        "statistics": stats
    }
    
    log_path = os.path.join(db_path, "migration_log.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    print(f"📋 Log da migração salvo em: {log_path}")

def show_model_options():
    """Mostra opções de modelos disponíveis"""
    print("\n🤖 MODELOS RECOMENDADOS:")
    print("=" * 60)
    for key, config in RECOMMENDED_MODELS.items():
        print(f"Preset: --model-preset {key}")
        print(f"   Nome: {config['name']}")
        print(f"   Tipo: {config['type'].upper()}")
        print(f"   Descrição: {config['description']}")
        print(f"   Batch recomendado: {config['batch_size']}")
        print()

def main():
    parser = argparse.ArgumentParser(
        description="Migração da base de conhecimento JSON para ChromaDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXEMPLOS DE USO:

  # Migração padrão (modelo MiniLM)
  python scripts/migrate_to_chromadb.py

  # Usar E5 Base (recomendado para melhor qualidade)
  python scripts/migrate_to_chromadb.py --model-preset multilingual-e5-base

  # Usar BGE-M3 (estado da arte)
  python scripts/migrate_to_chromadb.py --model-preset bge-m3

  # Modelo customizado
  python scripts/migrate_to_chromadb.py --model intfloat/multilingual-e5-small

Para ver opções de modelos: python scripts/migrate_to_chromadb.py --show-models
        """
    )
    
    parser.add_argument("--json", default="data/manual_complete.json", 
                       help="Caminho para o arquivo JSON da base de conhecimento")
    parser.add_argument("--db", default="./chromadb_storage", 
                       help="Diretório para armazenar o banco ChromaDB")
    parser.add_argument("--collection", default="epson_manuals", 
                       help="Nome da coleção no ChromaDB")
    parser.add_argument("--model", 
                       help="Modelo de embeddings customizado")
    parser.add_argument("--model-preset", choices=list(RECOMMENDED_MODELS.keys()),
                       default="multilingual-e5-base",
                       help="Preset de modelo recomendado (padrão: multilingual-e5-base)")
    parser.add_argument("--batch", type=int,
                       help="Tamanho do batch (automático baseado no modelo se não especificado)")
    parser.add_argument("--show-models", action="store_true",
                       help="Mostra modelos disponíveis e sai")
    
    args = parser.parse_args()
    
    if args.show_models:
        show_model_options()
        return
    
    # Determina modelo e configurações
    if args.model:
        # Modelo customizado
        model_name = args.model
        model_type = get_model_type(model_name)
        batch_size = args.batch or 128  # Padrão se não especificado
    else:
        # Usar preset
        preset = RECOMMENDED_MODELS[args.model_preset]
        model_name = preset["name"]
        model_type = preset["type"]
        batch_size = args.batch or preset["batch_size"]  # Usa batch do preset se não especificado
    
    print(f"📋 CONFIGURAÇÃO SELECIONADA:")
    print(f"   Modelo: {model_name}")
    print(f"   Tipo: {model_type.upper()}")
    print(f"   Batch size: {batch_size}")
    if model_type != "standard":
        print(f"   Prefixos: ✅ Ativados automaticamente")
    
    try:
        print("🚀 MIGRAÇÃO JSON → ChromaDB")
        print("=" * 50)
        
        # 1. Carrega dados
        items = load_knowledge_base(args.json)
        
        # 2. Processa e valida
        processed_items = process_items(items)
        
        if not processed_items:
            print("❌ Nenhum item válido encontrado para migração!")
            return
        
        # 3. Cria coleção ChromaDB
        client, collection = create_chromadb_collection(args.db, args.collection)
        
        # 4. Insere com embeddings
        insert_embeddings(collection, processed_items, model_name, batch_size)
        
        # 5. Salva log
        stats = {
            "total_items": len(items),
            "migrated_items": len(processed_items),
            "model_used": model_name,
            "model_type": model_type,
            "batch_size": batch_size,
            "preset_used": args.model_preset if not args.model else None
        }
        save_migration_log(args.db, args.collection, stats)
        
        print("\n" + "=" * 50)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"📊 {len(processed_items)} itens migrados para ChromaDB")
        print(f"🗄️  Banco: {args.db}")
        print(f"📁 Coleção: {args.collection}")
        print(f"🔍 Para testar: python scripts/test_chromadb.py")
        
    except Exception as e:
        print(f"\n❌ ERRO na migração: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()