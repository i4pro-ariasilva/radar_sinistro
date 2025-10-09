"""
Módulo de Sinistros Históricos
Sistema completo para geração, análise e gestão de sinistros históricos
"""

from .sinistros_generator import SinistrosHistoricosGenerator
from .sinistros_analyzer import SinistrosAnalyzer
from .sinistros_types import TiposSinistro, CausasSinistro

__all__ = [
    'SinistrosHistoricosGenerator',
    'SinistrosAnalyzer', 
    'TiposSinistro',
    'CausasSinistro'
]