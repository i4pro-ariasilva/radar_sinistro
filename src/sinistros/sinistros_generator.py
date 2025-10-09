"""
Gerador de Sinistros Históricos
Sistema inteligente para gerar sinistros históricos realistas
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import numpy as np

from .sinistros_types import (
    TiposSinistro, CausasSinistro, SeveridadeSinistro,
    get_causa_para_tipo, get_condicoes_climaticas_para_tipo,
    calcular_valor_prejuizo
)

class SinistrosHistoricosGenerator:
    """
    Gerador inteligente de sinistros históricos com base em padrões realistas
    """
    
    def __init__(self):
        self.tipos_disponiveis = list(TiposSinistro)
        self.sazonalidade_config = self._setup_sazonalidade()
        
    def _setup_sazonalidade(self) -> Dict:
        """Configura padrões sazonais para cada tipo de sinistro"""
        return {
            TiposSinistro.ENCHENTE: {
                'meses_pico': [11, 12, 1, 2, 3],  # Verão
                'probabilidade_base': 0.15
            },
            TiposSinistro.VENDAVAL: {
                'meses_pico': [9, 10, 11, 12],    # Primavera/Verão
                'probabilidade_base': 0.12
            },
            TiposSinistro.GRANIZO: {
                'meses_pico': [10, 11, 12, 1],    # Verão
                'probabilidade_base': 0.08
            },
            TiposSinistro.QUEIMADAS: {
                'meses_pico': [6, 7, 8, 9],       # Inverno/Seca
                'probabilidade_base': 0.10
            },
            TiposSinistro.ALAGAMENTO: {
                'meses_pico': [12, 1, 2, 3],      # Verão
                'probabilidade_base': 0.12
            },
            TiposSinistro.DESTELHAMENTO: {
                'meses_pico': [10, 11, 12, 1, 2], # Primavera/Verão
                'probabilidade_base': 0.10
            },
            TiposSinistro.INFILTRACAO: {
                'meses_pico': [11, 12, 1, 2, 3, 4], # Verão/Outono
                'probabilidade_base': 0.15
            },
            TiposSinistro.QUEDA_ARVORE: {
                'meses_pico': [9, 10, 11, 12, 1], # Ventos fortes
                'probabilidade_base': 0.08
            }
        }
    
    def generate_sinistros_for_policies(self, policies: List[Dict], 
                                      num_sinistros: int = None,
                                      periodo_dias: int = 365) -> List[Dict]:
        """
        Gera sinistros históricos baseados nas apólices fornecidas
        
        Args:
            policies: Lista de apólices
            num_sinistros: Número de sinistros (None = automático)
            periodo_dias: Período em dias para gerar sinistros
            
        Returns:
            Lista de sinistros históricos
        """
        
        if not policies:
            return []
        
        # Filtrar apenas apólices ativas
        active_policies = [p for p in policies if p.get('ativa', True)]
        
        if not active_policies:
            return []
        
        # Calcular número automático se não especificado
        if num_sinistros is None:
            # 15-25% das apólices podem ter sinistros
            num_sinistros = int(len(active_policies) * random.uniform(0.15, 0.25))
            num_sinistros = max(1, min(num_sinistros, len(active_policies)))
        
        sinistros = []
        
        print(f"🌩️ Gerando {num_sinistros} sinistros para {len(active_policies)} apólices...")
        
        for i in range(num_sinistros):
            try:
                # Selecionar apólice aleatória
                policy = random.choice(active_policies)
                
                # Gerar sinistro
                sinistro = self._generate_single_sinistro(policy, periodo_dias)
                sinistros.append(sinistro)
                
                if (i + 1) % 10 == 0:
                    print(f"  ✅ {i + 1}/{num_sinistros} sinistros gerados...")
                    
            except Exception as e:
                print(f"  ⚠️ Erro ao gerar sinistro {i + 1}: {e}")
                continue
        
        print(f"✅ Total de {len(sinistros)} sinistros gerados com sucesso!")
        return sinistros
    
    def _generate_single_sinistro(self, policy: Dict, periodo_dias: int) -> Dict:
        """Gera um único sinistro para uma apólice"""
        
        # Data do sinistro (após contratação, dentro do período)
        data_sinistro = self._generate_sinistro_date(policy, periodo_dias)
        
        # Selecionar tipo de sinistro baseado na sazonalidade
        tipo_sinistro = self._select_tipo_sazonal(data_sinistro.month)
        
        # Gerar causa apropriada
        causa = get_causa_para_tipo(tipo_sinistro)
        
        # Calcular valor do prejuízo
        valor_segurado = float(policy.get('valor_segurado', 200000))
        valor_prejuizo = calcular_valor_prejuizo(tipo_sinistro, valor_segurado)
        
        # Gerar condições climáticas apropriadas
        condicoes_climaticas = get_condicoes_climaticas_para_tipo(tipo_sinistro)
        
        # Coordenadas próximas à apólice
        lat_base = float(policy.get('latitude', -23.5505))
        lon_base = float(policy.get('longitude', -46.6333))
        
        # Variação de até ~1km
        lat_variation = random.uniform(-0.01, 0.01)
        lon_variation = random.uniform(-0.01, 0.01)
        
        sinistro_lat = lat_base + lat_variation
        sinistro_lon = lon_base + lon_variation
        
        return {
            'numero_apolice': policy['numero_apolice'],
            'data_sinistro': data_sinistro.strftime('%Y-%m-%d %H:%M:%S'),
            'tipo_sinistro': tipo_sinistro.value,
            'valor_prejuizo': valor_prejuizo,
            'causa': causa.value,
            'latitude': round(sinistro_lat, 6),
            'longitude': round(sinistro_lon, 6),
            'condicoes_climaticas': json.dumps(condicoes_climaticas, ensure_ascii=False),
            'precipitacao_mm': condicoes_climaticas['precipitacao_mm'],
            'vento_kmh': condicoes_climaticas['vento_kmh'],
            'temperatura_c': condicoes_climaticas['temperatura_c'],
            'umidade_percent': condicoes_climaticas.get('umidade_percent', 70),
            'severidade': self._calculate_severidade(valor_prejuizo, valor_segurado).value[0]
        }
    
    def _generate_sinistro_date(self, policy: Dict, periodo_dias: int) -> datetime:
        """Gera data do sinistro após a contratação da apólice"""
        
        # Data de contratação
        data_contratacao_str = policy.get('data_contratacao')
        if isinstance(data_contratacao_str, str):
            data_contratacao = datetime.strptime(data_contratacao_str, '%Y-%m-%d')
        else:
            data_contratacao = data_contratacao_str
        
        # Data máxima (hoje ou contratação + período)
        data_maxima = min(
            datetime.now(),
            data_contratacao + timedelta(days=periodo_dias)
        )
        
        # Garantir que há tempo suficiente
        if data_maxima <= data_contratacao:
            data_maxima = data_contratacao + timedelta(days=30)
        
        # Gerar data aleatória no período
        delta_days = (data_maxima - data_contratacao).days
        random_days = random.randint(1, max(1, delta_days))
        random_hours = random.randint(0, 23)
        random_minutes = random.randint(0, 59)
        
        return data_contratacao + timedelta(
            days=random_days,
            hours=random_hours, 
            minutes=random_minutes
        )
    
    def _select_tipo_sazonal(self, mes: int) -> TiposSinistro:
        """Seleciona tipo de sinistro baseado na sazonalidade"""
        
        # Calcular probabilidades ajustadas pela sazonalidade
        probabilidades = {}
        
        for tipo, config in self.sazonalidade_config.items():
            prob_base = config['probabilidade_base']
            
            if mes in config['meses_pico']:
                # Aumentar probabilidade na época de pico
                probabilidades[tipo] = prob_base * 2.5
            else:
                # Probabilidade reduzida fora da época
                probabilidades[tipo] = prob_base * 0.5
        
        # Normalizar probabilidades
        total = sum(probabilidades.values())
        for tipo in probabilidades:
            probabilidades[tipo] /= total
        
        # Seleção ponderada
        tipos = list(probabilidades.keys())
        pesos = list(probabilidades.values())
        
        return np.random.choice(tipos, p=pesos)
    
    def _calculate_severidade(self, valor_prejuizo: float, valor_segurado: float) -> SeveridadeSinistro:
        """Calcula severidade baseada na proporção do prejuízo"""
        
        proporcao = valor_prejuizo / valor_segurado
        
        if proporcao < 0.1:
            return SeveridadeSinistro.LEVE
        elif proporcao < 0.3:
            return SeveridadeSinistro.MODERADO
        elif proporcao < 0.6:
            return SeveridadeSinistro.GRAVE
        elif proporcao < 0.9:
            return SeveridadeSinistro.SEVERO
        else:
            return SeveridadeSinistro.CATASTROFICO
    
    def generate_bulk_sinistros(self, policies: List[Dict], 
                               distribuicao_tipos: Dict[TiposSinistro, float] = None) -> List[Dict]:
        """
        Gera sinistros em lote com distribuição personalizada
        
        Args:
            policies: Lista de apólices
            distribuicao_tipos: Distribuição personalizada por tipo
            
        Returns:
            Lista de sinistros gerados
        """
        
        if distribuicao_tipos is None:
            # Distribuição padrão brasileira
            distribuicao_tipos = {
                TiposSinistro.ENCHENTE: 0.25,
                TiposSinistro.VENDAVAL: 0.20,
                TiposSinistro.ALAGAMENTO: 0.15,
                TiposSinistro.GRANIZO: 0.12,
                TiposSinistro.INFILTRACAO: 0.10,
                TiposSinistro.DESTELHAMENTO: 0.08,
                TiposSinistro.QUEIMADAS: 0.05,
                TiposSinistro.QUEDA_ARVORE: 0.05
            }
        
        total_sinistros = int(len(policies) * 0.2)  # 20% das apólices
        sinistros = []
        
        for tipo, proporcao in distribuicao_tipos.items():
            num_tipo = int(total_sinistros * proporcao)
            
            for _ in range(num_tipo):
                policy = random.choice(policies)
                sinistro = self._generate_single_sinistro(policy, 365)
                sinistro['tipo_sinistro'] = tipo.value
                sinistros.append(sinistro)
        
        return sinistros
    
    def get_estatisticas_geradas(self, sinistros: List[Dict]) -> Dict:
        """Retorna estatísticas dos sinistros gerados"""
        
        if not sinistros:
            return {'total': 0}
        
        # Contar por tipo
        tipos_count = {}
        valores_por_tipo = {}
        
        for sinistro in sinistros:
            tipo = sinistro['tipo_sinistro']
            valor = sinistro['valor_prejuizo']
            
            tipos_count[tipo] = tipos_count.get(tipo, 0) + 1
            if tipo not in valores_por_tipo:
                valores_por_tipo[tipo] = []
            valores_por_tipo[tipo].append(valor)
        
        # Calcular estatísticas
        total_valor = sum(s['valor_prejuizo'] for s in sinistros)
        valor_medio = total_valor / len(sinistros)
        
        return {
            'total': len(sinistros),
            'valor_total': total_valor,
            'valor_medio': valor_medio,
            'distribuicao_tipos': tipos_count,
            'valores_por_tipo': {
                tipo: {
                    'total': sum(valores),
                    'medio': np.mean(valores),
                    'maximo': max(valores),
                    'minimo': min(valores)
                }
                for tipo, valores in valores_por_tipo.items()
            }
        }