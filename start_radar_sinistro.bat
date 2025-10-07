@echo off
cls
echo ====================================================
echo    🌦️ RADAR DE SINISTRO v3.0 - INICIALIZADOR
echo ====================================================
echo.
echo Sistema Inteligente de Predição de Riscos Climáticos
echo.

REM Definir diretório do projeto
cd /d "%~dp0"

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Python não encontrado!
    echo.
    echo Por favor, instale o Python 3.8 ou superior:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ Python encontrado
python --version

REM Verificar se Streamlit está instalado
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Streamlit não encontrado. Instalando dependências...
    echo.
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Erro ao instalar dependências!
        pause
        exit /b 1
    )
) else (
    echo ✅ Streamlit encontrado
)

REM Verificar estrutura do projeto
if not exist "app.py" (
    echo ❌ ERRO: Arquivo app.py não encontrado!
    echo Certifique-se de estar no diretório correto do projeto.
    pause
    exit /b 1
)

if not exist "database" mkdir database

echo.
echo ====================================================
echo 🚀 INICIANDO RADAR DE SINISTRO...
echo ====================================================
echo.
echo 📝 Logs do sistema serão exibidos abaixo
echo 🌐 O navegador abrirá automaticamente em: http://localhost:8501
echo 🔄 Para parar o sistema, pressione Ctrl+C
echo.
echo ====================================================
echo.

REM Iniciar Streamlit
streamlit run app.py --server.port 8501 --server.headless false

REM Se chegou aqui, o Streamlit foi fechado
echo.
echo ====================================================
echo 🛑 RADAR DE SINISTRO FINALIZADO
echo ====================================================
echo.
pause