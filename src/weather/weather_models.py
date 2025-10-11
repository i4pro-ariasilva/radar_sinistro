"""
Modelos de dados climáticos para o sistema de weather
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class WeatherConditions(Enum):
    """Condições climáticas padronizadas"""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    OVERCAST = "overcast"
    FOG = "fog"
    DRIZZLE = "drizzle"
    RAIN = "rain"
    SNOW = "snow"
    SNOW_GRAINS = "snow_grains"
    RAIN_SHOWERS = "rain_showers"
    SNOW_SHOWERS = "snow_showers"
    THUNDERSTORM = "thunderstorm"
    UNKNOWN = "unknown"

@dataclass
class WeatherData:
    """Dados climáticos estruturados"""
    # Localização
    latitude: float
    longitude: float
    
    # Dados temporais
    timestamp: datetime
    
    # Temperatura (°C)
    temperature_current: Optional[float] = None
    temperature_max: Optional[float] = None
    temperature_min: Optional[float] = None
    temperature_apparent: Optional[float] = None
    
    # Precipitação (mm)
    precipitation: Optional[float] = None
    precipitation_probability: Optional[float] = None
    rain: Optional[float] = None
    snowfall: Optional[float] = None
    
    # Vento
    wind_speed: Optional[float] = None  # km/h
    wind_direction: Optional[float] = None  # graus
    wind_gusts: Optional[float] = None  # km/h
    
    # Atmosfera
    humidity: Optional[float] = None  # %
    pressure_msl: Optional[float] = None  # hPa
    visibility: Optional[float] = None  # km
    
    # Condições
    weather_code: Optional[int] = None
    conditions: WeatherConditions = WeatherConditions.UNKNOWN
    cloud_cover: Optional[float] = None  # %
    
    # Dados históricos/tendências (últimos 7 dias)
    temperature_max_7d: Optional[float] = None
    temperature_min_7d: Optional[float] = None
    precipitation_sum_7d: Optional[float] = None
    
    # Metadados
    source: str = "openmeteo"
    is_cached: bool = False
    cache_age_minutes: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Converte para dicionário para cache/serialização"""
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'timestamp': self.timestamp.isoformat(),
            'temperature_current': self.temperature_current,
            'temperature_max': self.temperature_max,
            'temperature_min': self.temperature_min,
            'temperature_apparent': self.temperature_apparent,
            'precipitation': self.precipitation,
            'precipitation_probability': self.precipitation_probability,
            'rain': self.rain,
            'snowfall': self.snowfall,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'wind_gusts': self.wind_gusts,
            'humidity': self.humidity,
            'pressure_msl': self.pressure_msl,
            'visibility': self.visibility,
            'weather_code': self.weather_code,
            'conditions': self.conditions.value,
            'cloud_cover': self.cloud_cover,
            'temperature_max_7d': self.temperature_max_7d,
            'temperature_min_7d': self.temperature_min_7d,
            'precipitation_sum_7d': self.precipitation_sum_7d,
            'source': self.source,
            'is_cached': self.is_cached,
            'cache_age_minutes': self.cache_age_minutes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WeatherData':
        """Cria instância a partir de dicionário do cache"""
        data = data.copy()
        
        # Converter timestamp string para datetime
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        # Converter conditions string para enum
        if isinstance(data['conditions'], str):
            try:
                data['conditions'] = WeatherConditions(data['conditions'])
            except ValueError:
                data['conditions'] = WeatherConditions.UNKNOWN
        
        return cls(**data)

@dataclass
class WeatherForecast:
    """Previsão climática para múltiplos dias"""
    latitude: float
    longitude: float
    forecast_date: datetime
    daily_forecasts: list[WeatherData]
    
    def get_forecast_day(self, days_ahead: int) -> Optional[WeatherData]:
        """Retorna previsão para N dias à frente"""
        if 0 <= days_ahead < len(self.daily_forecasts):
            return self.daily_forecasts[days_ahead]
        return None

class LegacyWeatherCurrent:
    """Adaptador para compatibilidade com código legado que espera weather_data.current.*"""
    def __init__(self, data: WeatherData):
        self.temperature_c = data.temperature_current
        self.precipitation_mm = data.precipitation
        self.wind_speed_kmh = data.wind_speed
        self.humidity_percent = data.humidity
        self.pressure_hpa = data.pressure_msl
        self.conditions = data.conditions.value
        self.timestamp = data.timestamp

class LegacyWeatherPayload:
    """Wrapper para expor interface antiga (weather_data.current)"""
    def __init__(self, data: WeatherData):
        self.current = LegacyWeatherCurrent(data)
        self.raw = data  # acesso ao objeto original
        self.source = data.source
        self.is_cached = data.is_cached
        self.latitude = data.latitude
        self.longitude = data.longitude
        self.timestamp = data.timestamp

    def to_dict(self) -> dict:
        return {
            'current': {
                'temperature_c': self.current.temperature_c,
                'precipitation_mm': self.current.precipitation_mm,
                'wind_speed_kmh': self.current.wind_speed_kmh,
                'humidity_percent': self.current.humidity_percent,
                'conditions': self.current.conditions,
                'timestamp': self.current.timestamp.isoformat() if self.current.timestamp else None
            },
            'source': self.source,
            'is_cached': self.is_cached,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

def weather_code_to_conditions(weather_code: Optional[int]) -> WeatherConditions:
    """
    Converte código WMO da OpenMeteo para condições padronizadas
    Ref: https://open-meteo.com/en/docs
    """
    if weather_code is None:
        return WeatherConditions.UNKNOWN
    
    # Mapeamento baseado nos códigos WMO
    code_mapping = {
        0: WeatherConditions.CLEAR,
        1: WeatherConditions.PARTLY_CLOUDY,
        2: WeatherConditions.PARTLY_CLOUDY, 
        3: WeatherConditions.OVERCAST,
        45: WeatherConditions.FOG,
        48: WeatherConditions.FOG,
        51: WeatherConditions.DRIZZLE,
        53: WeatherConditions.DRIZZLE,
        55: WeatherConditions.DRIZZLE,
        56: WeatherConditions.DRIZZLE,
        57: WeatherConditions.DRIZZLE,
        61: WeatherConditions.RAIN,
        63: WeatherConditions.RAIN,
        65: WeatherConditions.RAIN,
        66: WeatherConditions.RAIN,
        67: WeatherConditions.RAIN,
        71: WeatherConditions.SNOW,
        73: WeatherConditions.SNOW,
        75: WeatherConditions.SNOW,
        77: WeatherConditions.SNOW_GRAINS,
        80: WeatherConditions.RAIN_SHOWERS,
        81: WeatherConditions.RAIN_SHOWERS,
        82: WeatherConditions.RAIN_SHOWERS,
        85: WeatherConditions.SNOW_SHOWERS,
        86: WeatherConditions.SNOW_SHOWERS,
        95: WeatherConditions.THUNDERSTORM,
        96: WeatherConditions.THUNDERSTORM,
        99: WeatherConditions.THUNDERSTORM,
    }
    
    return code_mapping.get(weather_code, WeatherConditions.UNKNOWN)

def calculate_weather_risk_score(weather_data: WeatherData) -> float:
    """
    Calcula score de risco baseado nas condições climáticas
    Retorna valor entre 0 (baixo risco) e 1 (alto risco)
    """
    risk_score = 0.0
    
    # Risco por precipitação
    if weather_data.precipitation:
        if weather_data.precipitation > 50:  # Chuva forte
            risk_score += 0.4
        elif weather_data.precipitation > 20:  # Chuva moderada
            risk_score += 0.2
        elif weather_data.precipitation > 5:  # Chuva leve
            risk_score += 0.1
    
    # Risco por vento
    if weather_data.wind_speed:
        if weather_data.wind_speed > 80:  # Vento muito forte
            risk_score += 0.3
        elif weather_data.wind_speed > 50:  # Vento forte
            risk_score += 0.2
        elif weather_data.wind_speed > 30:  # Vento moderado
            risk_score += 0.1
    
    # Risco por condições específicas
    high_risk_conditions = [
        WeatherConditions.THUNDERSTORM,
        WeatherConditions.SNOW,
        WeatherConditions.SNOW_SHOWERS
    ]
    if weather_data.conditions in high_risk_conditions:
        risk_score += 0.3
    
    # Normalizar entre 0 e 1
    return min(risk_score, 1.0)
