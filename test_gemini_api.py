#!/usr/bin/env python3
"""
Teste da API do Gemini - Verifica se a API key está funcionando
"""
import google.generativeai as genai

# Testa com a mesma API key
API_KEY = "AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk"
genai.configure(api_key=API_KEY)

print("🔍 Testando API do Gemini...\n")

# Testa diferentes modelos
models_to_test = [
    'gemini-1.5-flash-latest',
    'gemini-1.5-flash',
    'gemini-1.5-pro-latest',
    'gemini-1.5-pro',
    'gemini-pro',
    'gemini-1.0-pro'
]

for model_name in models_to_test:
    print(f"📝 Testando modelo: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Responda apenas: OK")
        
        if response and response.text:
            print(f"   ✅ {model_name} funcionando!")
            print(f"   Resposta: {response.text.strip()[:50]}")
        else:
            print(f"   ⚠️  {model_name} - sem resposta")
            
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print(f"   ❌ {model_name} - Modelo não encontrado (404)")
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            print(f"   ⚠️  {model_name} - Problema de cota/limite")
        elif "api" in error_msg.lower() and "key" in error_msg.lower():
            print(f"   🔑 {model_name} - Problema com API key")
        else:
            print(f"   ❌ {model_name} - Erro: {error_msg[:100]}")
    
    print()

print("\n📊 RESUMO:")
print("Se TODOS falharam → Problema com API key ou conta")
print("Se ALGUNS funcionam → Use o modelo que funcionou")
