#!/usr/bin/env python3
"""
Teste final com modelo correto
"""
import google.generativeai as genai

API_KEY = "AIzaSyDjejxDFqTSg_i-KDnS2QqsXdiWLydIrSk"
genai.configure(api_key=API_KEY)

print("🧪 Testando configuração final...\n")

# Testa exatamente como no código
try:
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    print("✅ Modelo principal carregado: models/gemini-2.5-flash")
    
    # Testa pergunta simples
    response = model.generate_content("Como trocar tinta de impressora Epson L3110?")
    print(f"\n📝 Resposta: {response.text[:200]}...")
    print("\n✅ TUDO FUNCIONANDO!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    print("\nTentando fallback...")
    
    try:
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        response = model.generate_content("Como trocar tinta?")
        print(f"✅ Fallback funcionou: {response.text[:100]}...")
    except Exception as e2:
        print(f"❌ Fallback também falhou: {e2}")
