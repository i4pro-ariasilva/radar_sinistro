"""
Cliente para API OpenMeteo - Dados climáticos gratuitos
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .weather_models import WeatherData, WeatherConditions, weather_code_to_conditions

logger = logging.getLogger(__name__)

class OpenMeteoClient:
    """
    Cliente para API OpenMeteo
    Documentação: https://open-meteo.com/en/docs
    """
    
    BASE_URL = "https://api.open-meteo.com/v1"
    
    def __init__(self, timeout: int = 10, retries: int = 3):
        """
        Inicializa cliente OpenMeteo
        
        Args:
            timeout: Timeout para requests em segundos
            retries: Número de tentativas em caso de falha
        """
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        
        # Headers recomendados
        self.session.headers.update({
            'User-Agent': 'RadarSinistro/1.0 (Climate Risk Analysis)',
            'Accept': 'application/json'
        })
    
    def get_current_weather(self, latitude: float, longitude: float) -> Optional[WeatherData]:
        """
        Busca dados climáticos atuais para coordenadas específicas
        
        Args:
            latitude: Latitude em graus decimais
            longitude: Longitude em graus decimais
            
        Returns:
            WeatherData com dados atuais ou None em caso de erro
        """
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'current': [
                'temperature_2m',
                'relative_humidity_2m', 
                'apparent_temperature',
                'precipitation',
                'rain',
                'snowfall',
                'weather_code',
                'cloud_cover',
                'pressure_msl',
                'surface_pressure',
                'wind_speed_10m',
                'wind_direction_10m',
                'wind_gusts_10m'
            ],
            'timezone': 'auto',
            'forecast_days': 1
        }
        
        try:
            response = self._make_request('/forecast', params)
            if response:
                return self._parse_current_weather(response, latitude, longitude)
        except Exception as e:
            logger.error(f"Erro ao buscar clima atual: {e}")
        
        return None
    
    def get_historical_weather(self, latitude: float, longitude: float, days: int = 7) -> Optional[WeatherData]:
        """
        Busca dados históricos para análise de tendências
        
        Args:
            latitude: Latitude em graus decimais
            longitude: Longitude em graus decimais  
            days: Número de dias históricos (máximo 92)
            
        Returns:
            WeatherData com médias históricas ou None
        """
        # Calcula data de início
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'daily': [
                'temperature_2m_max',
                'temperature_2m_min',
                'precipitation_sum',
                'rain_sum',
                'snowfall_sum',
                'wind_speed_10m_max'
            ],
            'timezone': 'auto'
        }
        
        try:
            response = self._make_request('/forecast', params)
            if response:
                return self._parse_historical_weather(response, latitude, longitude, days)
        except Exception as e:
            logger.error(f"Erro ao buscar dados históricos: {e}")
        
        return None
    
    def get_weather_with_history(self, latitude: float, longitude: float) -> Optional[WeatherData]:
        """
        Busca dados atuais + histórico em uma única requisição otimizada
        
        Args:
            latitude: Latitude em graus decimais
            longitude: Longitude em graus decimais
            
        Returns:
            WeatherData completo com dados atuais e históricos
        """
        # Data para histórico de 7 dias
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'current': [
                'temperature_2m',
                'relative_humidity_2m',
                'apparent_temperature', 
                'precipitation',
                'rain',
                'snowfall',
                'weather_code',
                'cloud_cover',
                'pressure_msl',
                'wind_speed_10m',
                'wind_direction_10m',
                'wind_gusts_10m'
            ],
            'daily': [
                'temperature_2m_max',
                'temperature_2m_min', 
                'precipitation_sum'
            ],
            'past_days': 7,
            'forecast_days': 1,
            'timezone': 'auto'
        }
        
        try:
            response = self._make_request('/forecast', params)
            if response:
                return self._parse_complete_weather(response, latitude, longitude)
        except Exception as e:
            logger.error(f"Erro ao buscar dados completos: {e}")
        
        return None
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        """
        Executa requisição HTTP com retry logic
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da requisição
            
        Returns:
            Resposta JSON ou None em caso de erro
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(self.retries):
            try:
                logger.debug(f"Tentativa {attempt + 1} - Requisição para: {url}")
                
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Verificar se a resposta contém dados válidos
                if 'error' in data:
                    logger.error(f"Erro da API OpenMeteo: {data['error']}")
                    return None
                
                logger.debug(f"Sucesso na requisição OpenMeteo")
                return data
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout na tentativa {attempt + 1}")
                if attempt == self.retries - 1:
                    logger.error("Todas as tentativas de timeout falharam")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Erro de requisição na tentativa {attempt + 1}: {e}")
                if attempt == self.retries - 1:
                    logger.error(f"Todas as tentativas falharam: {e}")
                    
            except Exception as e:
                logger.error(f"Erro inesperado: {e}")
                break
        
        return None
    
    def _parse_current_weather(self, data: Dict, latitude: float, longitude: float) -> WeatherData:
        """Parse dados climáticos atuais da resposta da API"""
        current = data.get('current', {})
        
        # Converter weather_code para condições
        weather_code = current.get('weather_code')
        conditions = weather_code_to_conditions(weather_code)
        
        return WeatherData(
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime.now(),
            temperature_current=current.get('temperature_2m'),
            temperature_apparent=current.get('apparent_temperature'),
            precipitation=current.get('precipitation'),
            rain=current.get('rain'),
            snowfall=current.get('snowfall'),
            wind_speed=current.get('wind_speed_10m'),
            wind_direction=current.get('wind_direction_10m'),
            wind_gusts=current.get('wind_gusts_10m'),
            humidity=current.get('relative_humidity_2m'),
            pressure_msl=current.get('pressure_msl'),
            weather_code=weather_code,
            conditions=conditions,
            cloud_cover=current.get('cloud_cover'),
            source="openmeteo",
            is_cached=False
        )
    
    def _parse_historical_weather(self, data: Dict, latitude: float, longitude: float, days: int) -> WeatherData:
        """Parse dados históricos da resposta da API"""
        daily = data.get('daily', {})
        
        # Calcular médias dos últimos dias
        temp_max_list = daily.get('temperature_2m_max', [])
        temp_min_list = daily.get('temperature_2m_min', [])
        precip_list = daily.get('precipitation_sum', [])
        
        # Filtrar valores None
        temp_max_values = [t for t in temp_max_list if t is not None]
        temp_min_values = [t for t in temp_min_list if t is not None]
        precip_values = [p for p in precip_list if p is not None]
        
        return WeatherData(
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime.now(),
            temperature_max_7d=max(temp_max_values) if temp_max_values else None,
            temperature_min_7d=min(temp_min_values) if temp_min_values else None,
            precipitation_sum_7d=sum(precip_values) if precip_values else None,
            source="openmeteo_historical",
            is_cached=False
        )
    
    def _parse_complete_weather(self, data: Dict, latitude: float, longitude: float) -> WeatherData:
        """Parse dados completos (atual + histórico) da resposta da API"""
        current = data.get('current', {})
        daily = data.get('daily', {})
        
        # Dados atuais
        weather_code = current.get('weather_code')
        conditions = weather_code_to_conditions(weather_code)
        
        # Dados históricos
        temp_max_list = daily.get('temperature_2m_max', [])
        temp_min_list = daily.get('temperature_2m_min', [])
        precip_list = daily.get('precipitation_sum', [])
        
        # Filtrar valores None e calcular estatísticas
        temp_max_values = [t for t in temp_max_list if t is not None]
        temp_min_values = [t for t in temp_min_list if t is not None]
        precip_values = [p for p in precip_list if p is not None]
        
        return WeatherData(
            latitude=latitude,
            longitude=longitude,
            timestamp=datetime.now(),
            # Dados atuais
            temperature_current=current.get('temperature_2m'),
            temperature_apparent=current.get('apparent_temperature'),
            precipitation=current.get('precipitation'),
            rain=current.get('rain'),
            snowfall=current.get('snowfall'),
            wind_speed=current.get('wind_speed_10m'),
            wind_direction=current.get('wind_direction_10m'),
            wind_gusts=current.get('wind_gusts_10m'),
            humidity=current.get('relative_humidity_2m'),
            pressure_msl=current.get('pressure_msl'),
            weather_code=weather_code,
            conditions=conditions,
            cloud_cover=current.get('cloud_cover'),
            # Dados históricos
            temperature_max_7d=max(temp_max_values) if temp_max_values else None,
            temperature_min_7d=min(temp_min_values) if temp_min_values else None,
            precipitation_sum_7d=sum(precip_values) if precip_values else None,
            source="openmeteo_complete",
            is_cached=False
        )
    
    def health_check(self) -> bool:
        """
        Verifica se a API está funcionando
        
        Returns:
            True se API estiver acessível, False caso contrário
        """
        try:
            # Teste simples com coordenadas de São Paulo
            response = self.get_current_weather(-23.5505, -46.6333)
            return response is not None
        except Exception as e:
            logger.error(f"Health check falhou: {e}")
            return False