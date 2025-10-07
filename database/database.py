"""
Classe principal para gerenciamento do banco de dados SQLite
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Optional
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """Classe principal para gerenciamento do banco de dados"""
    
    def __init__(self, db_path: str = 'radar_climatico.db'):
        """
        Inicializa a conexão com o banco de dados
        
        Args:
            db_path: Caminho para o arquivo do banco SQLite
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados executando o script SQL"""
        try:
            # Busca o script SQL na mesma pasta
            script_path = os.path.join(os.path.dirname(__file__), 'init_db.sql')
            
            if not os.path.exists(script_path):
                logger.error(f"Script SQL não encontrado: {script_path}")
                return
            
            with open(script_path, 'r', encoding='utf-8') as file:
                sql_script = file.read()
            
            with self.get_connection() as conn:
                # Executar script SQL completo de uma vez
                try:
                    conn.executescript(sql_script)
                except Exception as e:
                    logger.warning(f"executescript falhou: {e}, tentando comando por comando...")
                    # Se falhar, tentar comando por comando
                    commands = sql_script.split(';')
                    for command in commands:
                        command = command.strip()
                        if command and not command.startswith('--'):
                            try:
                                conn.execute(command + ';')
                            except Exception as cmd_error:
                                logger.warning(f"Comando SQL ignorado: {cmd_error}")
                conn.commit()
            
            logger.info("Banco de dados inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para conexões com o banco
        
        Yields:
            sqlite3.Connection: Conexão com o banco de dados
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Permite acesso por nome da coluna
            conn.execute("PRAGMA foreign_keys = ON")  # Habilita foreign keys
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro na conexão com banco: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> Optional[list]:
        """
        Executa uma query SELECT e retorna os resultados
        
        Args:
            query: Query SQL para executar
            params: Parâmetros para a query
            
        Returns:
            Lista de resultados ou None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            raise
    
    def execute_command(self, command: str, params: tuple = ()) -> int:
        """
        Executa um comando INSERT, UPDATE ou DELETE
        
        Args:
            command: Comando SQL para executar
            params: Parâmetros para o comando
            
        Returns:
            ID do último registro inserido ou número de linhas afetadas
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(command, params)
                conn.commit()
                return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
        except Exception as e:
            logger.error(f"Erro ao executar comando: {e}")
            raise
    
    def backup_database(self, backup_path: str):
        """
        Cria backup do banco de dados
        
        Args:
            backup_path: Caminho para salvar o backup
        """
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Backup criado em: {backup_path}")
        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> list:
        """
        Retorna informações sobre uma tabela
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Lista com informações das colunas
        """
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)
    
    def get_table_count(self, table_name: str) -> int:
        """
        Retorna o número de registros em uma tabela
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Número de registros
        """
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def vacuum_database(self):
        """Otimiza o banco de dados (VACUUM)"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.commit()
            logger.info("Banco de dados otimizado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao otimizar banco: {e}")
            raise
    
    def get_database_stats(self) -> dict:
        """
        Retorna estatísticas do banco de dados
        
        Returns:
            Dicionário com estatísticas
        """
        stats = {
            'file_size_mb': 0,
            'tables': {},
            'last_backup': None
        }
        
        try:
            # Tamanho do arquivo
            if os.path.exists(self.db_path):
                size_bytes = os.path.getsize(self.db_path)
                stats['file_size_mb'] = round(size_bytes / (1024 * 1024), 2)
            
            # Contagem por tabela
            tables = ['apolices', 'sinistros_historicos', 'previsoes_risco', 'dados_climaticos']
            for table in tables:
                try:
                    stats['tables'][table] = self.get_table_count(table)
                except:
                    stats['tables'][table] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return stats


# Instância global do banco (singleton pattern)
_db_instance = None

def get_database() -> Database:
    """Retorna a instância global do banco de dados"""
    global _db_instance
    if _db_instance is None:
        # Usar o caminho correto do banco radar_sinistro.db
        db_path = os.path.join('database', 'radar_sinistro.db')
        _db_instance = Database(db_path)
    return _db_instance