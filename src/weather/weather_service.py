"""
Serviço principal de dados climáticos
Integra OpenMeteo API + Cache + Fallbacks
"""
import logging
from typing import Optional
from datetime import datetime
from .openmeteo_client import OpenMeteoClient
from .weather_cache import WeatherCache
from .weather_models import WeatherData, WeatherConditions, calculate_weather_risk_score

logger = logging.getLogger(__name__)

class WeatherService:
    """
    Serviço principal para dados climáticos
    Estratégia: Cache -> API -> Fallback simulado
    """
    
    def __init__(self, 
                 cache_ttl_hours: int = 1,
                 cache_db_path: str = "weather_cache.db",
                 api_timeout: int = 10,
                 api_retries: int = 3):
        """
        Inicializa serviço de weather
        
        Args:
            cache_ttl_hours: TTL do cache em horas
            cache_db_path: Caminho para banco de cache
            api_timeout: Timeout da API em segundos
            api_retries: Número de tentativas da API
        """
        self.cache = WeatherCache(cache_db_path, cache_ttl_hours)
        self.client = OpenMeteoClient(api_timeout, api_retries)
        
        # Estatísticas de uso
        self.stats = {
            'cache_hits': 0,
            'api_calls': 0,
            'fallbacks': 0,
            'errors': 0
        }
        
        logger.info(f"WeatherService inicializado - Cache TTL: {cache_ttl_hours}h")
    
    def get_current_weather(self, latitude: float, longitude: float, use_cache: bool = True) -> Optional[WeatherData]:
        """
        Busca dados climáticos atuais com estratégia inteligente
        
        Args:
            latitude: Latitude em graus decimais
            longitude: Longitude em graus decimais
            use_cache: Se deve usar cache (padrão True)
            
        Returns:
            WeatherData com dados atuais ou None se falhar
        """
        try:
            # 1. Tentar cache primeiro (se habilitado)
            if use_cache:
                cached_data = self.cache.get(latitude, longitude, "current")
                if cached_data:
                    self.stats['cache_hits'] += 1
                    logger.debug(f"Dados do cache para ({latitude}, {longitude})")
                    return cached_data
            
            # 2. Buscar da API
            logger.debug(f"Buscando dados da API para ({latitude}, {longitude})")
            api_data = self.client.get_weather_with_history(latitude, longitude)
            
            if api_data:
                self.stats['api_calls'] += 1
                
                # Armazenar no cache
                if use_cache:
                    self.cache.set(api_data, "current")
                
                logger.debug(f"Dados da API obtidos para ({latitude}, {longitude})")
                return api_data
            
            # 3. Fallback para dados simulados
            logger.warning(f"API falhou, usando fallback simulado para ({latitude}, {longitude})")
            fallback_data = self._generate_fallback_data(latitude, longitude)
            self.stats['fallbacks'] += 1
            return fallback_data
        
        except Exception as e:
            logger.error(f"Erro ao buscar dados climáticos: {e}")
            self.stats['errors'] += 1
            
            # Última tentativa: fallback simulado
            return self._generate_fallback_data(latitude, longitude)
    
    def get_weather_for_prediction(self, latitude: float, longitude: float) -> WeatherData:
        """
        Busca dados climáticos otimizados para predição de ML
        Garante que sempre retorna dados (nunca None)
        
        Args:
            latitude: Latitude em graus decimais
            longitude: Longitude em graus decimais
            
        Returns:
            WeatherData (sempre retorna, usa fallback se necessário)
        """
        weather_data = self.get_current_weather(latitude, longitude)
        
        if weather_data is None:
            logger.warning("Todas as fontes falharam, gerando dados mínimos para predição")
            weather_data = self._generate_minimal_fallback(latitude, longitude)
        
        return weather_data
    
    def _generate_fallback_data(self, latitude: float, longitude: float) -> WeatherData:
        """
        Gera dados climáticos simulados realísticos baseados na localização
        
        Args:
            latitude: Latitude em graus decimais
            longitude: Longitude em graus decimais
            
        Returns:
            WeatherData simulado baseado na região
        """
        import random
        from datetime import datetime
        
        # Determinar região/clima baseado na latitude
        if latitude < -30:  # Sul do Brasil
            base_temp = 18
            humidity_base = 70
        elif latitude < -15:  # Centro-Oeste/Sudeste
            base_temp = 24
            humidity_base = 65
        else:  # Norte/Nordeste
            base_temp = 28
            humidity_base = 75
        
        # Variação sazonal (simplificada)
        month = datetime.now().month
        if month in [12, 1, 2]:  # Verão
            temp_adjustment = 5
            rain_prob = 0.7
        elif month in [6, 7, 8]:  # Inverno
            temp_adjustment = -5
            rain_prob = 0.3
        else:  # Outono/Primavera
            temp_adjustment = 0
            rain_prob = 0.5
        
        # Gerar dados com variação aleatória realística
        current_temp = base_temp + temp_adjustment + random.uniform(-5, 5)
        humidity = max(30, min(95, humidity_base + random.uniform(-15, 15)))
        
        # Precipitação baseada na probabilidade sazonal
        precipitation = 0
        if random.random() < rain_prob:
            precipitation = random.uniform(0.1, 25.0)
        
        return WeatherData(
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime.now(),
            temperature_current=round(current_temp, 1),
            temperature_max=round(current_temp + random.uniform(2, 8), 1),
            temperature_min=round(current_temp - random.uniform(2, 6), 1),
            temperature_apparent=round(current_temp + random.uniform(-2, 3), 1),
            precipitation=precipitation,
            rain=precipitation,
            humidity=round(humidity, 1),
            wind_speed=random.uniform(5, 25),
            wind_direction=random.uniform(0, 360),
            pressure_msl=random.uniform(1010, 1025),
            cloud_cover=random.uniform(10, 90),
            weather_code=1 if precipitation == 0 else 61,
            conditions=WeatherConditions.PARTLY_CLOUDY if precipitation == 0 else WeatherConditions.RAIN,
            # Dados históricos simulados
            temperature_max_7d=round(current_temp + random.uniform(5, 12), 1),
            temperature_min_7d=round(current_temp - random.uniform(3, 8), 1),
            precipitation_sum_7d=random.uniform(0, 50),
            source="fallback_simulated",
            is_cached=False
        )
    
    def _generate_minimal_fallback(self, latitude: float, longitude: float) -> WeatherData:
        """
        Gera dados mínimos para garantir que predição sempre funcione
        
        Args:
            latitude: Latitude em graus decimais
            longitude: Longitude em graus decimais
            
        Returns:
            WeatherData com valores padrão seguros
        """
        return WeatherData(
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime.now(),
            temperature_current=22.0,  # Temperatura neutra
            humidity=60.0,  # Umidade média
            precipitation=0.0,  # Sem chuva
            wind_speed=10.0,  # Vento leve
            pressure_msl=1013.0,  # Pressão padrão
            conditions=WeatherConditions.PARTLY_CLOUDY,
            weather_code=1,
            source="minimal_fallback",
            is_cached=False
        )
    
    def get_weather_risk_assessment(self, latitude: float, longitude: float) -> dict:
        """
        Avalia risco climático para uma localização
        
        Args:
            latitude: Latitude em graus decimais
            longitude: Longitude em graus decimais
            
        Returns:
            Dicionário com assessment completo de risco
        """
        weather_data = self.get_weather_for_prediction(latitude, longitude)
        risk_score = calculate_weather_risk_score(weather_data)
        
        # Classificar nível de risco
        if risk_score <= 0.3:
            risk_level = "baixo"
        elif risk_score <= 0.6:
            risk_level = "medio"
        else:
            risk_level = "alto"
        
        # Identificar fatores de risco
        risk_factors = []
        
        if weather_data.precipitation and weather_data.precipitation > 10:
            risk_factors.append(f"Precipitação elevada: {weather_data.precipitation:.1f}mm")
        
        if weather_data.wind_speed and weather_data.wind_speed > 40:
            risk_factors.append(f"Vento forte: {weather_data.wind_speed:.1f} km/h")
        
        if weather_data.conditions in [WeatherConditions.THUNDERSTORM, WeatherConditions.SNOW]:
            risk_factors.append(f"Condições adversas: {weather_data.conditions.value}")
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'weather_summary': {
                'temperature': weather_data.temperature_current,
                'humidity': weather_data.humidity,
                'precipitation': weather_data.precipitation,
                'wind_speed': weather_data.wind_speed,
                'conditions': weather_data.conditions.value
            },
            'data_source': weather_data.source,
            'is_cached': weather_data.is_cached,
            'timestamp': weather_data.timestamp.isoformat()
        }
    
    def health_check(self) -> dict:
        """
        Verifica saúde do serviço de weather
        
        Returns:
            Status detalhado do serviço
        """
        # Testar API
        api_healthy = self.client.health_check()
        
        # Estatísticas do cache
        cache_stats = self.cache.get_cache_stats()
        
        # Estatísticas de uso
        total_requests = sum(self.stats.values())
        
        return {
            'api_status': 'healthy' if api_healthy else 'unavailable',
            'cache_status': 'healthy' if cache_stats else 'error',
            'service_stats': self.stats.copy(),
            'total_requests': total_requests,
            'cache_stats': cache_stats,
            'fallback_available': True,  # Sempre disponível
            'timestamp': datetime.now().isoformat()
        }
    
    def clear_cache(self, confirm: bool = False):
        """
        Limpa cache do serviço
        
        Args:
            confirm: Confirma que deseja limpar
        """
        self.cache.clear_cache(confirm)
        if confirm:
            logger.info("Cache do WeatherService limpo")
    
    def get_service_stats(self) -> dict:
        """
        Retorna estatísticas detalhadas do serviço
        
        Returns:
            Estatísticas de uso e performance
        """
        total_requests = sum(self.stats.values())
        
        if total_requests > 0:
            cache_hit_rate = (self.stats['cache_hits'] / total_requests) * 100
            error_rate = (self.stats['errors'] / total_requests) * 100
        else:
            cache_hit_rate = 0
            error_rate = 0
        
        return {
            'requests': self.stats.copy(),
            'total_requests': total_requests,
            'cache_hit_rate_percent': round(cache_hit_rate, 1),
            'error_rate_percent': round(error_rate, 1),
            'cache_stats': self.cache.get_cache_stats()
        }