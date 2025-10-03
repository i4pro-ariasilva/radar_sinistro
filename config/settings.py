"""
Configurações principais do sistema
"""

import os
from pathlib import Path

# Diretório base do projeto
BASE_DIR = Path(__file__).parent.parent

# Configurações do banco de dados
DATABASE_CONFIG = {
    'default_db_path': os.path.join(BASE_DIR, 'radar_climatico.db'),
    'backup_dir': os.path.join(BASE_DIR, 'backups'),
    'connection_timeout': 30.0,
    'enable_foreign_keys': True
}

# Configurações de dados
DATA_CONFIG = {
    'raw_data_dir': os.path.join(BASE_DIR, 'data', 'raw'),
    'processed_data_dir': os.path.join(BASE_DIR, 'data', 'processed'),
    'cache_dir': os.path.join(BASE_DIR, 'data', 'cache'),
    'sample_data_dir': os.path.join(BASE_DIR, 'data', 'sample'),
    'max_file_size_mb': 100,
    'supported_formats': ['csv', 'xlsx', 'xls', 'json', 'parquet']
}

# Configurações de APIs externas
API_CONFIG = {
    'weather': {
        'openweather_api_key': os.getenv('OPENWEATHER_API_KEY', ''),
        'inmet_base_url': 'https://apitempo.inmet.gov.br/estacao/',
        'cache_timeout_hours': 1,
        'max_requests_per_minute': 60
    },
    'geocoding': {
        'nominatim_base_url': 'https://nominatim.openstreetmap.org/',
        'cache_timeout_days': 30,
        'request_delay_seconds': 1
    }
}

# Configurações do modelo ML
MODEL_CONFIG = {
    'model_dir': os.path.join(BASE_DIR, 'models'),
    'model_filename': 'radar_modelo.pkl',
    'scaler_filename': 'feature_scaler.pkl',
    'feature_columns': [
        'chuva_mm', 'vento_kmh', 'temperatura_max', 'valor_residencia',
        'proximidade_rio_km', 'tipo_residencia_enc', 'cep_enc'
    ],
    'target_column': 'houve_sinistro',
    'test_size': 0.3,
    'random_state': 42
}

# Configurações de risco
RISK_CONFIG = {
    'score_thresholds': {
        'baixo': 25,
        'medio': 50,
        'alto': 75,
        'critico': 100
    },
    'alert_threshold': 70,
    'prediction_cache_hours': 6,
    'weather_influence_factors': {
        'chuva_weight': 0.4,
        'vento_weight': 0.3,
        'temperatura_weight': 0.1,
        'historico_weight': 0.2
    }
}

# Configurações da API web
WEB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5000,
    'debug': True,
    'cors_enabled': True,
    'max_content_length': 16 * 1024 * 1024,  # 16MB
    'rate_limit_per_minute': 100
}

# Configurações de logging
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_dir': os.path.join(BASE_DIR, 'logs'),
    'max_file_size_mb': 10,
    'backup_count': 5
}

# Configurações de validação
VALIDATION_CONFIG = {
    'cep_pattern': r'^\d{5}-\d{3}$',
    'policy_number_min_length': 5,
    'policy_number_max_length': 20,
    'min_insurance_value': 10000,
    'max_insurance_value': 5000000,
    'valid_residence_types': ['casa', 'apartamento', 'sobrado'],
    'brazil_lat_bounds': (-33.75, 5.27),
    'brazil_lon_bounds': (-73.98, -28.84)
}

# Configurações de qualidade de dados
QUALITY_CONFIG = {
    'min_completeness_percentage': 80,
    'min_validity_percentage': 90,
    'max_duplicate_percentage': 5,
    'outlier_detection_method': 'iqr',
    'outlier_factor': 1.5
}

# Configurações do frontend
FRONTEND_CONFIG = {
    'map_default_center': [-15.7801, -47.9292],  # Brasília
    'map_default_zoom': 5,
    'map_provider': 'OpenStreetMap',
    'refresh_interval_seconds': 300,  # 5 minutos
    'max_policies_display': 1000
}

# Configurações de teste
TEST_CONFIG = {
    'test_db_path': ':memory:',
    'sample_data_size': 100,
    'mock_api_responses': True,
    'test_timeout_seconds': 30
}

# Função para criar diretórios necessários
def create_directories():
    """Cria diretórios necessários se não existirem"""
    directories = [
        DATABASE_CONFIG['backup_dir'],
        DATA_CONFIG['raw_data_dir'],
        DATA_CONFIG['processed_data_dir'],
        DATA_CONFIG['cache_dir'],
        DATA_CONFIG['sample_data_dir'],
        MODEL_CONFIG['model_dir'],
        LOGGING_CONFIG['log_dir']
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Função para validar configurações
def validate_config():
    """Valida se as configurações estão corretas"""
    errors = []
    
    # Verificar se diretório base existe
    if not BASE_DIR.exists():
        errors.append(f"Diretório base não encontrado: {BASE_DIR}")
    
    # Verificar configurações de API
    if not API_CONFIG['weather']['openweather_api_key']:
        errors.append("OPENWEATHER_API_KEY não configurada")
    
    # Verificar limites de validação
    if VALIDATION_CONFIG['min_insurance_value'] >= VALIDATION_CONFIG['max_insurance_value']:
        errors.append("Limites de valor de seguro inválidos")
    
    return errors

# Função para obter configuração por ambiente
def get_config_for_environment(env: str = 'development'):
    """Retorna configurações específicas para o ambiente"""
    if env == 'production':
        config = {
            **globals(),
            'WEB_CONFIG': {
                **WEB_CONFIG,
                'debug': False,
                'host': '0.0.0.0'
            },
            'LOGGING_CONFIG': {
                **LOGGING_CONFIG,
                'level': 'WARNING'
            }
        }
    elif env == 'testing':
        config = {
            **globals(),
            'DATABASE_CONFIG': {
                **DATABASE_CONFIG,
                'default_db_path': TEST_CONFIG['test_db_path']
            },
            'LOGGING_CONFIG': {
                **LOGGING_CONFIG,
                'level': 'DEBUG'
            }
        }
    else:  # development
        config = globals()
    
    return config

# Carregar configurações do ambiente ao importar
if __name__ == "__main__":
    # Criar diretórios necessários
    create_directories()
    
    # Validar configurações
    errors = validate_config()
    if errors:
        print("Erros de configuração encontrados:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configurações validadas com sucesso!")