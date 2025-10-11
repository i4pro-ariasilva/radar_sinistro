"""
Test suite para o projeto Radar de Sinistro
Estrutura de testes organizados por módulos
"""

import pytest
import sys
import os
from pathlib import Path

# Configuração do path para os testes
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configurações globais para testes
pytest_plugins = []

# Configuração de logging para testes
import logging
logging.basicConfig(level=logging.WARNING)