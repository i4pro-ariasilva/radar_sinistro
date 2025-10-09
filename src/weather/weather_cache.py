"""
Cache inteligente para dados climáticos
Evita chamadas desnecessárias para APIs externas
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

class WeatherCache:
    """Sistema de cache para dados climáticos"""
    
    def __init__(self, cache_dir: str = "data/cache", cache_duration_hours: int = 1):
        """
        Inicializar cache
        
        Args:
            cache_dir: Diretório para armazenar cache
            cache_duration_hours: Duração do cache em horas
        """
        self.cache_dir = Path(cache_dir)
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, location: str, query_type: str = "current") -> str:
        """Gerar chave de cache para localização"""
        # Normalizar localização para usar como nome de arquivo
        normalized_location = location.replace(" ", "_").replace(",", "_").replace("/", "_")
        return f"weather_{query_type}_{normalized_location}.json"
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Obter caminho completo do arquivo de cache"""
        return self.cache_dir / cache_key
    
    def get(self, location: str, query_type: str = "current") -> Optional[Dict[str, Any]]:
        """
        Obter dados do cache se ainda válidos
        
        Args:
            location: Localização (CEP, cidade, coordenadas)
            query_type: Tipo de consulta (current, forecast, etc.)
            
        Returns:
            Dados do cache se válidos, None caso contrário
        """
        try:
            cache_key = self._get_cache_key(location, query_type)
            cache_file = self._get_cache_file_path(cache_key)
            
            if not cache_file.exists():
                return None
            
            # Verificar se arquivo não expirou
            file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - file_time > self.cache_duration:
                # Cache expirado, remover arquivo
                cache_file.unlink()
                return None
            
            # Ler dados do cache
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            return cache_data.get('data')
            
        except Exception as e:
            print(f"Erro ao ler cache: {e}")
            return None
    
    def set(self, location: str, data: Dict[str, Any], query_type: str = "current") -> bool:
        """
        Armazenar dados no cache
        
        Args:
            location: Localização
            data: Dados para cachear
            query_type: Tipo de consulta
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            cache_key = self._get_cache_key(location, query_type)
            cache_file = self._get_cache_file_path(cache_key)
            
            cache_data = {
                'location': location,
                'query_type': query_type,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Erro ao salvar cache: {e}")
            return False
    
    def clear(self, location: Optional[str] = None) -> int:
        """
        Limpar cache
        
        Args:
            location: Localização específica para limpar (None para limpar tudo)
            
        Returns:
            Número de arquivos removidos
        """
        removed_count = 0
        
        try:
            if location:
                # Limpar cache específico
                for query_type in ['current', 'forecast', 'history']:
                    cache_key = self._get_cache_key(location, query_type)
                    cache_file = self._get_cache_file_path(cache_key)
                    
                    if cache_file.exists():
                        cache_file.unlink()
                        removed_count += 1
            else:
                # Limpar todo o cache
                for cache_file in self.cache_dir.glob("weather_*.json"):
                    cache_file.unlink()
                    removed_count += 1
                    
        except Exception as e:
            print(f"Erro ao limpar cache: {e}")
        
        return removed_count
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Obter informações sobre o cache
        
        Returns:
            Dicionário com estatísticas do cache
        """
        try:
            cache_files = list(self.cache_dir.glob("weather_*.json"))
            total_files = len(cache_files)
            
            if total_files == 0:
                return {
                    'total_files': 0,
                    'total_size_mb': 0,
                    'oldest_file': None,
                    'newest_file': None,
                    'expired_files': 0
                }
            
            # Calcular tamanho total
            total_size = sum(f.stat().st_size for f in cache_files)
            total_size_mb = total_size / (1024 * 1024)
            
            # Encontrar arquivos mais antigos e novos
            file_times = [(f, datetime.fromtimestamp(f.stat().st_mtime)) for f in cache_files]
            file_times.sort(key=lambda x: x[1])
            
            oldest_file = file_times[0][1] if file_times else None
            newest_file = file_times[-1][1] if file_times else None
            
            # Contar arquivos expirados
            now = datetime.now()
            expired_files = sum(1 for _, file_time in file_times 
                              if now - file_time > self.cache_duration)
            
            return {
                'total_files': total_files,
                'total_size_mb': round(total_size_mb, 2),
                'oldest_file': oldest_file.isoformat() if oldest_file else None,
                'newest_file': newest_file.isoformat() if newest_file else None,
                'expired_files': expired_files,
                'cache_duration_hours': self.cache_duration.total_seconds() / 3600
            }
            
        except Exception as e:
            print(f"Erro ao obter informações do cache: {e}")
            return {'error': str(e)}
    
    def cleanup_expired(self) -> int:
        """
        Remover arquivos de cache expirados
        
        Returns:
            Número de arquivos removidos
        """
        removed_count = 0
        
        try:
            now = datetime.now()
            cache_files = list(self.cache_dir.glob("weather_*.json"))
            
            for cache_file in cache_files:
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                
                if now - file_time > self.cache_duration:
                    cache_file.unlink()
                    removed_count += 1
                    
        except Exception as e:
            print(f"Erro ao limpar cache expirado: {e}")
        
        return removed_count
    
    def get_all_cached_data(self, include_expired: bool = False) -> list:
        """
        Obter todos os dados armazenados no cache
        
        Args:
            include_expired: Se True, inclui dados expirados também
            
        Returns:
            Lista com todos os dados do cache
        """
        cached_data = []
        
        try:
            now = datetime.now()
            cache_files = list(self.cache_dir.glob("weather_*.json"))
            
            for cache_file in cache_files:
                try:
                    # Verificar se expirado
                    file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    is_expired = now - file_time > self.cache_duration
                    
                    if is_expired and not include_expired:
                        continue
                    
                    # Ler dados do arquivo
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_content = json.load(f)
                    
                    # Adicionar informações extras
                    cache_content['file_path'] = str(cache_file)
                    cache_content['file_time'] = file_time.isoformat()
                    cache_content['is_expired'] = is_expired
                    cache_content['cache_key'] = cache_file.stem
                    
                    cached_data.append(cache_content)
                    
                except Exception as e:
                    print(f"Erro ao ler arquivo {cache_file}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Erro ao listar dados do cache: {e}")
        
        return cached_data
    
    def export_to_dataframe(self, include_expired: bool = False):
        """
        Exportar dados do cache para DataFrame do pandas
        
        Args:
            include_expired: Se True, inclui dados expirados
            
        Returns:
            DataFrame com dados climáticos do cache
        """
        try:
            import pandas as pd
        except ImportError:
            print("Pandas não disponível para exportação")
            return None
        
        cached_data = self.get_all_cached_data(include_expired)
        
        if not cached_data:
            return pd.DataFrame()
        
        # Converter para formato tabular
        rows = []
        
        for cache_item in cached_data:
            try:
                data = cache_item.get('data', {})
                
                # Extrair informações básicas
                row = {
                    'location': cache_item.get('location', ''),
                    'query_type': cache_item.get('query_type', ''),
                    'timestamp': cache_item.get('timestamp', ''),
                    'file_time': cache_item.get('file_time', ''),
                    'is_expired': cache_item.get('is_expired', False),
                    'cache_key': cache_item.get('cache_key', ''),
                }
                
                # Extrair dados climáticos se disponíveis
                if isinstance(data, dict):
                    row.update({
                        'temperature_c': data.get('temperature_c'),
                        'temperature_f': data.get('temperature_f'),
                        'condition': data.get('condition'),
                        'humidity_percent': data.get('humidity_percent'),
                        'wind_speed_kph': data.get('wind_speed_kph'),
                        'wind_direction': data.get('wind_direction'),
                        'pressure_mb': data.get('pressure_mb'),
                        'visibility_km': data.get('visibility_km'),
                        'uv_index': data.get('uv_index'),
                        'precipitation_mm': data.get('precipitation_mm'),
                        'cloud_cover_percent': data.get('cloud_cover_percent'),
                        'feels_like_c': data.get('feels_like_c'),
                        'risk_score': data.get('risk_score'),
                        'risk_level': data.get('risk_level'),
                        'latitude': data.get('latitude'),
                        'longitude': data.get('longitude'),
                        'city': data.get('city'),
                        'region': data.get('region'),
                        'country': data.get('country'),
                    })
                
                rows.append(row)
                
            except Exception as e:
                print(f"Erro ao processar item do cache: {e}")
                continue
        
        return pd.DataFrame(rows)
    
    def get_summary_statistics(self) -> dict:
        """
        Obter estatísticas resumidas dos dados em cache
        
        Returns:
            Dicionário com estatísticas do cache
        """
        try:
            df = self.export_to_dataframe(include_expired=False)
            
            if df.empty:
                return {'message': 'Nenhum dado em cache'}
            
            stats = {
                'total_records': len(df),
                'unique_locations': df['location'].nunique() if 'location' in df else 0,
                'date_range': {
                    'oldest': df['timestamp'].min() if 'timestamp' in df else None,
                    'newest': df['timestamp'].max() if 'timestamp' in df else None,
                },
                'weather_stats': {}
            }
            
            # Estatísticas climáticas se disponíveis
            numeric_columns = ['temperature_c', 'humidity_percent', 'wind_speed_kph', 
                             'pressure_mb', 'uv_index', 'precipitation_mm', 'risk_score']
            
            for col in numeric_columns:
                if col in df and df[col].notna().any():
                    stats['weather_stats'][col] = {
                        'mean': float(df[col].mean()),
                        'min': float(df[col].min()),
                        'max': float(df[col].max()),
                        'std': float(df[col].std()),
                        'count': int(df[col].count())
                    }
            
            # Contagens por categoria
            if 'condition' in df:
                stats['condition_counts'] = df['condition'].value_counts().to_dict()
            
            if 'risk_level' in df:
                stats['risk_level_counts'] = df['risk_level'].value_counts().to_dict()
            
            return stats
            
        except Exception as e:
            return {'error': f"Erro ao calcular estatísticas: {e}"}