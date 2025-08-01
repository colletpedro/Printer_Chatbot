#!/bin/bash
# Script de conveniência para executar o webhook server
cd "$(dirname "$0")"
source venv/bin/activate
WEBHOOK_SECRET="webhook-secret-123" python webhook/webhook_server.py 