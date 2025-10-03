"""
Inicializador do módulo database
"""

from .database import Database, get_database
from .models import (
    Apolice, SinistroHistorico, PrevisaoRisco, DadoClimatico,
    ApoliceAtiva, PrevisaoRecente, TipoResidencia, NivelRisco,
    determinar_nivel_risco, validar_cep, normalizar_cep
)
from .crud_operations import CRUDOperations
from .sample_data_generator import SampleDataGenerator

__all__ = [
    'Database', 'get_database',
    'Apolice', 'SinistroHistorico', 'PrevisaoRisco', 'DadoClimatico',
    'ApoliceAtiva', 'PrevisaoRecente', 'TipoResidencia', 'NivelRisco',
    'determinar_nivel_risco', 'validar_cep', 'normalizar_cep',
    'CRUDOperations', 'SampleDataGenerator'
]