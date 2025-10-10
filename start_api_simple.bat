@echo off
echo ========================================
echo    RADAR SINISTRO API - INICIO RAPIDO
echo ========================================
echo.
echo Iniciando API em http://localhost:8000
echo.
echo Documentacao disponivel em:
echo   http://localhost:8000/docs
echo.
echo Pressione Ctrl+C para parar
echo.

python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000