@echo off
echo ========================================
echo    RADAR SINISTRO API - INICIALIZADOR
echo ========================================
echo.

echo [1] Verificando dependencias...
python -c "import fastapi, uvicorn; print('✅ Dependencias OK')" 2>nul || (echo ❌ Instalando dependencias... && pip install fastapi uvicorn[standard] --quiet && echo ✅ Dependencias instaladas)

echo.
echo [2] Testando importacao da API...
python -c "import sys; sys.path.append('.'); from api.main import app; print('✅ API carregada com sucesso')" || (echo ❌ Erro ao carregar API && pause && exit /b 1)

echo.
echo [3] Iniciando servidor da API...
echo.
echo 📍 A API estará disponível em:
echo    • Documentação: http://localhost:8000/docs
echo    • ReDoc: http://localhost:8000/redoc  
echo    • Health Check: http://localhost:8000/health
echo    • Base URL: http://localhost:8000/api/v1
echo.
echo ⚠️  Para parar o servidor, pressione Ctrl+C
echo.

python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000