"""
Configurações específicas do banco de dados
"""

import os
import sqlite3
from typing import Dict, Any
from .settings import DATABASE_CONFIG, BASE_DIR


class DatabaseConfig:
    """Classe para gerenciar configurações do banco de dados"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DATABASE_CONFIG['default_db_path']
        self.backup_dir = DATABASE_CONFIG['backup_dir']
        self.connection_timeout = DATABASE_CONFIG['connection_timeout']
        self.enable_foreign_keys = DATABASE_CONFIG['enable_foreign_keys']
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Retorna parâmetros para conexão com o banco"""
        return {
            'database': self.db_path,
            'timeout': self.connection_timeout,
            'check_same_thread': False,
            'isolation_level': None  # Autocommit mode
        }
    
    def get_pragma_settings(self) -> list:
        """Retorna configurações PRAGMA para SQLite"""
        pragmas = [
            "PRAGMA journal_mode=WAL;",  # Write-Ahead Logging para performance
            "PRAGMA synchronous=NORMAL;",  # Balanceamento performance/segurança
            "PRAGMA cache_size=10000;",  # Cache de 10MB
            "PRAGMA temp_store=MEMORY;",  # Armazenar temporários na memória
        ]
        
        if self.enable_foreign_keys:
            pragmas.append("PRAGMA foreign_keys=ON;")
        
        return pragmas
    
    def create_backup_path(self, backup_name: str = None) -> str:
        """Cria caminho para backup do banco"""
        if not backup_name:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"radar_backup_{timestamp}.db"
        
        return os.path.join(self.backup_dir, backup_name)
    
    def validate_database_file(self) -> Dict[str, Any]:
        """Valida se o arquivo de banco está acessível e válido"""
        result = {
            'exists': False,
            'readable': False,
            'writable': False,
            'valid_sqlite': False,
            'size_mb': 0,
            'tables_count': 0,
            'errors': []
        }
        
        try:
            # Verificar se arquivo existe
            if os.path.exists(self.db_path):
                result['exists'] = True
                
                # Verificar tamanho
                size_bytes = os.path.getsize(self.db_path)
                result['size_mb'] = round(size_bytes / (1024 * 1024), 2)
                
                # Verificar permissões
                result['readable'] = os.access(self.db_path, os.R_OK)
                result['writable'] = os.access(self.db_path, os.W_OK)
                
                # Verificar se é SQLite válido
                if result['readable']:
                    conn = sqlite3.connect(self.db_path)
                    try:
                        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = cursor.fetchall()
                        result['valid_sqlite'] = True
                        result['tables_count'] = len(tables)
                    except sqlite3.Error as e:
                        result['errors'].append(f"Erro SQLite: {e}")
                    finally:
                        conn.close()
            else:
                result['errors'].append("Arquivo de banco não existe")
        
        except Exception as e:
            result['errors'].append(f"Erro ao validar banco: {e}")
        
        return result
    
    def optimize_database(self, db_path: str = None) -> bool:
        """Otimiza o banco de dados"""
        target_db = db_path or self.db_path
        
        try:
            conn = sqlite3.connect(target_db)
            
            # Executar otimizações
            optimization_commands = [
                "VACUUM;",
                "REINDEX;",
                "ANALYZE;",
                "PRAGMA optimize;"
            ]
            
            for command in optimization_commands:
                conn.execute(command)
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"Erro ao otimizar banco: {e}")
            return False
    
    def get_database_stats(self, db_path: str = None) -> Dict[str, Any]:
        """Retorna estatísticas do banco de dados"""
        target_db = db_path or self.db_path
        stats = {}
        
        try:
            conn = sqlite3.connect(target_db)
            
            # Informações básicas
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            stats['tables'] = tables
            stats['table_count'] = len(tables)
            
            # Contagem de registros por tabela
            table_counts = {}
            for table in tables:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                except sqlite3.Error:
                    table_counts[table] = 'Erro'
            
            stats['record_counts'] = table_counts
            stats['total_records'] = sum(
                count for count in table_counts.values() 
                if isinstance(count, int)
            )
            
            # Tamanho das páginas
            cursor = conn.execute("PRAGMA page_size;")
            page_size = cursor.fetchone()[0]
            stats['page_size'] = page_size
            
            cursor = conn.execute("PRAGMA page_count;")
            page_count = cursor.fetchone()[0]
            stats['page_count'] = page_count
            stats['estimated_size_mb'] = round((page_size * page_count) / (1024 * 1024), 2)
            
            conn.close()
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats


# Configurações específicas por ambiente
ENVIRONMENT_CONFIGS = {
    'development': {
        'db_name': 'radar_climatico_dev.db',
        'enable_query_logging': True,
        'auto_backup': False,
        'connection_pool_size': 1
    },
    'testing': {
        'db_name': ':memory:',
        'enable_query_logging': False,
        'auto_backup': False,
        'connection_pool_size': 1
    },
    'production': {
        'db_name': 'radar_climatico_prod.db',
        'enable_query_logging': False,
        'auto_backup': True,
        'connection_pool_size': 5,
        'backup_schedule': 'daily'
    }
}


def get_database_config(environment: str = 'development') -> DatabaseConfig:
    """Retorna configuração do banco para o ambiente especificado"""
    env_config = ENVIRONMENT_CONFIGS.get(environment, ENVIRONMENT_CONFIGS['development'])
    
    if env_config['db_name'] == ':memory:':
        db_path = ':memory:'
    else:
        db_path = os.path.join(BASE_DIR, env_config['db_name'])
    
    config = DatabaseConfig(db_path)
    
    # Aplicar configurações específicas do ambiente
    for key, value in env_config.items():
        if key != 'db_name':
            setattr(config, key, value)
    
    return config


# Instância padrão para desenvolvimento
default_db_config = get_database_config('development')


if __name__ == "__main__":
    # Teste das configurações
    config = get_database_config('development')
    
    print("Configurações do banco:")
    print(f"  Caminho: {config.db_path}")
    print(f"  Timeout: {config.connection_timeout}s")
    print(f"  Foreign Keys: {config.enable_foreign_keys}")
    
    # Validar banco se existe
    validation = config.validate_database_file()
    print(f"\nValidação do banco:")
    for key, value in validation.items():
        print(f"  {key}: {value}")
    
    # Estatísticas se banco válido
    if validation['valid_sqlite']:
        stats = config.get_database_stats()
        print(f"\nEstatísticas:")
        for key, value in stats.items():
            print(f"  {key}: {value}")