#!/bin/bash
echo "🔍 Verificando se há menções a etiqueta no código..."
grep -n "etiqueta" app_streamlit.py | grep -i "modelo" || echo "✅ NENHUMA menção a etiqueta com modelo encontrada!"
echo ""
echo "📊 Última modificação do arquivo:"
ls -la app_streamlit.py | awk "{print \$6, \$7, \$8}"
echo ""
echo "📝 Total de linhas no arquivo:"
wc -l app_streamlit.py

