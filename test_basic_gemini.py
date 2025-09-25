#!/usr/bin/env python3
"""
Teste com configuração mais básica do Gemini
"""
import google.generativeai as genai

API_KEY = "AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk"
genai.configure(api_key=API_KEY)

print("🔍 Testando modelos básicos e alternativos...\n")

# Lista todos os modelos disponíveis
print("📋 Listando modelos disponíveis:")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"   • {m.name}")
except Exception as e:
    print(f"   ❌ Erro ao listar: {e}")

print("\n🧪 Tentando text-bison-001 (modelo legacy):")
try:
    model = genai.GenerativeModel('text-bison-001')
    response = model.generate_content("Say: OK")
    print(f"   ✅ Funcionou: {response.text}")
except Exception as e:
    print(f"   ❌ Erro: {str(e)[:100]}")

print("\n🧪 Tentando gemini-pro (sem versão):")
try:
    model = genai.GenerativeModel('models/gemini-pro')  # Com prefixo models/
    response = model.generate_content("Say: OK")
    print(f"   ✅ Funcionou: {response.text}")
except Exception as e:
    print(f"   ❌ Erro: {str(e)[:100]}...")
    
print("\n🧪 Tentando chat-bison-001:")
try:
    model = genai.GenerativeModel('chat-bison-001')
    response = model.generate_content("Say: OK")
    print(f"   ✅ Funcionou: {response.text}")
except Exception as e:
    print(f"   ❌ Erro: {str(e)[:100]}")
