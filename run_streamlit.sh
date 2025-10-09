#!/bin/bash

# Script para executar a aplicação Streamlit no Linux/Mac
# Execute: chmod +x run_streamlit.sh && ./run_streamlit.sh

echo "🌦️ Iniciando Sistema de Radar de Risco Climático - Interface Streamlit"
echo "================================================================="

# Verificar se está no diretório correto
if [ ! -f "streamlit_app/app.py" ]; then
    echo "❌ Erro: Execute este script a partir do diretório raiz do projeto (radar_sinistro)"
    echo "💡 Navegue até o diretório radar_sinistro e execute novamente"
    exit 1
fi

# Verificar se Streamlit está instalado
echo "🔍 Verificando dependências..."

if command -v streamlit &> /dev/null; then
    echo "✅ Streamlit encontrado"
else
    echo "❌ Streamlit não encontrado. Instalando dependências..."
    echo "📦 Executando: pip install -r requirements.txt"
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "❌ Erro na instalação das dependências"
        exit 1
    fi
fi

# Verificar se o banco de dados existe
if [ ! -f "radar_climatico.db" ]; then
    echo "⚠️ Banco de dados não encontrado. Será criado automaticamente."
    echo "💡 Use a opção 'Inicializar Sistema' na interface para configurar"
fi

echo ""
echo "🚀 Iniciando aplicação Streamlit..."
echo "📱 A interface será aberta em: http://localhost:8501"
echo "⏹️ Pressione Ctrl+C para parar o servidor"
echo ""

# Executar Streamlit
streamlit run streamlit_app/app.py