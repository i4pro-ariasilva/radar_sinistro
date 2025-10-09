# Script para executar a aplicação Streamlit
# Execute este arquivo para iniciar a interface web

Write-Host "🌦️ Iniciando Sistema de Radar de Risco Climático - Interface Streamlit" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# Verificar se está no diretório correto
if (-not (Test-Path "streamlit_app\app.py")) {
    Write-Host "❌ Erro: Execute este script a partir do diretório raiz do projeto (radar_sinistro)" -ForegroundColor Red
    Write-Host "💡 Navegue até o diretório radar_sinistro e execute novamente" -ForegroundColor Yellow
    pause
    exit 1
}

# Verificar se Streamlit está instalado
Write-Host "🔍 Verificando dependências..." -ForegroundColor Yellow

try {
    streamlit --version | Out-Null
    Write-Host "✅ Streamlit encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Streamlit não encontrado. Instalando dependências..." -ForegroundColor Red
    Write-Host "📦 Executando: pip install -r requirements.txt" -ForegroundColor Yellow
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erro na instalação das dependências" -ForegroundColor Red
        pause
        exit 1
    }
}

# Verificar se o banco de dados existe
if (-not (Test-Path "radar_climatico.db")) {
    Write-Host "⚠️ Banco de dados não encontrado. Será criado automaticamente." -ForegroundColor Yellow
    Write-Host "💡 Use a opção 'Inicializar Sistema' na interface para configurar" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "🚀 Iniciando aplicação Streamlit..." -ForegroundColor Green
Write-Host "📱 A interface será aberta em: http://localhost:8501" -ForegroundColor Cyan
Write-Host "⏹️ Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host ""

# Executar Streamlit
streamlit run streamlit_app/app.py