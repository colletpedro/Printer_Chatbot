#!/usr/bin/env python3
import asyncio
import time
import json
from pathlib import Path
import sys

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.workers.migration import process_drive_updates
from src.core.models import WebhookEvent

async def auto_monitor():
    """Monitor automático que verifica mudanças periodicamente"""
    
    print("🤖 MONITOR AUTOMÁTICO ATIVO")
    print("=" * 50)
    print("🔄 Verificando mudanças a cada 5 minutos...")
    print("📁 Novos PDFs serão processados automaticamente")
    print("⏹️ Pressione Ctrl+C para parar")
    print("=" * 50)
    print()
    
    while True:
        try:
            print(f"🔍 [{time.strftime('%H:%M:%S')}] Verificando novos PDFs...")
            
            # Simula evento de webhook
            event = WebhookEvent(
                channel_id="auto-monitor",
                resource_state="update"
            )
            
            # Processa atualizações
            result = await process_drive_updates(event)
            
            if result.success:
                if result.processed_files:
                    print(f"✅ Processados {len(result.processed_files)} arquivos:")
                    for file in result.processed_files:
                        print(f"   📄 {file}")
                    print(f"🧩 Total de seções: {result.total_sections}")
                else:
                    print("ℹ️ Nenhum arquivo novo detectado")
            else:
                print("❌ Erro no processamento:")
                for error in result.errors:
                    print(f"   • {error}")
            
            print(f"⏳ Próxima verificação em 5 minutos...")
            print()
            
            # Aguarda 5 minutos
            await asyncio.sleep(300)
            
        except KeyboardInterrupt:
            print("\n⏹️ Monitor automático interrompido")
            break
        except Exception as e:
            print(f"❌ Erro no monitor: {e}")
            await asyncio.sleep(60)  # Aguarda 1 minuto em caso de erro

if __name__ == "__main__":
    asyncio.run(auto_monitor())
