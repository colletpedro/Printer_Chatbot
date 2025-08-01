#!/bin/bash
# Script de conveniência para renovar webhook
cd "$(dirname "$0")"
source venv/bin/activate
python webhook/renew_webhook.py 