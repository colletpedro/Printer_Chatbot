# Sincronização Direta Google Drive → ChromaDB

## Visão Geral

Este documento descreve o novo sistema de sincronização direta entre Google Drive e ChromaDB, criado para substituir o processo anterior que usava JSON como intermediário.

## Características Principais

✅ **Sincronização Direta**: Conecta diretamente Google Drive ao ChromaDB  
✅ **Detecção Inteligente**: Identifica PDFs adicionados, modificados ou removidos  
✅ **Sem JSON Intermediário**: Não depende de arquivos JSON para funcionar  
✅ **Sem Fallback**: Funciona exclusivamente com ChromaDB  
✅ **Execução Manual**: Script executado sob demanda pelo usuário  
✅ **Log Detalhado**: Registra todas as operações realizadas  
✅ **Otimização por Hash**: Evita downloads desnecessários usando hash MD5 do Drive  

## Arquivos Criados

### 1. `sync_drive_chromadb.py`
Script principal que realiza a sincronização completa.

**Funcionalidades:**
- Lista PDFs no Google Drive
- Verifica estado atual do ChromaDB
- Detecta mudanças (adições, modificações, remoções)
- Processa PDFs e extrai seções
- Atualiza ChromaDB diretamente
- Gera log detalhado das operações

### 2. `run_sync_drive_chromadb.sh`
Script executável que facilita a execução da sincronização.

**Funcionalidades:**
- Verifica dependências
- Ativa ambiente virtual automaticamente
- Valida arquivos essenciais
- Executa sincronização
- Mostra resultados e dicas

## Como Usar

### Pré-requisitos

1. **Dependências Python:**
```bash
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
pip install chromadb sentence-transformers torch
```

2. **Arquivos necessários:**
- `core/key.json` (credenciais Google Drive)
- `core/extract_pdf_complete.py` (extração de PDFs)
- `scripts/migrate_to_chromadb.py` (funções ChromaDB)

### Execução

#### Opção 1: Script Automatizado (Recomendado)
```bash
./run_sync_drive_chromadb.sh
```

#### Opção 2: Execução Direta
```bash
python3 sync_drive_chromadb.py
```

## Fluxo de Operação

```
1. 📁 Lista PDFs no Google Drive
         ↓
2. 🗄️ Verifica estado atual do ChromaDB
         ↓
3. 🔍 Compara estados e identifica mudanças
         ↓
4. ❌ Remove modelos que não existem mais no Drive
         ↓
5. ➕ Adiciona novos PDFs encontrados no Drive
         ↓
6. 🔄 Atualiza PDFs modificados (hash diferente)
         ↓
7. 📋 Salva log detalhado da operação
```

## Detecção de Mudanças

### Adição de PDFs
- **Trigger**: PDF existe no Drive mas não no ChromaDB
- **Ação**: Baixa, processa e insere todas as seções

### Modificação de PDFs
- **Trigger**: Hash MD5 do PDF no Drive ≠ hash armazenado no ChromaDB
- **Ação**: Remove seções antigas, processa versão nova e reinsere
- **Otimização**: Usa hash do Google Drive, evitando download para verificação

### Remoção de PDFs
- **Trigger**: PDF existe no ChromaDB mas não no Drive
- **Ação**: Remove todas as seções do modelo do ChromaDB

## Configurações

### Configurações Principais
```python
DRIVE_FOLDER_ID = "1B-Xsgvy4W392yfLP4ilrzrtl8zzmEgTl"  # Pasta do Drive
COLLECTION_NAME = "epson_manuals"                        # Coleção ChromaDB
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"       # Modelo de embedding
BATCH_SIZE = 128                                         # Tamanho do batch
```

### Caminhos
- **Credenciais**: `core/key.json`
- **ChromaDB**: `chromadb_storage/`
- **Logs**: `data/sync_log.json`
- **Temp**: `temp_sync/` (criado e removido automaticamente)

## Logs e Monitoramento

### Log de Sincronização (`data/sync_log.json`)
```json
{
  "sync_date": "2024-01-15T10:30:00",
  "sync_type": "direct_drive_chromadb",
  "statistics": {
    "pdfs_found": 12,
    "pdfs_added": 2,
    "pdfs_updated": 1,
    "pdfs_removed": 0,
    "pdfs_skipped": 9,
    "sections_added": 45,
    "sections_removed": 0,
    "errors": []
  },
  "configuration": {
    "drive_folder_id": "1B-Xsgvy4W392yfLP4ilrzrtl8zzmEgTl",
    "chromadb_path": "chromadb_storage",
    "collection_name": "epson_manuals",
    "embedding_model": "intfloat/multilingual-e5-base",
    "batch_size": 128
  }
}
```

### Estatísticas Exibidas
- ⏱️ **Duração**: Tempo total da sincronização
- 📁 **PDFs encontrados**: Total de PDFs no Drive
- ➕ **PDFs adicionados**: Novos PDFs processados
- 🔄 **PDFs atualizados**: PDFs modificados reprocessados
- ❌ **PDFs removidos**: PDFs deletados do ChromaDB
- ⏭️ **PDFs ignorados**: PDFs não modificados (downloads evitados)
- 📝 **Seções adicionadas**: Total de seções inseridas
- 🗑️ **Seções removidas**: Total de seções deletadas
- 🚀 **Eficiência**: Percentual de downloads evitados por otimização
- ⚠️ **Erros**: Lista de erros encontrados (se houver)

## Tratamento de Erros

### Erros Comuns e Soluções

1. **Credenciais inválidas**
   - Verificar se `core/key.json` existe e está correto
   - Confirmar permissões da conta de serviço

2. **ChromaDB não acessível**
   - Verificar se diretório `chromadb_storage/` tem permissões
   - Confirmar instalação do ChromaDB

3. **Modelo de embedding não encontrado**
   - Primeira execução baixa o modelo automaticamente
   - Verificar conexão com internet

4. **PDF corrompido**
   - Script continua processando outros PDFs
   - Erro é registrado no log

### Comportamento em Caso de Erro
- ❌ **Sem fallback**: Script não tenta usar JSON se ChromaDB falhar
- 🔄 **Continuidade**: Erros em PDFs individuais não param o processo
- 📋 **Log completo**: Todos os erros são registrados
- 🧹 **Limpeza**: Arquivos temporários são removidos mesmo com erro

## Comparação com Sistema Anterior

| Aspecto | Sistema Anterior | Sistema Novo |
|---------|------------------|--------------|
| **Intermediário** | JSON obrigatório | Direto Drive → ChromaDB |
| **Fallback** | JSON se ChromaDB falhar | Sem fallback |
| **Dependências** | JSON + ChromaDB | Apenas ChromaDB |
| **Detecção** | Webhook + JSON | Comparação direta |
| **Execução** | Automática | Manual |
| **Logs** | Múltiplos arquivos | Log unificado |

## Integração com Sistema Existente

### Chatbot
O chatbot continuará funcionando normalmente, pois:
- ✅ Usa a mesma coleção ChromaDB (`epson_manuals`)
- ✅ Mantém formato de metadados compatível
- ✅ Preserva modelo de embedding (`multilingual-e5-base`)

### Webhook (Opcional)
- ⚠️ Webhook não é necessário para este sistema
- ✅ Pode coexistir se necessário para outras funcionalidades
- 🔄 Recomenda-se desativar para evitar conflitos

## Manutenção

### Execução Recomendada
- 📅 **Frequência**: Conforme necessidade (manual)
- ⏰ **Quando executar**: Após mudanças conhecidas no Drive
- 🔍 **Monitoramento**: Verificar logs após execução

### Limpeza
- 🗑️ Arquivos temporários são removidos automaticamente
- 📋 Logs são preservados para auditoria
- 💾 ChromaDB mantém histórico de versões

## Troubleshooting

### Script não executa
```bash
# Verificar permissões
chmod +x run_sync_drive_chromadb.sh

# Verificar Python
python3 --version

# Verificar dependências
pip list | grep -E "(google|chromadb|sentence)"
```

### Erro de importação
```bash
# Instalar dependências
pip install -r scripts/requirements_chromadb.txt
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

### ChromaDB corrompido
```bash
# Backup do ChromaDB
cp -r chromadb_storage chromadb_storage.backup

# Recriar coleção (o script faz automaticamente se não existir)
rm -rf chromadb_storage
python3 sync_drive_chromadb.py
```

### Verificar sincronização
```bash
# Ver log da última execução
cat data/sync_log.json | jq '.'

# Testar ChatBot após sincronização
python3 backup_old_system/chatbot_chromadb.py
```

## Exemplo de Execução

```bash
$ ./run_sync_drive_chromadb.sh

🚀 Iniciando sincronização direta Google Drive → ChromaDB
==========================================================
🔧 Ativando ambiente virtual...
✅ Ambiente virtual ativado
🔍 Verificando dependências...
✅ Todas as dependências estão instaladas
📁 Verificando arquivos essenciais...
✅ Todos os arquivos essenciais encontrados

🔄 Executando sincronização...
==========================================================

🚀 SINCRONIZAÇÃO DIRETA GOOGLE DRIVE → CHROMADB
============================================================
Este script sincroniza PDFs do Google Drive diretamente com ChromaDB
sem usar arquivos JSON intermediários.

🔍 Verificando dependências...
🚀 Inicializando sincronização direta Drive → ChromaDB

🔧 Configurando serviços...
📁 Configurando Google Drive...
✅ Google Drive configurado
🗄️ Configurando ChromaDB...
✅ Coleção 'epson_manuals' encontrada
🤖 Carregando modelo de embedding: intfloat/multilingual-e5-base
🏷️ Modelo E5 detectado - prefixos automáticos ativados
✅ Modelo carregado
✅ Configuração concluída!

🔄 INICIANDO SINCRONIZAÇÃO
==================================================

📋 Listando PDFs no Drive (pasta: 1B-Xsgvy4W392yfLP4ilrzrtl8zzmEgTl)...
✅ Encontrados 12 PDFs no Drive
   📄 impressoraL1300.pdf (2.1 MB) - Hash: a1b2c3d4...
   📄 impressoraL3110.pdf (1.8 MB) - Hash: e5f6g7h8...
   📄 impressoraL3150.pdf (2.0 MB) - Hash: i9j0k1l2...
   ... (mais PDFs)

🗄️ Verificando estado atual do ChromaDB...
✅ ChromaDB contém 10 modelos:
   📱 impressoraL1300: 45 seções (hash: a1b2c3d4...)
   📱 impressoraL3110: 38 seções (hash: e5f6g7h8...)
   ... (mais modelos)

🔍 ANÁLISE DE MUDANÇAS:
   📁 Drive: 12 modelos
   🗄️ ChromaDB: 10 modelos

📋 PLANO DE SINCRONIZAÇÃO:
   ➕ Adicionar: 2 modelos
   ❌ Remover: 0 modelos
   🔍 Verificar: 10 modelos
      Novos: impressoraL805, impressoraL5290

📥 Baixando: impressoraL805.pdf
✅ Baixado: temp_sync/impressoraL805.pdf
🔄 Processando PDF: impressoraL805
📝 Extraídas 42 seções
🧠 Gerando embeddings para batch 1
✅ Inseridas 42 seções
🎉 Modelo impressoraL805 processado com sucesso!

... (processamento de outros PDFs)

✅ impressoraL1300 não modificado (hash: a1b2c3d4...)
✅ impressoraL3110 não modificado (hash: e5f6g7h8...)
🔄 PDF modificado detectado: impressoraL4150
   Hash Drive: x9y8z7w6...
   Hash armazenado: a1b2c3d4...
🗑️ Removendo modelo impressoraL4150 do ChromaDB...
✅ Removidas 35 seções do modelo impressoraL4150
🔄 Processando PDF: impressoraL4150
📝 Extraídas 38 seções
🧠 Gerando embeddings para batch 1
✅ Inseridas 38 seções
🎉 Modelo impressoraL4150 processado com sucesso!

📋 Log salvo: data/sync_log.json

==================================================
📊 ESTATÍSTICAS DA SINCRONIZAÇÃO
==================================================
⏱️ Duração: 0:03:45
📁 PDFs encontrados no Drive: 12
➕ PDFs adicionados: 2
🔄 PDFs atualizados: 1
❌ PDFs removidos: 0
⏭️ PDFs não modificados (ignorados): 9
📝 Seções adicionadas: 118
🗑️ Seções removidas: 35
🚀 Downloads evitados: 75.0% (otimização por hash)
✅ Nenhum erro encontrado
==================================================

🎉 Sincronização concluída com sucesso!

💡 Dicas:
   • Execute este script sempre que quiser sincronizar
   • Verifique o log em data/sync_log.json para detalhes
   • Use o chatbot para testar as atualizações
==========================================================
```

## Conclusão

O novo sistema de sincronização direta oferece:

- ✅ **Simplicidade**: Sem dependência de JSON intermediário
- ✅ **Confiabilidade**: Detecção precisa de mudanças via hash
- ✅ **Transparência**: Log detalhado de todas as operações
- ✅ **Eficiência**: Processamento apenas dos PDFs modificados
- ✅ **Controle**: Execução manual quando necessário

Este sistema substitui completamente a necessidade de manter arquivos JSON sincronizados, oferecendo uma solução mais direta e confiável para manter a base de conhecimento atualizada.

