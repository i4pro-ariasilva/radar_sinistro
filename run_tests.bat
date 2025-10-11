@echo off
REM Script para executar testes do Radar de Sinistro
REM Uso: run_tests.bat [categoria]
REM Categorias: api, web, services, ml, database, all

echo 🌦️ RADAR DE SINISTRO - EXECUTAR TESTES
echo =======================================

IF "%1"=="" (
    echo 📋 Executando TODOS os testes...
    python tests\run_all_tests.py
    GOTO :END
)

IF "%1"=="api" (
    echo 🔧 Executando testes de API...
    python -m unittest tests.test_api -v
    GOTO :END
)

IF "%1"=="web" (
    echo 🌐 Executando testes de módulos web...
    python -m unittest tests.test_web_modules -v
    GOTO :END
)

IF "%1"=="services" (
    echo ⚙️ Executando testes de serviços...
    python -m unittest tests.test_services -v
    GOTO :END
)

IF "%1"=="ml" (
    echo 🤖 Executando testes de Machine Learning...
    python -m unittest tests.test_ml_modules -v
    GOTO :END
)

IF "%1"=="database" (
    echo 🗄️ Executando testes de banco de dados...
    python -m unittest tests.test_database -v
    GOTO :END
)

IF "%1"=="all" (
    echo 📋 Executando TODOS os testes...
    python tests\run_all_tests.py
    GOTO :END
)

echo ❌ Categoria inválida: %1
echo 📖 Categorias disponíveis: api, web, services, ml, database, all

:END
echo.
echo ✅ Execução finalizada!
pause