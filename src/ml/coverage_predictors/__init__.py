#!/usr/bin/env python3
"""
Modelos específicos de predição de risco por cobertura
Sistema modular com um arquivo para cada tipo de cobertura
"""

from .base_predictor import CoverageSpecificPredictor
from .danos_eletricos import DanosEletricosPredictor
from .vendaval import VendavalPredictor
from .granizo import GranizoPredictor
from .alagamento import AlagamentoPredictor
from .coverage_manager import CoverageRiskManager

__all__ = [
    'CoverageSpecificPredictor',
    'DanosEletricosPredictor', 
    'VendavalPredictor',
    'GranizoPredictor',
    'AlagamentoPredictor',
    'CoverageRiskManager'
]
