"""
Módulo de relatórios automáticos
"""

from .auto_reports import (
    auto_generate_weather_reports,
    get_weather_cache_summary,
    cleanup_expired_cache
)

__all__ = [
    'auto_generate_weather_reports',
    'get_weather_cache_summary', 
    'cleanup_expired_cache'
]