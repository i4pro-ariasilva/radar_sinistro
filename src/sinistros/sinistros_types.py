"""
Tipos e Categorias de Sinistros
Define todos os tipos de sinistros suportados pelo sistema
"""

from enum import Enum
from typing import Dict, List, Tuple
import random

class TiposSinistro(Enum):
    """Tipos de sinistros suportados"""
    ENCHENTE = "Enchente"
    VENDAVAL = "Vendaval" 
    GRANIZO = "Granizo"
    QUEIMADAS = "Queimadas"
    ALAGAMENTO = "Alagamento"
    DESTELHAMENTO = "Destelhamento"
    INFILTRACAO = "Infiltração"
    QUEDA_ARVORE = "Queda de árvore"
    TEMPESTADE = "Tempestade"
    TORNADO = "Tornado"
    RAIO = "Raio"
    SECA = "Seca"

class CausasSinistro(Enum):
    """Causas dos sinistros"""
    CHUVA_INTENSA = "Chuva intensa"
    VENTO_FORTE = "Vento forte"
    TEMPESTADE = "Tempestade"
    GRANIZO_SEVERO = "Granizo severo"
    ALAGAMENTO_URBANO = "Alagamento urbano"
    TRANSBORDAMENTO_RIO = "Transbordamento de rio"
    TEMPORAL = "Temporal"
    INCENDIO_FLORESTAL = "Incêndio florestal"
    QUEIMADA_CONTROLADA = "Queimada descontrolada"
    SECA_PROLONGADA = "Seca prolongada"
    ATIVIDADE_ELETRICA = "Atividade elétrica"
    FENOMENO_CLIMATICO = "Fenômeno climático extremo"

class SeveridadeSinistro(Enum):
    """Níveis de severidade"""
    LEVE = ("Leve", 1)
    MODERADO = ("Moderado", 2)
    GRAVE = ("Grave", 3)
    SEVERO = ("Severo", 4)
    CATASTROFICO = ("Catastrófico", 5)

class SinistroConfig:
    """Configurações para geração de sinistros"""
    
    # Mapeamento tipo -> causas mais prováveis
    TIPO_CAUSA_MAP: Dict[TiposSinistro, List[CausasSinistro]] = {
        TiposSinistro.ENCHENTE: [
            CausasSinistro.CHUVA_INTENSA,
            CausasSinistro.TRANSBORDAMENTO_RIO,
            CausasSinistro.TEMPESTADE
        ],
        TiposSinistro.VENDAVAL: [
            CausasSinistro.VENTO_FORTE,
            CausasSinistro.TEMPESTADE,
            CausasSinistro.TEMPORAL
        ],
        TiposSinistro.GRANIZO: [
            CausasSinistro.GRANIZO_SEVERO,
            CausasSinistro.TEMPESTADE,
            CausasSinistro.TEMPORAL
        ],
        TiposSinistro.QUEIMADAS: [
            CausasSinistro.INCENDIO_FLORESTAL,
            CausasSinistro.QUEIMADA_CONTROLADA,
            CausasSinistro.SECA_PROLONGADA
        ],
        TiposSinistro.ALAGAMENTO: [
            CausasSinistro.CHUVA_INTENSA,
            CausasSinistro.ALAGAMENTO_URBANO,
            CausasSinistro.TEMPESTADE
        ],
        TiposSinistro.DESTELHAMENTO: [
            CausasSinistro.VENTO_FORTE,
            CausasSinistro.TEMPESTADE,
            CausasSinistro.GRANIZO_SEVERO
        ],
        TiposSinistro.INFILTRACAO: [
            CausasSinistro.CHUVA_INTENSA,
            CausasSinistro.TEMPESTADE,
            CausasSinistro.TEMPORAL
        ],
        TiposSinistro.QUEDA_ARVORE: [
            CausasSinistro.VENTO_FORTE,
            CausasSinistro.TEMPESTADE,
            CausasSinistro.TEMPORAL
        ],
        TiposSinistro.RAIO: [
            CausasSinistro.ATIVIDADE_ELETRICA,
            CausasSinistro.TEMPESTADE,
            CausasSinistro.TEMPORAL
        ]
    }
    
    # Condições climáticas típicas por tipo de sinistro
    CONDICOES_CLIMATICAS_TIPO: Dict[TiposSinistro, Dict] = {
        TiposSinistro.ENCHENTE: {
            'precipitacao_min': 50,
            'precipitacao_max': 200,
            'temperatura_min': 18,
            'temperatura_max': 35,
            'vento_min': 5,
            'vento_max': 40
        },
        TiposSinistro.VENDAVAL: {
            'precipitacao_min': 0,
            'precipitacao_max': 50,
            'temperatura_min': 15,
            'temperatura_max': 30,
            'vento_min': 40,
            'vento_max': 100
        },
        TiposSinistro.GRANIZO: {
            'precipitacao_min': 20,
            'precipitacao_max': 80,
            'temperatura_min': 8,
            'temperatura_max': 25,
            'vento_min': 20,
            'vento_max': 70
        },
        TiposSinistro.QUEIMADAS: {
            'precipitacao_min': 0,
            'precipitacao_max': 5,
            'temperatura_min': 25,
            'temperatura_max': 45,
            'vento_min': 10,
            'vento_max': 50,
            'umidade_min': 10,
            'umidade_max': 40
        },
        TiposSinistro.ALAGAMENTO: {
            'precipitacao_min': 30,
            'precipitacao_max': 150,
            'temperatura_min': 20,
            'temperatura_max': 35,
            'vento_min': 5,
            'vento_max': 30
        }
    }
    
    # Fator de severidade por tipo (multiplicador do valor base)
    SEVERIDADE_FATOR: Dict[TiposSinistro, Tuple[float, float]] = {
        TiposSinistro.ENCHENTE: (0.3, 0.9),      # 30-90% do valor segurado
        TiposSinistro.VENDAVAL: (0.1, 0.6),      # 10-60% do valor segurado
        TiposSinistro.GRANIZO: (0.1, 0.5),       # 10-50% do valor segurado
        TiposSinistro.QUEIMADAS: (0.4, 1.0),     # 40-100% do valor segurado
        TiposSinistro.ALAGAMENTO: (0.2, 0.7),    # 20-70% do valor segurado
        TiposSinistro.DESTELHAMENTO: (0.1, 0.4), # 10-40% do valor segurado
        TiposSinistro.INFILTRACAO: (0.05, 0.3),  # 5-30% do valor segurado
        TiposSinistro.QUEDA_ARVORE: (0.1, 0.5),  # 10-50% do valor segurado
        TiposSinistro.RAIO: (0.1, 0.6)           # 10-60% do valor segurado
    }

def get_causa_para_tipo(tipo: TiposSinistro) -> CausasSinistro:
    """Retorna uma causa apropriada para o tipo de sinistro"""
    causas_possiveis = SinistroConfig.TIPO_CAUSA_MAP.get(tipo, [CausasSinistro.FENOMENO_CLIMATICO])
    return random.choice(causas_possiveis)

def get_condicoes_climaticas_para_tipo(tipo: TiposSinistro) -> Dict:
    """Gera condições climáticas realistas para o tipo de sinistro"""
    config = SinistroConfig.CONDICOES_CLIMATICAS_TIPO.get(tipo, {})
    
    if not config:
        # Condições padrão se tipo não mapeado
        return {
            'temperatura_c': round(random.uniform(15, 35), 1),
            'precipitacao_mm': round(random.uniform(0, 50), 1),
            'vento_kmh': round(random.uniform(5, 40), 1),
            'umidade_percent': round(random.uniform(40, 90), 1)
        }
    
    condicoes = {
        'temperatura_c': round(random.uniform(
            config.get('temperatura_min', 15),
            config.get('temperatura_max', 35)
        ), 1),
        'precipitacao_mm': round(random.uniform(
            config.get('precipitacao_min', 0),
            config.get('precipitacao_max', 50)
        ), 1),
        'vento_kmh': round(random.uniform(
            config.get('vento_min', 5),
            config.get('vento_max', 40)
        ), 1),
        'umidade_percent': round(random.uniform(
            config.get('umidade_min', 40),
            config.get('umidade_max', 90)
        ), 1)
    }
    
    return condicoes

def calcular_valor_prejuizo(tipo: TiposSinistro, valor_segurado: float) -> float:
    """Calcula valor do prejuízo baseado no tipo e valor segurado"""
    fator_min, fator_max = SinistroConfig.SEVERIDADE_FATOR.get(tipo, (0.1, 0.5))
    fator = random.uniform(fator_min, fator_max)
    
    # Adicionar variação adicional
    variacao = random.uniform(0.8, 1.2)
    
    valor_prejuizo = valor_segurado * fator * variacao
    
    # Valor mínimo de R$ 1.000
    return max(1000.0, round(valor_prejuizo, 2))