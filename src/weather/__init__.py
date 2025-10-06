"""
Módulo Weather - Sistema de dados climáticos reais
==================================================

Este módulo fornece integração com APIs climáticas (OpenMeteo)
para obter dados meteorológicos reais para análise de riscos.

Componentes:
- openmeteo_client: Cliente para API OpenMeteo
- weather_cache: Sistema de cache com SQLite
- weather_service: Serviço principal com fallbacks
- weather_models: Modelos de dados climáticos
"""

__version__ = "1.0.0"
__author__ = "Radar Sinistro Team"

from .weather_service import WeatherService
from .weather_models import WeatherData, WeatherConditions

__all__ = [
    'WeatherService',
    'WeatherData', 
    'WeatherConditions'
]