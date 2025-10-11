"""
Sistema de cache SQLite para dados climáticos
"""
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from .weather_models import WeatherData

logger = logging.getLogger(__name__)

class WeatherCache:
    """
    Cache inteligente para dados climáticos usando SQLite
    TTL configurável, cleanup automático
    """
    
    def __init__(self, db_path: str = "weather_cache.db", ttl_hours: int = 1):
        """
        Inicializa cache SQLite
        
        Args:
            db_path: Caminho para arquivo SQLite
            ttl_hours: Time-to-live em horas para cache
        """
        self.db_path = Path(db_path)
        self.ttl_hours = ttl_hours
        self.ttl_delta = timedelta(hours=ttl_hours)
        
        # Criar diretório se não existir
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        self._cleanup_expired()
    
    def _init_database(self):
        """Inicializa estrutura do banco de dados"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS weather_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        cache_key TEXT NOT NULL UNIQUE,
                        weather_data TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        expires_at TIMESTAMP NOT NULL
                    )
                """)
                
                # Índices para performance
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_cache_key 
                    ON weather_cache(cache_key)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_coordinates 
                    ON weather_cache(latitude, longitude)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_expires_at 
                    ON weather_cache(expires_at)
                """)
                
                conn.commit()
                logger.debug(f"Cache database inicializado: {self.db_path}")
        
        except Exception as e:
            logger.error(f"Erro ao inicializar cache database: {e}")
    
    def _generate_cache_key(self, latitude: float, longitude: float, data_type: str = "current") -> str:
        """
        Gera chave única para cache baseada em coordenadas
        
        Args:
            latitude: Latitude em graus decimais
            longitude: Longitude em graus decimais
            data_type: Tipo de dado (current, historical, complete)
            
        Returns:
            Chave única para cache
        """
        # Arredondar coordenadas para 2 casas decimais (aproximadamente 1km de precisão)
        lat_rounded = round(latitude, 2)
        lon_rounded = round(longitude, 2)
        
        return f"weather_{data_type}_{lat_rounded}_{lon_rounded}"
    
    def get(self, latitude: float, longitude: float, data_type: str = "current") -> Optional[WeatherData]:
        """
        Busca dados no cache
        
        Args:
            latitude: Latitude em graus decimais
            longitude: Longitude em graus decimais
            data_type: Tipo de dado a buscar
            
        Returns:
            WeatherData se encontrado e válido, None caso contrário
        """
        cache_key = self._generate_cache_key(latitude, longitude, data_type)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT weather_data, created_at, expires_at 
                    FROM weather_cache 
                    WHERE cache_key = ? AND expires_at > datetime('now')
                """, (cache_key,))
                
                row = cursor.fetchone()
                
                if row:
                    # Deserializar dados
                    weather_data_dict = json.loads(row['weather_data'])
                    weather_data = WeatherData.from_dict(weather_data_dict)
                    
                    # Adicionar informações de cache
                    created_at = datetime.fromisoformat(row['created_at'])
                    cache_age = datetime.now() - created_at
                    
                    weather_data.is_cached = True
                    weather_data.cache_age_minutes = int(cache_age.total_seconds() / 60)
                    
                    logger.debug(f"Cache hit para {cache_key}, idade: {cache_age}")
                    return weather_data
                
                logger.debug(f"Cache miss para {cache_key}")
                return None
        
        except Exception as e:
            logger.error(f"Erro ao buscar cache: {e}")
            return None
    
    def set(self, weather_data: WeatherData, data_type: str = "current") -> bool:
        """
        Armazena dados no cache
        
        Args:
            weather_data: Dados climáticos para armazenar
            data_type: Tipo de dado sendo armazenado
            
        Returns:
            True se armazenado com sucesso, False caso contrário
        """
        cache_key = self._generate_cache_key(
            weather_data.latitude, 
            weather_data.longitude, 
            data_type
        )
        
        try:
            now = datetime.now()
            expires_at = now + self.ttl_delta
            
            # Serializar dados
            weather_data_json = json.dumps(weather_data.to_dict())
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Usar INSERT OR REPLACE para atualizar se já existir
                cursor.execute("""
                    INSERT OR REPLACE INTO weather_cache 
                    (latitude, longitude, cache_key, weather_data, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    weather_data.latitude,
                    weather_data.longitude,
                    cache_key,
                    weather_data_json,
                    now.isoformat(),
                    expires_at.isoformat()
                ))
                
                conn.commit()
                logger.debug(f"Cache armazenado para {cache_key}, expira em: {expires_at}")
                return True
        
        except Exception as e:
            logger.error(f"Erro ao armazenar cache: {e}")
            return False
    
    def _cleanup_expired(self):
        """Remove entradas expiradas do cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM weather_cache 
                    WHERE expires_at <= datetime('now')
                """)
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.debug(f"Removidas {deleted_count} entradas expiradas do cache")
        
        except Exception as e:
            logger.error(f"Erro no cleanup do cache: {e}")
    
    def cleanup_old_entries(self, days_old: int = 7):
        """
        Remove entradas antigas do cache (mesmo se não expiradas)
        
        Args:
            days_old: Remover entradas mais antigas que N dias
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM weather_cache 
                    WHERE created_at <= ?
                """, (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"Removidas {deleted_count} entradas antigas do cache (>{days_old} dias)")
        
        except Exception as e:
            logger.error(f"Erro no cleanup de entradas antigas: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache
        
        Returns:
            Dicionário com estatísticas de uso
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total de entradas
                cursor.execute("SELECT COUNT(*) FROM weather_cache")
                total_entries = cursor.fetchone()[0]
                
                # Entradas válidas (não expiradas)
                cursor.execute("""
                    SELECT COUNT(*) FROM weather_cache 
                    WHERE expires_at > datetime('now')
                """)
                valid_entries = cursor.fetchone()[0]
                
                # Entradas expiradas
                expired_entries = total_entries - valid_entries
                
                # Tamanho do arquivo
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    'total_entries': total_entries,
                    'valid_entries': valid_entries,
                    'expired_entries': expired_entries,
                    'database_size_bytes': db_size,
                    'database_size_mb': round(db_size / (1024 * 1024), 2),
                    'ttl_hours': self.ttl_hours
                }
        
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do cache: {e}")
            return {}
    
    def clear_cache(self, confirm: bool = False):
        """
        Limpa todo o cache
        
        Args:
            confirm: Confirma que deseja apagar todos os dados
        """
        if not confirm:
            logger.warning("Cache não foi limpo - confirm=False")
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM weather_cache")
                conn.commit()
                
                logger.info("Cache completamente limpo")
        
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
    
    def get_nearby_cached_data(self, latitude: float, longitude: float, radius_km: float = 5.0) -> list[WeatherData]:
        """
        Busca dados em cache próximos às coordenadas (útil para fallback)
        
        Args:
            latitude: Latitude de referência
            longitude: Longitude de referência  
            radius_km: Raio de busca em km
            
        Returns:
            Lista de WeatherData próximos e válidos
        """
        try:
            # Aproximação simples: 1 grau ≈ 111 km
            lat_delta = radius_km / 111.0
            lon_delta = radius_km / (111.0 * abs(cos(radians(latitude))))
            
            lat_min = latitude - lat_delta
            lat_max = latitude + lat_delta
            lon_min = longitude - lon_delta
            lon_max = longitude + lon_delta
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT weather_data, created_at
                    FROM weather_cache 
                    WHERE latitude BETWEEN ? AND ?
                    AND longitude BETWEEN ? AND ?
                    AND expires_at > datetime('now')
                    ORDER BY ABS(latitude - ?) + ABS(longitude - ?)
                    LIMIT 10
                """, (lat_min, lat_max, lon_min, lon_max, latitude, longitude))
                
                results = []
                for row in cursor.fetchall():
                    weather_data_dict = json.loads(row['weather_data'])
                    weather_data = WeatherData.from_dict(weather_data_dict)
                    weather_data.is_cached = True
                    results.append(weather_data)
                
                return results
        
        except Exception as e:
            logger.error(f"Erro ao buscar dados próximos: {e}")
            return []

def cos(x):
    """Função cos simples para cálculo de distância"""
    import math
    return math.cos(x)

def radians(x):
    """Função radians simples para conversão"""
    import math
    return math.radians(x)
