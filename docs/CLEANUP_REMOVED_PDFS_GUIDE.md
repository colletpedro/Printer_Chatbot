# 🧹 Guia do Script de Limpeza de PDFs Removidos

## 📋 Visão Geral

O script `cleanup_removed_pdfs.py` permite remover **manualmente** da base de conhecimento as seções de PDFs que foram removidos do Google Drive.

## ❓ Quando Usar

Use este script quando:
- ✅ Você removeu um PDF do Google Drive
- ✅ Quer que ele seja removido também da base de conhecimento  
- ✅ Não quer que o chatbot responda mais sobre esse modelo

## 🚀 Como Executar

### Opção 1: Script Shell (Recomendado)
```bash
./cleanup_removed_pdfs.sh
```

### Opção 2: Diretamente com Python
```bash
source venv/bin/activate  # Ativar ambiente virtual
python3 scripts/cleanup_removed_pdfs.py
```

## 🔄 Como Funciona

### 1. **Conecta ao Google Drive**
- Lista todos os PDFs atualmente na pasta configurada
- Extrai os modelos dos nomes dos arquivos

### 2. **Analisa a Base de Conhecimento**
- Carrega o arquivo `data/manual_complete.json`
- Identifica seções que não têm PDF correspondente no Drive

### 3. **Exibe Seções Órfãs**
- Mostra modelos que existem na base mas não no Drive
- Exibe número de seções e exemplos

### 4. **Permite Escolha Interativa**
- Para cada modelo órfão, pergunta se deve remover
- Opção `info` mostra detalhes completos das seções

### 5. **Confirmação de Segurança**
- Exige digitação de `CONFIRMO` para prosseguir
- Mostra resumo do que será removido

### 6. **Atualiza a Base**
- Remove as seções escolhidas do JSON
- Atualiza metadados (total de seções, timestamp)
- Salva arquivo atualizado

## 📊 Exemplo de Execução

```
🧹 LIMPEZA DA BASE DE CONHECIMENTO
==================================================

🔄 Conectando ao Google Drive...
📁 Listando PDFs atuais no Drive...

📋 PDFs encontrados no Drive (5):
   📄 impressoraL3110.pdf → impressoraL3110
   📄 impressoraL4260.pdf → impressoraL4260
   📄 impressoraL3150.pdf → impressoraL3150
   📄 impressoraL4150.pdf → impressoraL4150
   📄 impressoraL3250_L3251.pdf → impressoraL3250_L3251

📖 Carregando base de conhecimento...
   ✅ 3099 seções carregadas

🔍 Procurando seções órfãs...

📋 SEÇÕES ÓRFÃS ENCONTRADAS:
============================================================

🖨️  Modelo: impressoraL375_ANTIGO
   📄 Seções: 150
   📝 Exemplos de seções:
      1. Configuração de Rede
      2. Solução de Problemas  
      3. Especificações Técnicas
      ... e mais 147 seções

🤔 ESCOLHA O QUE REMOVER:
============================================================

❓ Remover todas as seções do modelo 'impressoraL375_ANTIGO'? (s/n/info): info

   📊 Informações detalhadas do modelo 'impressoraL375_ANTIGO':
      📄 Total de seções: 150
      📝 Títulos das seções:
         1. Configuração de Rede Wi-Fi
         2. Solução de Problemas de Impressão
         3. Especificações Técnicas Completas
         ...

❓ Remover todas as seções do modelo 'impressoraL375_ANTIGO'? (s/n/info): s
   ✅ Modelo 'impressoraL375_ANTIGO' marcado para remoção

⚠️  CONFIRMAÇÃO FINAL:
   🗑️  Modelos a remover: impressoraL375_ANTIGO
   📄 Total de seções a remover: 150
   📊 Seções restantes: 2949

❓ Confirma a remoção? Esta ação NÃO PODE ser desfeita! (digite 'CONFIRMO'): CONFIRMO

🗑️  Removendo seções...
💾 Salvando base de conhecimento atualizada...

✅ LIMPEZA CONCLUÍDA COM SUCESSO!
   🗑️  Seções removidas: 150
   📄 Seções restantes: 2949
   📁 Arquivo atualizado: /path/to/data/manual_complete.json

💡 RECOMENDAÇÃO:
   🔄 Reinicie o chatbot para que ele carregue a base atualizada
   📝 As seções removidas não estarão mais disponíveis nas consultas
```

## ⚠️ Avisos Importantes

### 🔒 **Segurança**
- ⚠️ A remoção é **PERMANENTE** e NÃO pode ser desfeita
- ⚠️ Faça backup do `manual_complete.json` se necessário
- ⚠️ Digite `CONFIRMO` exatamente como mostrado

### 🎯 **Quando NÃO Usar**
- ❌ Para PDFs temporariamente offline
- ❌ Para PDFs que você pretende recolocar no Drive
- ❌ Se não tiver certeza sobre a remoção

### 🔄 **Após a Execução**
- ✅ Reinicie o chatbot para carregar a base atualizada
- ✅ Teste se o modelo realmente não aparece mais
- ✅ Verifique se outros modelos continuam funcionando

## 🛠️ Arquivos Modificados

- **`data/manual_complete.json`**: Base de conhecimento atualizada
- **Logs**: Todas as operações são logadas na tela

## 🐛 Solução de Problemas

### Erro: "No module named 'google'"
```bash
# Certifique-se de ativar o ambiente virtual
source venv/bin/activate
```

### Erro: "Arquivo não encontrado"
```bash
# Execute a partir do diretório raiz do projeto
cd /path/to/GeminiMGI
./cleanup_removed_pdfs.sh
```

### Erro: "Credenciais inválidas"
```bash
# Verifique se o arquivo core/key.json existe e está correto
ls -la core/key.json
```

## 💡 Dicas

1. **Use `info`** para ver detalhes antes de remover
2. **Teste primeiro** removendo um modelo pequeno
3. **Faça backup** da base de conhecimento regularmente
4. **Documente** quais PDFs você removeu e por quê

## 🔗 Arquivos Relacionados

- **Script principal**: `scripts/cleanup_removed_pdfs.py`
- **Script de execução**: `cleanup_removed_pdfs.sh`  
- **Base de conhecimento**: `data/manual_complete.json`
- **Credenciais**: `core/key.json` 