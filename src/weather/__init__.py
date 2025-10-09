"""
Módulo de integração com APIs climáticas
Suporte para WeatherAPI.com e outras fontes de dados meteorológicos
"""

from .weather_client import WeatherClient
from .weather_data import WeatherData
from .weather_cache import WeatherCache

__all__ = ['WeatherClient', 'WeatherData', 'WeatherCache']