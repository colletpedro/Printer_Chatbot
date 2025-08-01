#!/usr/bin/env python3
"""
Exemplo de integração ChromaDB com o chatbot existente
Mostra como substituir a busca textual atual pela busca semântica

Este é um exemplo de como adaptar o chatbot.py atual para usar ChromaDB
"""

import chromadb
from sentence_transformers import SentenceTransformer
import os

def apply_query_prefix(query, model_type):
    """Aplica prefixos apropriados para consultas baseado no tipo de modelo"""
    if model_type in ["e5", "bge"]:
        return f"query: {query}"
    else:
        return query  # Modelos padrão não precisam de prefixo

class ChromaDBSearch:
    """Classe para gerenciar busca semântica com ChromaDB"""
    
    def __init__(self, db_path="./chromadb_storage", collection_name="epson_manuals", 
                 model_name="intfloat/multilingual-e5-base"):
        self.db_path = db_path
        self.collection_name = collection_name
        self.model_name = model_name
        self.model = None
        self.collection = None
        self._load_resources()
    
    def _load_resources(self):
        """Carrega ChromaDB e modelo de embeddings"""
        try:
            # Carrega ChromaDB
            client = chromadb.PersistentClient(path=self.db_path)
            self.collection = client.get_collection(name=self.collection_name)
            
            # Carrega modelo de embeddings
            print(f"🤖 Carregando modelo {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            
            print(f"✅ ChromaDB carregado: {self.collection.count()} documentos")
            
        except Exception as e:
            print(f"❌ Erro ao carregar ChromaDB: {e}")
            print("💡 Execute: python scripts/migrate_to_chromadb.py")
            raise
    
    def semantic_search(self, query, printer_model=None, n_results=10, min_similarity=0.6):
        """
        Busca semântica que substitui o enhanced_search atual
        
        Args:
            query: Pergunta do usuário
            printer_model: Filtro por modelo de impressora (opcional)
            n_results: Número máximo de resultados
            min_similarity: Similaridade mínima (0-1)
        
        Returns:
            Lista de tuplas (documento, score) - compatível com enhanced_search
        """
        try:
            # Detecta tipo de modelo dos metadados (pega uma amostra)
            sample = self.collection.get(limit=1)
            model_type = "standard"  # padrão
            if sample['metadatas'] and sample['metadatas'][0].get('model_type'):
                model_type = sample['metadatas'][0]['model_type']
            
            # Aplica prefixo apropriado na consulta
            query_with_prefix = apply_query_prefix(query, model_type)
            
            # Gera embedding da consulta (com prefixo se necessário)
            query_embedding = self.model.encode([query_with_prefix], normalize_embeddings=True)[0].tolist()
            
            # Prepara filtros
            where_filter = {}
            if printer_model:
                where_filter["printer_model"] = printer_model
            
            # Busca no ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter if where_filter else None
            )
            
            # Converte para formato compatível com sistema atual
            formatted_results = []
            
            if results['ids'][0]:
                for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                    # Converte distância para similaridade (0-1, onde 1 = idêntico)
                    similarity = 1 - distance
                    
                    # Filtra por similaridade mínima
                    if similarity < min_similarity:
                        continue
                    
                    # Cria documento no formato do sistema atual
                    document = {
                        'id': doc_id,
                        'title': results['metadatas'][0][i].get('original_title', ''),
                        'content': results['documents'][0][i],
                        'printer_model': results['metadatas'][0][i].get('printer_model'),
                        'type': results['metadatas'][0][i].get('type', 'geral'),
                        'keywords': results['metadatas'][0][i].get('keywords', '').split(', ') if results['metadatas'][0][i].get('keywords') else [],
                        'pdf_hash': results['metadatas'][0][i].get('pdf_hash')
                    }
                    
                    # Score compatível (0-100)
                    score = int(similarity * 100)
                    
                    formatted_results.append((document, score))
            
            # Ordena por score decrescente
            formatted_results.sort(key=lambda x: x[1], reverse=True)
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Erro na busca semântica: {e}")
            return []
    
    def get_available_printer_models(self):
        """Obtém lista de modelos de impressora disponíveis"""
        try:
            all_docs = self.collection.get()
            models = set()
            
            for metadata in all_docs['metadatas']:
                if metadata.get('printer_model'):
                    models.add(metadata['printer_model'])
            
            return sorted(list(models))
            
        except Exception as e:
            print(f"❌ Erro ao obter modelos: {e}")
            return []
    
    def hybrid_search(self, query, printer_model=None, n_results=10, semantic_weight=0.7):
        """
        Busca híbrida: combina busca semântica com busca por palavras-chave
        
        Args:
            semantic_weight: Peso da busca semântica (0-1), o resto é busca textual
        """
        # Busca semântica
        semantic_results = self.semantic_search(query, printer_model, n_results)
        
        # Busca textual simples (usando contains no texto)
        text_results = self._text_search(query, printer_model, n_results)
        
        # Combina resultados com pesos
        combined_results = {}
        
        # Adiciona resultados semânticos
        for doc, score in semantic_results:
            doc_id = doc['id']
            combined_results[doc_id] = {
                'doc': doc,
                'semantic_score': score,
                'text_score': 0
            }
        
        # Adiciona/atualiza com resultados textuais
        for doc, score in text_results:
            doc_id = doc['id']
            if doc_id in combined_results:
                combined_results[doc_id]['text_score'] = score
            else:
                combined_results[doc_id] = {
                    'doc': doc,
                    'semantic_score': 0,
                    'text_score': score
                }
        
        # Calcula score final combinado
        final_results = []
        for doc_id, data in combined_results.items():
            combined_score = (
                data['semantic_score'] * semantic_weight +
                data['text_score'] * (1 - semantic_weight)
            )
            final_results.append((data['doc'], int(combined_score)))
        
        # Ordena por score combinado
        final_results.sort(key=lambda x: x[1], reverse=True)
        
        return final_results[:n_results]
    
    def _text_search(self, query, printer_model=None, n_results=10):
        """Busca textual simples para busca híbrida"""
        try:
            # Prepara filtros
            where_filter = {}
            if printer_model:
                where_filter["printer_model"] = printer_model
            
            # Busca por contém texto (limitação do ChromaDB)
            # Em implementação real, usaria busca full-text mais sofisticada
            all_results = self.collection.get(
                where=where_filter if where_filter else None
            )
            
            # Busca simples por palavras-chave no texto
            query_words = query.lower().split()
            text_matches = []
            
            if all_results['ids']:
                for i, doc_text in enumerate(all_results['documents']):
                    score = 0
                    doc_text_lower = doc_text.lower()
                    
                    for word in query_words:
                        if len(word) > 2 and word in doc_text_lower:
                            score += 10  # Score simples
                    
                    if score > 0:
                        document = {
                            'id': all_results['ids'][i],
                            'title': all_results['metadatas'][i].get('original_title', ''),
                            'content': doc_text,
                            'printer_model': all_results['metadatas'][i].get('printer_model'),
                            'type': all_results['metadatas'][i].get('type', 'geral'),
                            'keywords': all_results['metadatas'][i].get('keywords', []),
                            'pdf_hash': all_results['metadatas'][i].get('pdf_hash')
                        }
                        text_matches.append((document, score))
            
            # Ordena e limita resultados
            text_matches.sort(key=lambda x: x[1], reverse=True)
            return text_matches[:n_results]
            
        except Exception as e:
            print(f"❌ Erro na busca textual: {e}")
            return []

# Exemplo de uso - substituição no chatbot.py atual
def enhanced_search_chromadb(query, filtered_knowledge_base=None, printer_model=None):
    """
    Drop-in replacement para a função enhanced_search atual
    
    Esta função pode substituir diretamente a enhanced_search no chatbot.py
    """
    try:
        # Inicializa ChromaDB (em produção, fazer isso uma vez no início)
        chroma_search = ChromaDBSearch()
        
        # Usa busca semântica
        results = chroma_search.semantic_search(
            query=query, 
            printer_model=printer_model,
            n_results=10,
            min_similarity=0.3  # Mais permissivo que o sistema atual
        )
        
        return results if results else None
        
    except Exception as e:
        print(f"❌ Erro na busca ChromaDB, usando sistema atual: {e}")
        # Fallback para sistema atual se ChromaDB falhar
        if filtered_knowledge_base:
            # Importa função original (isso requer refatoração no código atual)
            # from chatbot import enhanced_search as original_enhanced_search
            # return original_enhanced_search(query, filtered_knowledge_base)
            pass
        return None

if __name__ == "__main__":
    """Teste da integração"""
    try:
        print("🧪 Testando integração ChromaDB...")
        
        chroma_search = ChromaDBSearch()
        
        # Teste de busca
        query = "como trocar tinta"
        results = chroma_search.semantic_search(query)
        
        print(f"\n🔍 Resultados para '{query}':")
        for i, (doc, score) in enumerate(results[:3]):
            print(f"   {i+1}. {doc['id']} (Score: {score})")
            print(f"      Modelo: {doc['printer_model']}")
            
        # Teste de modelos
        models = chroma_search.get_available_printer_models()
        print(f"\n📱 Modelos disponíveis: {len(models)}")
        
        print("✅ Integração funcionando!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        print("💡 Execute primeiro: python scripts/migrate_to_chromadb.py")