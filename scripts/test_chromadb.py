#!/usr/bin/env python3
"""
Script de teste para validar a migração do ChromaDB
Testa funcionalidades básicas e comparações com o sistema atual

Uso:
    python scripts/test_chromadb.py
    python scripts/test_chromadb.py --query "como trocar tinta"
"""

import argparse
import os
import sys
import json
from datetime import datetime
import chromadb
from sentence_transformers import SentenceTransformer

# Adiciona o diretório core ao path para importar funções do sistema atual
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

def apply_query_prefix(query, model_type):
    """Aplica prefixos apropriados para consultas baseado no tipo de modelo"""
    if model_type in ["e5", "bge"]:
        return f"query: {query}"
    else:
        return query  # Modelos padrão não precisam de prefixo

def load_chromadb(db_path, collection_name):
    """Carrega a coleção do ChromaDB"""
    try:
        client = chromadb.PersistentClient(path=db_path)
        collection = client.get_collection(name=collection_name)
        return client, collection
    except Exception as e:
        print(f"❌ Erro ao carregar ChromaDB: {e}")
        print("💡 Execute primeiro: python scripts/migrate_to_chromadb.py")
        return None, None

def test_basic_functionality(collection):
    """Testa funcionalidades básicas do ChromaDB"""
    print("🔍 TESTE 1: Funcionalidades Básicas")
    print("-" * 40)
    
    try:
        # Conta total de documentos
        count = collection.count()
        print(f"✅ Total de documentos: {count}")
        
        # Pega uma amostra de documentos
        sample = collection.get(limit=3)
        print(f"✅ Amostra carregada: {len(sample['ids'])} documentos")
        
        # Mostra exemplo de documento
        if sample['ids']:
            print(f"\n📄 Exemplo de documento:")
            print(f"   ID: {sample['ids'][0]}")
            print(f"   Modelo: {sample['metadatas'][0].get('printer_model', 'N/A')}")
            print(f"   Tipo: {sample['metadatas'][0].get('type', 'N/A')}")
            text_preview = sample['documents'][0][:100] + "..." if len(sample['documents'][0]) > 100 else sample['documents'][0]
            print(f"   Texto: {text_preview}")
        
        return True
    except Exception as e:
        print(f"❌ Erro no teste básico: {e}")
        return False

def test_semantic_search(collection, model_name):
    """Testa busca semântica"""
    print("\n🔎 TESTE 2: Busca Semântica")
    print("-" * 40)
    
    test_queries = [
        "como trocar tinta da impressora",
        "impressora não liga",
        "papel emperrado",
        "configurar wifi",
        "qualidade de impressão ruim"
    ]
    
    try:
        # Carrega o modelo (mesmo usado na migração)
        print(f"🤖 Carregando modelo {model_name}...")
        model = SentenceTransformer(model_name)
        
        # Detecta tipo de modelo dos metadados
        sample = collection.get(limit=1)
        model_type = "standard"  # padrão
        if sample['metadatas'] and sample['metadatas'][0].get('model_type'):
            model_type = sample['metadatas'][0]['model_type']
            print(f"🏷️  Tipo de modelo detectado: {model_type.upper()}")
        
        for query in test_queries:
            print(f"\n🔍 Consulta: '{query}'")
            
            # Aplica prefixo apropriado na consulta
            query_with_prefix = apply_query_prefix(query, model_type)
            if query_with_prefix != query:
                print(f"    Consulta com prefixo: '{query_with_prefix}'")
            
            # Gera embedding da consulta
            query_embedding = model.encode([query_with_prefix], normalize_embeddings=True)[0].tolist()
            
            # Busca documentos similares
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=3
            )
            
            if results['ids'][0]:
                print(f"   ✅ Encontrados {len(results['ids'][0])} resultados")
                for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                    metadata = results['metadatas'][0][i]
                    similarity = 1 - distance  # Converte distância para similaridade
                    print(f"      {i+1}. {doc_id} (Similaridade: {similarity:.3f})")
                    print(f"         Modelo: {metadata.get('printer_model', 'N/A')}")
                    print(f"         Tipo: {metadata.get('type', 'N/A')}")
            else:
                print("   ⚠️  Nenhum resultado encontrado")
        
        return True
    except Exception as e:
        print(f"❌ Erro na busca semântica: {e}")
        return False

def test_metadata_filtering(collection):
    """Testa filtros por metadados"""
    print("\n🏷️  TESTE 3: Filtros por Metadados")
    print("-" * 40)
    
    try:
        # Lista modelos disponíveis
        all_docs = collection.get()
        printers = set()
        types = set()
        
        for metadata in all_docs['metadatas']:
            if metadata.get('printer_model'):
                printers.add(metadata['printer_model'])
            if metadata.get('type'):
                types.add(metadata['type'])
        
        print(f"✅ Modelos disponíveis: {len(printers)}")
        print(f"   {sorted(list(printers))[:5]}{'...' if len(printers) > 5 else ''}")
        
        print(f"✅ Tipos de conteúdo: {sorted(list(types))}")
        
        # Teste de filtro por modelo específico
        if printers:
            test_printer = list(printers)[0]
            filtered_results = collection.get(
                where={"printer_model": test_printer},
                limit=5
            )
            print(f"✅ Filtro por modelo '{test_printer}': {len(filtered_results['ids'])} documentos")
        
        return True
    except Exception as e:
        print(f"❌ Erro nos filtros: {e}")
        return False

def compare_with_current_system(query, collection, model_name):
    """Compara resultados com o sistema atual (se disponível)"""
    print(f"\n⚖️  TESTE 4: Comparação com Sistema Atual")
    print("-" * 40)
    print(f"🔍 Consulta: '{query}'")
    
    try:
        # Busca no ChromaDB
        print("\n📊 Resultados ChromaDB:")
        model = SentenceTransformer(model_name)
        
        # Detecta tipo de modelo dos metadados
        sample = collection.get(limit=1)
        model_type = "standard"  # padrão
        if sample['metadatas'] and sample['metadatas'][0].get('model_type'):
            model_type = sample['metadatas'][0]['model_type']
        
        # Aplica prefixo apropriado na consulta
        query_with_prefix = apply_query_prefix(query, model_type)
        
        query_embedding = model.encode([query_with_prefix], normalize_embeddings=True)[0].tolist()
        
        chroma_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )
        
        if chroma_results['ids'][0]:
            for i, (doc_id, distance) in enumerate(zip(chroma_results['ids'][0], chroma_results['distances'][0])):
                similarity = 1 - distance
                metadata = chroma_results['metadatas'][0][i]
                print(f"   {i+1}. {doc_id} (Sim: {similarity:.3f}) - {metadata.get('printer_model', 'N/A')}")
        
        # Tenta carregar e comparar com sistema atual
        try:
            from chatbot import enhanced_search, knowledge_base, load_complete_manual
            
            print("\n📊 Resultados Sistema Atual:")
            if not knowledge_base:
                kb = load_complete_manual()
                if kb:
                    current_results = enhanced_search(query, kb)
                    if current_results:
                        for i, (section, score) in enumerate(current_results[:5]):
                            print(f"   {i+1}. {section.get('id', 'N/A')} (Score: {score}) - {section.get('printer_model', 'N/A')}")
                    else:
                        print("   Nenhum resultado encontrado")
                else:
                    print("   ❌ Não foi possível carregar a base atual")
            
        except ImportError:
            print("   ⚠️  Sistema atual não disponível para comparação")
        
        return True
    except Exception as e:
        print(f"❌ Erro na comparação: {e}")
        return False

def generate_test_report(results):
    """Gera relatório dos testes"""
    print("\n" + "=" * 50)
    print("📋 RELATÓRIO DOS TESTES")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"✅ Testes aprovados: {passed}/{total}")
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("💡 A migração foi bem-sucedida e o ChromaDB está funcionando corretamente.")
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam.")
        print("💡 Verifique os erros acima e considere re-executar a migração.")

def main():
    parser = argparse.ArgumentParser(description="Teste da migração ChromaDB")
    parser.add_argument("--db", default="./chromadb_storage", 
                       help="Diretório do banco ChromaDB")
    parser.add_argument("--collection", default="epson_manuals", 
                       help="Nome da coleção")
    parser.add_argument("--model", default="intfloat/multilingual-e5-base",
                       help="Modelo de embeddings usado na migração")
    parser.add_argument("--query", default="como trocar tinta da impressora",
                       help="Consulta de teste para comparação")
    
    args = parser.parse_args()
    
    print("🧪 TESTE DA MIGRAÇÃO ChromaDB")
    print("=" * 50)
    print(f"🗄️  Banco: {args.db}")
    print(f"📁 Coleção: {args.collection}")
    print(f"🤖 Modelo: {args.model}")
    
    # Carrega ChromaDB
    client, collection = load_chromadb(args.db, args.collection)
    if not collection:
        sys.exit(1)
    
    # Executa testes
    results = {}
    
    results["Funcionalidades Básicas"] = test_basic_functionality(collection)
    results["Busca Semântica"] = test_semantic_search(collection, args.model)
    results["Filtros por Metadados"] = test_metadata_filtering(collection)
    results["Comparação com Sistema Atual"] = compare_with_current_system(args.query, collection, args.model)
    
    # Gera relatório
    generate_test_report(results)

if __name__ == "__main__":
    main()