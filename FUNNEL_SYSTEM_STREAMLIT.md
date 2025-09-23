# 🔍 Sistema de Afunilamento Inteligente - Streamlit

## 📝 Descrição

Sistema de identificação progressiva de impressoras Epson através de perguntas interativas sobre características do equipamento.

## 🎯 Como Funciona

Quando o usuário faz uma pergunta sem especificar o modelo da impressora, o sistema:

1. **Tenta detectar** o modelo na mensagem
2. Se não detectar, **inicia o afunilamento** com perguntas interativas
3. **Filtra progressivamente** os modelos baseado nas respostas
4. **Identifica automaticamente** quando resta apenas uma opção
5. **Processa a pergunta original** após identificação

## 📊 Fluxo de Perguntas

### 1️⃣ Tipo de Impressora
```
"Sua impressora é multifuncional?"
- Sim, é multifuncional → Vai para pergunta de Duplex
- Não, só imprime → Vai para pergunta de A3
- Não sei → Pula característica
```

### 2️⃣ Para Multifuncionais

#### Duplex
```
"Imprime frente e verso automaticamente?"
- Sim → Filtra modelos com duplex
- Não → Filtra modelos sem duplex
```

#### ADF
```
"Tem alimentador automático de documentos?"
- Sim → Filtra modelos com ADF
- Não → Filtra modelos sem ADF
```

#### FAX (se tem ADF)
```
"Tem função de FAX?"
- Sim → L5190, L5290
- Não → L4150, L4260, L6490
```

### 3️⃣ Suporte A3
```
"Suporta papel A3?"
- Sim → L1300 (simples) ou L6490 (multi)
- Não → Demais modelos
```

## 🖨️ Mapeamento de Características

| Modelo | Multi | Duplex | ADF | FAX | A3 |
|--------|-------|--------|-----|-----|----|
| L805 | ❌ | ❌ | ❌ | ❌ | ❌ |
| L1300 | ❌ | ❌ | ❌ | ❌ | ✅ |
| L375 | ✅ | ❌ | ❌ | ❌ | ❌ |
| L396 | ✅ | ❌ | ❌ | ❌ | ❌ |
| L3110 | ✅ | ❌ | ❌ | ❌ | ❌ |
| L3150 | ✅ | ❌ | ❌ | ❌ | ❌ |
| L3250/L3251 | ✅ | ✅ | ❌ | ❌ | ❌ |
| L4150 | ✅ | ✅ | ✅ | ❌ | ❌ |
| L4260 | ✅ | ✅ | ✅ | ❌ | ❌ |
| L5190 | ✅ | ✅ | ✅ | ✅ | ❌ |
| L5290 | ✅ | ✅ | ✅ | ✅ | ❌ |
| L6490 | ✅ | ✅ | ✅ | ❌ | ✅ |

## 💡 Características do Sistema

### Inteligência
- **Filtragem progressiva**: Elimina opções a cada resposta
- **Detecção precoce**: Para quando identifica modelo único
- **Máximo 5 perguntas**: Otimizado para rapidez

### Flexibilidade
- **"Não sei"**: Pula característica sem filtrar
- **Cancelamento**: Botão para parar processo
- **Seleção manual**: Sempre disponível na sidebar

### Experiência do Usuário
- **Botões interativos**: Respostas com um clique
- **Feedback visual**: Mostra progresso e resultados
- **Pergunta pendente**: Processa após identificação

## 🔧 Implementação Técnica

### Estados do Sistema
```python
st.session_state.funnel_active    # Afunilamento ativo?
st.session_state.funnel_stage     # Estágio atual (1-6)
st.session_state.funnel_answers   # Respostas coletadas
st.session_state.pending_question # Pergunta aguardando
```

### Funções Principais
```python
start_funnel()                    # Inicia processo
get_funnel_question()             # Retorna próxima pergunta
process_funnel_answer()           # Processa resposta
filter_printers_by_features()     # Filtra modelos
```

## 📈 Casos de Uso

### Exemplo 1: Identificação Rápida
```
Usuário: "Como trocar a tinta?"
Sistema: "Sua impressora é multifuncional?"
Usuário: "Não, só imprime"
Sistema: "Suporta papel A3?"
Usuário: "Sim"
Sistema: ✅ Identificada L1300
```

### Exemplo 2: Múltiplas Características
```
Usuário: "Papel emperrado"
Sistema: "É multifuncional?"
Usuário: "Sim"
Sistema: "Tem duplex?"
Usuário: "Sim"
Sistema: "Tem ADF?"
Usuário: "Sim"
Sistema: "Tem FAX?"
Usuário: "Não"
Sistema: ✅ L4150 ou L4260 (mostra opções)
```

## 🚀 Vantagens

1. **Sem frustração**: Não força usuário a saber modelo
2. **Rápido**: Máximo 5 perguntas simples
3. **Preciso**: Identifica modelo correto
4. **Intuitivo**: Perguntas claras com exemplos
5. **Flexível**: Permite pular ou cancelar

## 📝 Notas

- Sistema espelha lógica do `chatbot_chromadb.py`
- Integrado com detecção automática de texto
- Compatível com todos os modelos no ChromaDB
- Mantém histórico de conversação

---

**Versão**: 1.0 | **Status**: ✅ Implementado e Funcionando
