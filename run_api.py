"""
Script para executar a API do Radar Sinistro
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_api():
    """Executa a API em modo de produção"""
    print("🎯 Iniciando Radar Sinistro API...")
    print("📍 URL: http://localhost:5000")
    print("📚 Documentação: http://localhost:5000/docs")
    print("🔍 ReDoc: http://localhost:5000/redoc")
    print("=" * 50)
    
    try:
        import uvicorn
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=5000,
            reload=False
        )
    except ImportError:
        print("❌ Erro: uvicorn não está instalado")
        print("Execute: pip install uvicorn")
    except Exception as e:
        print(f"❌ Erro ao iniciar API: {e}")

def run_dev():
    """Executa a API em modo de desenvolvimento"""
    print("🚀 Iniciando Radar Sinistro API (Modo Desenvolvimento)...")
    print("📍 URL: http://localhost:5000")
    print("📚 Documentação: http://localhost:5000/docs")
    print("🔍 ReDoc: http://localhost:5000/redoc")
    print("🔄 Auto-reload ativado")
    print("=" * 50)
    
    try:
        import uvicorn
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=5000,
            reload=True,
            reload_dirs=["api"]
        )
    except ImportError:
        print("❌ Erro: uvicorn não está instalado")
        print("Execute: pip install uvicorn")
    except Exception as e:
        print(f"❌ Erro ao iniciar API: {e}")

if __name__ == "__main__":
    # Verificar argumentos
    if len(sys.argv) > 1 and sys.argv[1] == "--dev":
        run_dev()
    else:
        run_api()