# Sistema de Auto-Reload da Base de Conhecimento

## 📋 Visão Geral

O sistema de auto-reload garante que o chatbot sempre tenha acesso às informações mais atualizadas, detectando automaticamente quando novos PDFs são adicionados via webhook e recarregando a base de conhecimento.

## 🔄 Como Funciona

### 1. **Verificação na Inicialização**
- Toda vez que o `chatbot.py` é executado, ele verifica se houve atualizações recentes
- Compara o timestamp da última atualização do webhook com a modificação do arquivo `manual_complete.json`
- Mostra o status da atualização na tela

### 2. **Verificação Automática Durante Execução**
- A cada **5 perguntas**, o chatbot verifica automaticamente se há atualizações
- Se detectar uma atualização, recarrega a base automaticamente
- Atualiza a lista de modelos disponíveis

### 3. **Comando Manual de Reload**
- Digite `reload` para forçar uma verificação manual
- Útil quando você sabe que adicionou um PDF recentemente

## 🛠️ Funcionalidades Implementadas

### `check_and_reload_manual()`
```python
# Verifica se há atualizações comparando timestamps
# Retorna: (bool, string) - (foi_atualizado, status_message)
```

### `reload_knowledge_base_if_updated()`
```python
# Recarrega a base de conhecimento se detectar atualizações
# Atualiza automaticamente a variável global knowledge_base
```

### Integração no Loop Principal
- Verificação automática a cada 5 perguntas
- Comando `reload` para verificação manual
- Contador de perguntas para controle

## 📊 Fluxo de Funcionamento

```
1. Novo PDF adicionado no Google Drive
   ↓
2. Webhook detecta mudança
   ↓
3. webhook_server.py executa update_drive.py
   ↓
4. manual_complete.json é atualizado
   ↓
5. Atividade é registrada em webhook_activity.json
   ↓
6. chatbot.py detecta a atualização (automática ou manual)
   ↓
7. Base de conhecimento é recarregada
   ↓
8. Novos modelos ficam disponíveis automaticamente
```

## 🎯 Benefícios

1. **Automático**: Não precisa reiniciar o chatbot manualmente
2. **Inteligente**: Só recarrega quando realmente há atualizações
3. **Transparente**: Mostra o status das atualizações
4. **Eficiente**: Verificação periódica sem impacto na performance
5. **Flexível**: Permite verificação manual quando necessário

## 🔧 Comandos Disponíveis

| Comando | Função |
|---------|--------|
| `reload` | Verifica e recarrega manualmente |
| `modo rapido` | Alterna para respostas concisas |
| `modo detalhado` | Alterna para respostas completas |
| `sair` | Encerra o programa |

## 📝 Logs e Status

### Na Inicialização:
```
🔍 Verificando atualizações recentes...
   ✅ Manual atualizado recentemente (14:39:01)
```

### Durante Execução:
```
🔍 Verificando atualizações automáticas...

🔄 Detectada atualização na base de conhecimento!
   Recarregando manual...
   ✅ Base atualizada: 3099 → 3150 seções
   📱 Modelos disponíveis: 7
```

## ⚠️ Considerações Técnicas

- **Tolerância de Tempo**: 5 minutos entre timestamps para evitar falsos positivos
- **Verificação Periódica**: A cada 5 perguntas para balancear eficiência e atualização
- **Fallback**: Em caso de erro, mantém a base atual funcionando
- **Thread-Safe**: Usa variável global com cuidado para evitar conflitos

## 🚀 Resultado Final

Agora, quando você adicionar um novo PDF no Google Drive:

1. ✅ O webhook detecta automaticamente
2. ✅ A base de conhecimento é atualizada
3. ✅ O chatbot detecta a atualização
4. ✅ Novos modelos ficam disponíveis automaticamente
5. ✅ Não é necessário reiniciar nada manualmente

**O sistema está completamente automatizado!** 🎉 