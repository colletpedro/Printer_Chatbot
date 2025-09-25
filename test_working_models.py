#!/usr/bin/env python3
"""
Teste com modelos que aparecem disponíveis
"""
import google.generativeai as genai

API_KEY = "AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk"
genai.configure(api_key=API_KEY)

print("🔍 Testando modelos DISPONÍVEIS com prefixo models/...\n")

# Testa os modelos que aparecem na lista
models_to_test = [
    'models/gemini-2.0-flash',       # Novo!
    'models/gemini-2.5-flash',       # Mais novo!
    'models/gemini-1.5-flash-8b',   # Versão leve
    'models/gemini-1.5-flash',      # Original
    'models/gemini-1.5-pro',        # Pro
]

working_models = []

for model_name in models_to_test:
    print(f"📝 Testando: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Responda apenas: OK")
        
        if response and response.text:
            print(f"   ✅ FUNCIONANDO! Resposta: {response.text.strip()[:30]}")
            working_models.append(model_name)
        else:
            print(f"   ⚠️  Sem resposta")
            
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "limit" in error_msg.lower():
            print(f"   ⚠️  Limite/cota excedido")
        else:
            print(f"   ❌ Erro: {error_msg[:80]}...")
    print()

print("\n✅ MODELOS QUE FUNCIONAM:")
for m in working_models:
    print(f"   • {m}")
    
if working_models:
    print(f"\n🎯 RECOMENDADO: Usar '{working_models[0]}'")
