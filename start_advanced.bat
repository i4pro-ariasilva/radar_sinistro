@echo off
REM ====================================================
REM    CONFIGURAÇÕES DO RADAR DE SINISTRO
REM ====================================================

REM Porta do servidor (padrão: 8501)
set STREAMLIT_PORT=8501

REM Modo headless (true/false) - false abre o navegador automaticamente
set STREAMLIT_HEADLESS=false

REM Tema (light/dark/auto)
set STREAMLIT_THEME=auto

REM Nível de log (error/warning/info/debug)
set STREAMLIT_LOG_LEVEL=info

REM ====================================================

cd /d "%~dp0"

echo ====================================================
echo    🌦️ RADAR DE SINISTRO v3.0 - MODO AVANÇADO
echo ====================================================
echo.
echo Configurações:
echo   • Porta: %STREAMLIT_PORT%
echo   • Headless: %STREAMLIT_HEADLESS%
echo   • Tema: %STREAMLIT_THEME%
echo   • Log Level: %STREAMLIT_LOG_LEVEL%
echo.
echo ====================================================
echo.

streamlit run app.py ^
    --server.port %STREAMLIT_PORT% ^
    --server.headless %STREAMLIT_HEADLESS% ^
    --theme.base %STREAMLIT_THEME% ^
    --logger.level %STREAMLIT_LOG_LEVEL%

echo.
echo Sistema finalizado.
pause