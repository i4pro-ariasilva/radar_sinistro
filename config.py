"""
Configurações do Sistema Radar de Sinistro v3.0
===============================================

Configurações centralizadas com validação automática
"""

import os
import logging
from pathlib import Path
from typing import List

# Configuração de logging sem emojis para Windows
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': 'logs/radar_sistema.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

# Diretórios do sistema
REQUIRED_DIRECTORIES = [
    'data/raw',
    'data/processed', 
    'data/sample',
    'data/exports',
    'logs',
    'models',
    'cache'
]

def create_directories():
    """Cria estrutura de diretórios necessários"""
    logger = logging.getLogger(__name__)
    
    for directory in REQUIRED_DIRECTORIES:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Diretório criado/verificado: {directory}")

def validate_config() -> List[str]:
    """
    Valida configurações do sistema
    
    Returns:
        Lista de erros encontrados (vazia se tudo OK)
    """
    errors = []
    
    # Verificar diretórios obrigatórios
    for directory in REQUIRED_DIRECTORIES:
        if not Path(directory).exists():
            errors.append(f"Diretório não encontrado: {directory}")
    
    # REMOVIDO: Verificação de OPENWEATHER_API_KEY
    # O sistema agora usa OpenMeteo API que é gratuita e não requer chave
    
    # Verificar permissões de escrita
    try:
        test_file = Path('logs/test_write.tmp')
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        errors.append(f"Sem permissão de escrita no diretório logs: {e}")
    
    # Verificar espaço em disco (básico)
    import shutil
    try:
        total, used, free = shutil.disk_usage('.')
        free_gb = free / (1024**3)
        if free_gb < 1.0:  # Menos de 1GB livre
            errors.append(f"Pouco espaço em disco: {free_gb:.1f}GB livres")
    except Exception:
        pass  # Não crítico
    
    return errors

# Configurações específicas do modelo ML
ML_CONFIG = {
    'random_state': 42,
    'test_size': 0.2,
    'cv_folds': 5,
    'early_stopping_rounds': 50,
    'max_features': 100
}

# Configurações do Weather Service
WEATHER_CONFIG = {
    'cache_ttl_hours': 1,
    'cache_db_path': 'cache/weather_cache.db',
    'api_timeout_seconds': 10,
    'api_retries': 3,
    'fallback_enabled': True
}

# Configurações do banco de dados
DATABASE_CONFIG = {
    'db_path': 'data/radar_sinistro.db',
    'backup_enabled': True,
    'backup_interval_hours': 24
}

if __name__ == "__main__":
    # Teste da configuração
    print("TESTANDO CONFIGURAÇÕES...")
    
    create_directories()
    errors = validate_config()
    
    if errors:
        print("ERROS ENCONTRADOS:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("SUCESSO - Todas as configurações estão corretas!")
        print(f"Diretórios: {len(REQUIRED_DIRECTORIES)} criados/verificados")
        print("OpenMeteo API: Não requer chave (serviço gratuito)")
