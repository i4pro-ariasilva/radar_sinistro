"""
Analisador de Sinistros Históricos
Sistema para análise e insights de sinistros históricos
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import json

from .sinistros_types import TiposSinistro

class SinistrosAnalyzer:
    """
    Analisador de sinistros históricos com insights e padrões
    """
    
    def __init__(self):
        self.sinistros_df = None
        
    def load_sinistros(self, sinistros: List[Dict]) -> pd.DataFrame:
        """Carrega sinistros para análise"""
        
        if not sinistros:
            return pd.DataFrame()
        
        self.sinistros_df = pd.DataFrame(sinistros)
        
        # Converter datas
        self.sinistros_df['data_sinistro'] = pd.to_datetime(self.sinistros_df['data_sinistro'])
        
        # Extrair componentes de data
        self.sinistros_df['ano'] = self.sinistros_df['data_sinistro'].dt.year
        self.sinistros_df['mes'] = self.sinistros_df['data_sinistro'].dt.month
        self.sinistros_df['dia_semana'] = self.sinistros_df['data_sinistro'].dt.dayofweek
        self.sinistros_df['trimestre'] = self.sinistros_df['data_sinistro'].dt.quarter
        
        # Converter condições climáticas se existir
        if 'condicoes_climaticas' in self.sinistros_df.columns:
            self._expand_climate_data()
        
        return self.sinistros_df
    
    def _expand_climate_data(self):
        """Expande dados climáticos do JSON"""
        
        def extract_climate(row):
            try:
                if pd.isna(row) or row == '':
                    return {}
                if isinstance(row, str):
                    return json.loads(row)
                return row
            except:
                return {}
        
        climate_data = self.sinistros_df['condicoes_climaticas'].apply(extract_climate)
        
        # Extrair campos climáticos
        for field in ['temperatura_c', 'precipitacao_mm', 'vento_kmh', 'umidade_percent']:
            if field not in self.sinistros_df.columns:
                self.sinistros_df[f'clima_{field}'] = climate_data.apply(lambda x: x.get(field, None))
    
    def analyze_patterns(self) -> Dict:
        """Analisa padrões nos sinistros"""
        
        if self.sinistros_df is None or self.sinistros_df.empty:
            return {}
        
        patterns = {}
        
        # Padrões temporais
        patterns['temporal'] = self._analyze_temporal_patterns()
        
        # Padrões por tipo
        patterns['por_tipo'] = self._analyze_type_patterns()
        
        # Padrões climáticos
        patterns['climatico'] = self._analyze_climate_patterns()
        
        # Padrões financeiros
        patterns['financeiro'] = self._analyze_financial_patterns()
        
        # Padrões geográficos
        patterns['geografico'] = self._analyze_geographic_patterns()
        
        return patterns
    
    def _analyze_temporal_patterns(self) -> Dict:
        """Analisa padrões temporais"""
        
        # Distribuição por mês
        monthly_dist = self.sinistros_df['mes'].value_counts().sort_index()
        
        # Distribuição por dia da semana
        weekday_dist = self.sinistros_df['dia_semana'].value_counts().sort_index()
        
        # Tendência anual
        yearly_trend = self.sinistros_df.groupby('ano').agg({
            'valor_prejuizo': ['count', 'sum', 'mean']
        }).round(2)
        
        # Sazonalidade por tipo
        seasonal_by_type = self.sinistros_df.groupby(['tipo_sinistro', 'mes']).size().unstack(fill_value=0)
        
        return {
            'distribuicao_mensal': monthly_dist.to_dict(),
            'distribuicao_semanal': weekday_dist.to_dict(),
            'tendencia_anual': yearly_trend.to_dict(),
            'sazonalidade_por_tipo': seasonal_by_type.to_dict(),
            'meses_pico': monthly_dist.idxmax(),
            'mes_mais_calmo': monthly_dist.idxmin()
        }
    
    def _analyze_type_patterns(self) -> Dict:
        """Analisa padrões por tipo de sinistro"""
        
        type_analysis = self.sinistros_df.groupby('tipo_sinistro').agg({
            'valor_prejuizo': ['count', 'sum', 'mean', 'median', 'std'],
            'precipitacao_mm': 'mean',
            'vento_kmh': 'mean',
            'temperatura_c': 'mean'
        }).round(2)
        
        # Frequência por tipo
        frequency = self.sinistros_df['tipo_sinistro'].value_counts()
        
        # Severidade média por tipo
        severity = self.sinistros_df.groupby('tipo_sinistro')['valor_prejuizo'].mean().sort_values(ascending=False)
        
        return {
            'estatisticas_por_tipo': type_analysis.to_dict(),
            'frequencia': frequency.to_dict(),
            'severidade_media': severity.to_dict(),
            'tipo_mais_frequente': frequency.index[0],
            'tipo_mais_custoso': severity.index[0]
        }
    
    def _analyze_climate_patterns(self) -> Dict:
        """Analisa padrões climáticos"""
        
        climate_cols = ['precipitacao_mm', 'vento_kmh', 'temperatura_c']
        available_cols = [col for col in climate_cols if col in self.sinistros_df.columns]
        
        if not available_cols:
            return {'erro': 'Dados climáticos não disponíveis'}
        
        # Estatísticas climáticas gerais
        climate_stats = self.sinistros_df[available_cols].describe().round(2)
        
        # Correlação com valor do prejuízo
        correlations = {}
        for col in available_cols:
            if self.sinistros_df[col].notna().sum() > 0:
                corr = self.sinistros_df[col].corr(self.sinistros_df['valor_prejuizo'])
                correlations[col] = round(corr, 3) if not pd.isna(corr) else 0
        
        # Condições extremas
        extreme_conditions = {}
        for col in available_cols:
            if self.sinistros_df[col].notna().sum() > 0:
                q95 = self.sinistros_df[col].quantile(0.95)
                extreme_conditions[f'{col}_extremo'] = len(self.sinistros_df[self.sinistros_df[col] >= q95])
        
        return {
            'estatisticas_climaticas': climate_stats.to_dict(),
            'correlacoes_prejuizo': correlations,
            'condicoes_extremas': extreme_conditions
        }
    
    def _analyze_financial_patterns(self) -> Dict:
        """Analisa padrões financeiros"""
        
        # Estatísticas de valor
        value_stats = self.sinistros_df['valor_prejuizo'].describe()
        
        # Distribuição por faixas de valor
        bins = [0, 10000, 50000, 100000, 500000, float('inf')]
        labels = ['Até 10k', '10k-50k', '50k-100k', '100k-500k', '500k+']
        self.sinistros_df['faixa_valor'] = pd.cut(self.sinistros_df['valor_prejuizo'], 
                                                  bins=bins, labels=labels)
        
        value_distribution = self.sinistros_df['faixa_valor'].value_counts()
        
        # Top 10 sinistros mais custosos
        top_expensive = self.sinistros_df.nlargest(10, 'valor_prejuizo')[
            ['tipo_sinistro', 'valor_prejuizo', 'data_sinistro']
        ]
        
        return {
            'estatisticas_valor': value_stats.to_dict(),
            'distribuicao_faixas': value_distribution.to_dict(),
            'top_10_custosos': top_expensive.to_dict('records'),
            'valor_total': self.sinistros_df['valor_prejuizo'].sum(),
            'valor_medio_mensal': self.sinistros_df.groupby('mes')['valor_prejuizo'].mean().to_dict()
        }
    
    def _analyze_geographic_patterns(self) -> Dict:
        """Analisa padrões geográficos"""
        
        geo_cols = ['latitude', 'longitude']
        available_geo = [col for col in geo_cols if col in self.sinistros_df.columns]
        
        if len(available_geo) < 2:
            return {'erro': 'Dados geográficos incompletos'}
        
        # Estatísticas geográficas
        geo_stats = self.sinistros_df[available_geo].describe()
        
        # Concentração geográfica (agrupamento por região aproximada)
        self.sinistros_df['lat_round'] = self.sinistros_df['latitude'].round(2)
        self.sinistros_df['lon_round'] = self.sinistros_df['longitude'].round(2)
        
        geographic_clusters = self.sinistros_df.groupby(['lat_round', 'lon_round']).agg({
            'valor_prejuizo': ['count', 'sum'],
            'tipo_sinistro': lambda x: x.value_counts().index[0]  # Tipo mais comum
        })
        
        # Top 5 regiões com mais sinistros
        top_regions = self.sinistros_df.groupby(['lat_round', 'lon_round']).size().nlargest(5)
        
        return {
            'estatisticas_geograficas': geo_stats.to_dict(),
            'top_5_regioes': top_regions.to_dict(),
            'dispersao_geografica': {
                'amplitude_lat': geo_stats.loc['max', 'latitude'] - geo_stats.loc['min', 'latitude'],
                'amplitude_lon': geo_stats.loc['max', 'longitude'] - geo_stats.loc['min', 'longitude']
            }
        }
    
    def generate_risk_insights(self) -> Dict:
        """Gera insights de risco baseados nos padrões"""
        
        if self.sinistros_df is None or self.sinistros_df.empty:
            return {}
        
        patterns = self.analyze_patterns()
        
        insights = {
            'alertas': [],
            'recomendacoes': [],
            'tendencias': [],
            'oportunidades': []
        }
        
        # Alertas baseados em padrões
        if 'temporal' in patterns:
            mes_pico = patterns['temporal'].get('meses_pico')
            if mes_pico:
                insights['alertas'].append(f"Mês {mes_pico} apresenta maior concentração de sinistros")
        
        if 'por_tipo' in patterns:
            tipo_custoso = patterns['por_tipo'].get('tipo_mais_custoso')
            if tipo_custoso:
                insights['alertas'].append(f"Sinistros tipo '{tipo_custoso}' são os mais custosos")
        
        # Recomendações
        insights['recomendacoes'].extend([
            "Implementar monitoramento climático preventivo",
            "Ajustar apólices baseado em padrões sazonais",
            "Criar campanhas de conscientização para tipos mais frequentes"
        ])
        
        # Tendências
        if 'financeiro' in patterns:
            valor_total = patterns['financeiro'].get('valor_total', 0)
            qtd_total = len(self.sinistros_df)
            insights['tendencias'].append(f"Valor médio por sinistro: R$ {valor_total/qtd_total:,.2f}")
        
        return insights
    
    def export_analysis_report(self, filename: str = None) -> str:
        """Exporta relatório de análise completo"""
        
        if filename is None:
            filename = f"relatorio_sinistros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'metadata': {
                'data_geracao': datetime.now().isoformat(),
                'total_sinistros': len(self.sinistros_df) if self.sinistros_df is not None else 0,
                'periodo_analise': {
                    'inicio': self.sinistros_df['data_sinistro'].min().isoformat() if self.sinistros_df is not None else None,
                    'fim': self.sinistros_df['data_sinistro'].max().isoformat() if self.sinistros_df is not None else None
                }
            },
            'padroes': self.analyze_patterns(),
            'insights': self.generate_risk_insights()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        return filename