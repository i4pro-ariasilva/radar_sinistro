#!/usr/bin/env python3
"""
Gerador de dados simulados para treinamento dos modelos de cobertura.
Cria datasets sintéticos realistas baseados em padrões meteorológicos brasileiros.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple
import os

class WeatherDataSimulator:
    """Simula dados climáticos realistas para diferentes regiões do Brasil"""
    
    def __init__(self):
        # Padrões climáticos por região (baseado em dados reais)
        self.regional_patterns = {
            'sudeste': {
                'temp_range': (15, 35),
                'humidity_range': (40, 90),
                'pressure_range': (1005, 1025),
                'precipitation_patterns': {
                    'verao': {'freq': 0.4, 'intensity': (10, 80)},
                    'inverno': {'freq': 0.1, 'intensity': (5, 30)},
                    'outono': {'freq': 0.25, 'intensity': (8, 50)},
                    'primavera': {'freq': 0.3, 'intensity': (12, 60)}
                }
            },
            'sul': {
                'temp_range': (10, 30),
                'humidity_range': (50, 95),
                'pressure_range': (1000, 1020),
                'precipitation_patterns': {
                    'verao': {'freq': 0.35, 'intensity': (15, 70)},
                    'inverno': {'freq': 0.3, 'intensity': (10, 40)},
                    'outono': {'freq': 0.4, 'intensity': (12, 55)},
                    'primavera': {'freq': 0.35, 'intensity': (15, 65)}
                }
            },
            'nordeste': {
                'temp_range': (22, 38),
                'humidity_range': (30, 80),
                'pressure_range': (1010, 1020),
                'precipitation_patterns': {
                    'verao': {'freq': 0.6, 'intensity': (20, 100)},
                    'inverno': {'freq': 0.05, 'intensity': (5, 20)},
                    'outono': {'freq': 0.3, 'intensity': (10, 60)},
                    'primavera': {'freq': 0.15, 'intensity': (8, 40)}
                }
            }
        }
    
    def get_season(self, month: int) -> str:
        """Retorna estação baseada no mês (hemisfério sul)"""
        if month in [12, 1, 2]:
            return 'verao'
        elif month in [3, 4, 5]:
            return 'outono'
        elif month in [6, 7, 8]:
            return 'inverno'
        else:
            return 'primavera'
    
    def get_region_by_cep(self, cep: str) -> str:
        """Determina região baseada no CEP"""
        if len(cep) < 2:
            return 'sudeste'
        
        first_two = cep[:2]
        if first_two in ['01', '02', '03', '04', '05', '06', '07', '08', '09', 
                        '11', '12', '13', '14', '15', '16', '17', '18', '19']:
            return 'sudeste'
        elif first_two in ['80', '81', '82', '83', '84', '85', '86', '87', '88', '89',
                          '90', '91', '92', '93', '94', '95', '96', '97', '98', '99']:
            return 'sul'
        else:
            return 'nordeste'
    
    def simulate_weather_conditions(self, cep: str, date: datetime, 
                                  extreme_event: str = None) -> Dict:
        """
        Simula condições climáticas para uma data específica
        
        Args:
            cep: CEP da localização
            date: Data para simular
            extreme_event: Tipo de evento extremo (tempestade, seca, etc.)
        """
        region = self.get_region_by_cep(cep)
        season = self.get_season(date.month)
        patterns = self.regional_patterns[region]
        
        # Temperatura base
        temp_min, temp_max = patterns['temp_range']
        
        # Ajuste sazonal
        seasonal_adj = {
            'verao': 5, 'outono': 0, 'inverno': -8, 'primavera': 2
        }[season]
        
        temp_min += seasonal_adj
        temp_max += seasonal_adj
        
        # Temperatura atual (com variação diária)
        hour_factor = np.sin((date.hour - 6) * np.pi / 12)  # Pico às 14h
        daily_temp = temp_min + (temp_max - temp_min) * max(0, hour_factor)
        
        # Adicionar ruído
        temperature = daily_temp + np.random.normal(0, 2)
        
        # Umidade (inversamente relacionada à temperatura)
        humidity_min, humidity_max = patterns['humidity_range']
        humidity_base = humidity_max - ((temperature - temp_min) / (temp_max - temp_min)) * (humidity_max - humidity_min)
        humidity = max(humidity_min, min(humidity_max, humidity_base + np.random.normal(0, 10)))
        
        # Pressão atmosférica
        pressure_min, pressure_max = patterns['pressure_range']
        pressure = np.random.uniform(pressure_min, pressure_max)
        
        # Precipitação baseada em padrões sazonais
        precip_pattern = patterns['precipitation_patterns'][season]
        has_rain = np.random.random() < precip_pattern['freq']
        precipitation = 0.0
        
        if has_rain:
            precip_min, precip_max = precip_pattern['intensity']
            precipitation = np.random.uniform(precip_min, precip_max)
        
        # Vento (baseado em pressão e precipitação)
        wind_base = 5 + (1020 - pressure) * 0.5  # Vento aumenta com baixa pressão
        if precipitation > 30:  # Tempestade
            wind_base *= 2
        wind_speed = max(0, wind_base + np.random.normal(0, 5))
        
        # Aplicar eventos extremos
        if extreme_event:
            temperature, humidity, pressure, precipitation, wind_speed = self._apply_extreme_event(
                extreme_event, temperature, humidity, pressure, precipitation, wind_speed
            )
        
        return {
            'temperatura_atual': round(temperature, 1),
            'temperatura_maxima': round(temperature + np.random.uniform(0, 5), 1),
            'temperatura_minima': round(temperature - np.random.uniform(0, 8), 1),
            'umidade_relativa': round(humidity, 1),
            'pressao_atmosferica': round(pressure, 1),
            'velocidade_vento': round(wind_speed, 1),
            'direcao_vento': round(np.random.uniform(0, 360), 1),
            'precipitacao_mm': round(precipitation, 1),
            'visibilidade': round(np.random.uniform(5000, 15000), 0),
            'cobertura_nuvens': round(min(100, precipitation * 2 + np.random.uniform(10, 50)), 1),
            'indice_uv': round(max(0, min(12, (temperature - 15) * 0.3 + np.random.uniform(1, 3))), 1),
            'sensacao_termica': round(temperature + np.random.uniform(-2, 3), 1),
            'ponto_orvalho': round(temperature - (100 - humidity) * 0.2, 1),
            'mes': date.month,
            'estacao': season,
            'hora_dia': date.hour
        }
    
    def _apply_extreme_event(self, event_type: str, temp: float, humidity: float, 
                           pressure: float, precip: float, wind: float) -> Tuple:
        """Aplica modificações para eventos climáticos extremos"""
        
        if event_type == 'tempestade_eletrica':
            # Tempestade elétrica: baixa pressão, alta umidade, vento forte
            pressure -= np.random.uniform(10, 25)
            humidity = min(100, humidity + np.random.uniform(15, 30))
            wind = max(wind, np.random.uniform(40, 80))
            precip = max(precip, np.random.uniform(20, 60))
            
        elif event_type == 'vendaval':
            # Vendaval: pressão muito baixa, vento extremo
            pressure -= np.random.uniform(20, 40)
            wind = max(wind, np.random.uniform(60, 120))
            
        elif event_type == 'granizo':
            # Granizo: instabilidade atmosférica, diferencial térmico alto
            pressure -= np.random.uniform(15, 30)
            temp += np.random.uniform(5, 12)  # Aquecimento diurno intenso
            humidity = min(100, humidity + np.random.uniform(20, 35))
            wind = max(wind, np.random.uniform(30, 70))
            precip = max(precip, np.random.uniform(15, 45))
            
        elif event_type == 'alagamento':
            # Alagamento: chuva intensa e persistente
            precip = max(precip, np.random.uniform(50, 150))
            humidity = min(100, humidity + np.random.uniform(25, 40))
            pressure -= np.random.uniform(5, 15)
            wind = max(5, min(wind, 25))  # Vento mais fraco (sistema estacionário)
            
        return temp, humidity, pressure, precip, wind

class PropertyDataSimulator:
    """Simula dados de propriedades residenciais"""
    
    def __init__(self):
        self.property_types = ['casa', 'apartamento', 'sobrado', 'kitnet']
        self.construction_materials = ['alvenaria', 'madeira', 'mista']
        self.value_ranges = {
            'baixo': (50000, 150000),
            'medio': (150000, 400000),
            'alto': (400000, 800000),
            'premium': (800000, 2000000)
        }
    
    def simulate_property(self, cep: str) -> Dict:
        """Simula dados de uma propriedade"""
        
        # Tipo de residência baseado na região
        region = WeatherDataSimulator().get_region_by_cep(cep)
        
        if cep[:2] in ['01', '02', '03', '04']:  # Centro SP - mais apartamentos
            tipo_prob = {'apartamento': 0.6, 'casa': 0.2, 'sobrado': 0.1, 'kitnet': 0.1}
        elif region == 'sudeste':
            tipo_prob = {'casa': 0.5, 'apartamento': 0.3, 'sobrado': 0.15, 'kitnet': 0.05}
        else:
            tipo_prob = {'casa': 0.7, 'apartamento': 0.2, 'sobrado': 0.08, 'kitnet': 0.02}
        
        tipo_residencia = np.random.choice(
            list(tipo_prob.keys()), 
            p=list(tipo_prob.values())
        )
        
        # Ano de construção (distribuição realista)
        current_year = datetime.now().year
        if tipo_residencia == 'apartamento':
            ano_construcao = np.random.randint(1980, current_year - 1)
        else:
            ano_construcao = np.random.randint(1970, current_year - 1)
        
        idade_imovel = current_year - ano_construcao
        
        # Valor baseado na idade e tipo
        if idade_imovel > 30:
            faixa_valor = np.random.choice(['baixo', 'medio'], p=[0.7, 0.3])
        elif idade_imovel > 15:
            faixa_valor = np.random.choice(['baixo', 'medio', 'alto'], p=[0.3, 0.5, 0.2])
        else:
            faixa_valor = np.random.choice(['medio', 'alto', 'premium'], p=[0.4, 0.4, 0.2])
        
        valor_min, valor_max = self.value_ranges[faixa_valor]
        valor_segurado = np.random.uniform(valor_min, valor_max)
        
        # Características específicas
        material_construcao = np.random.choice(
            self.construction_materials,
            p=[0.8, 0.15, 0.05]  # Alvenaria mais comum
        )
        
        return {
            'tipo_residencia': tipo_residencia,
            'ano_construcao': ano_construcao,
            'idade_imovel': idade_imovel,
            'valor_segurado': round(valor_segurado, 2),
            'faixa_valor': faixa_valor,
            'material_construcao': material_construcao,
            'cep_prefixo': cep[:5],
            'regiao_metropolitana': self._is_metropolitan(cep),
            'risco_construcao': self._calculate_construction_risk(idade_imovel, tipo_residencia, faixa_valor)
        }
    
    def _is_metropolitan(self, cep: str) -> bool:
        """Verifica se é região metropolitana"""
        metro_prefixes = ['01', '02', '03', '04', '05', '06', '07', '08', '09',
                         '20', '21', '22', '23', '24', '25', '26', '27', '28',
                         '30', '31', '32', '40', '41', '42', '50', '51', '52',
                         '60', '61', '70', '71', '72', '80', '81', '82',
                         '90', '91', '92']
        return cep[:2] in metro_prefixes
    
    def _calculate_construction_risk(self, idade: int, tipo: str, faixa_valor: str) -> float:
        """Calcula risco de construção"""
        risk = 0.0
        
        # Risco por idade
        if idade > 30:
            risk += 0.3
        elif idade > 20:
            risk += 0.2
        elif idade > 10:
            risk += 0.1
        
        # Risco por tipo
        type_risk = {'casa': 0.2, 'sobrado': 0.3, 'apartamento': 0.1, 'kitnet': 0.15}
        risk += type_risk.get(tipo, 0.2)
        
        # Risco por valor (menor valor = maior risco)
        value_risk = {'baixo': 0.3, 'medio': 0.2, 'alto': 0.1, 'premium': 0.05}
        risk += value_risk.get(faixa_valor, 0.2)
        
        return min(risk, 1.0)

class ClaimsDataGenerator:
    """Gera dados sintéticos de sinistros para treinamento"""
    
    def __init__(self):
        self.weather_sim = WeatherDataSimulator()
        self.property_sim = PropertyDataSimulator()
        
        # Probabilidades de sinistro por cobertura e condições
        self.claim_probabilities = {
            'danos_eletricos': {
                'base_prob': 0.15,
                'weather_multipliers': {
                    'velocidade_vento': {40: 2.0, 60: 3.5, 80: 5.0},
                    'pressao_atmosferica': {1005: 1.5, 1000: 2.5, 995: 4.0},
                    'indice_uv': {7: 1.3, 9: 1.8, 11: 2.5}
                }
            },
            'vendaval': {
                'base_prob': 0.12,
                'weather_multipliers': {
                    'velocidade_vento': {50: 2.5, 70: 4.0, 90: 6.0},
                    'pressao_atmosferica': {1005: 1.8, 1000: 3.0, 995: 5.0}
                }
            },
            'granizo': {
                'base_prob': 0.08,
                'weather_multipliers': {
                    'temperatura_diferencial': {15: 2.0, 20: 3.5, 25: 5.5},
                    'umidade_relativa': {80: 1.5, 85: 2.0, 90: 2.8}
                }
            },
            'alagamento': {
                'base_prob': 0.18,
                'weather_multipliers': {
                    'precipitacao_mm': {30: 2.0, 50: 4.0, 80: 7.0},
                    'regiao_metropolitana': {True: 2.5}
                }
            }
        }
    
    def generate_training_dataset(self, coverage_type: str, n_samples: int = 5000) -> pd.DataFrame:
        """
        Gera dataset de treinamento para uma cobertura específica
        
        Args:
            coverage_type: Tipo de cobertura (danos_eletricos, vendaval, granizo, alagamento)
            n_samples: Número de amostras a gerar
        """
        
        print(f"🔄 Gerando {n_samples} amostras para {coverage_type}...")
        
        samples = []
        
        # Gerar CEPs brasileiros realistas
        ceps = self._generate_realistic_ceps(n_samples)
        
        # Gerar datas nos últimos 3 anos
        start_date = datetime.now() - timedelta(days=3*365)
        end_date = datetime.now()
        
        for i in range(n_samples):
            if i % 1000 == 0:
                print(f"  Progresso: {i}/{n_samples}")
            
            # Data aleatória
            random_date = start_date + timedelta(
                days=np.random.randint(0, (end_date - start_date).days),
                hours=np.random.randint(0, 24)
            )
            
            cep = ceps[i]
            
            # Decidir se será um caso de sinistro ou não
            # 60% dos casos são negativos (sem sinistro)
            is_claim = np.random.random() < 0.4
            
            # Se é sinistro, usar condições climáticas extremas
            extreme_event = None
            if is_claim:
                if coverage_type == 'danos_eletricos':
                    extreme_event = 'tempestade_eletrica'
                elif coverage_type == 'vendaval':
                    extreme_event = 'vendaval'
                elif coverage_type == 'granizo':
                    extreme_event = 'granizo'
                elif coverage_type == 'alagamento':
                    extreme_event = 'alagamento'
            
            # Gerar dados climáticos
            weather_data = self.weather_sim.simulate_weather_conditions(
                cep, random_date, extreme_event
            )
            
            # Gerar dados da propriedade
            property_data = self.property_sim.simulate_property(cep)
            
            # Calcular probabilidade de sinistro baseada nas condições
            claim_prob = self._calculate_claim_probability(
                coverage_type, weather_data, property_data
            )
            
            # Determinar se houve sinistro (com base na probabilidade)
            if not is_claim:
                # Para casos negativos, garantir que a probabilidade seja baixa
                claim_prob = min(claim_prob, 0.3)
                occurred = np.random.random() < claim_prob * 0.5  # Reduzir ainda mais
            else:
                # Para casos positivos, usar a probabilidade calculada
                occurred = np.random.random() < max(claim_prob, 0.6)
            
            # Combinar todos os dados
            sample = {
                **weather_data,
                **property_data,
                'sinistro_ocorreu': 1 if occurred else 0,
                'coverage_type': coverage_type,
                'data_sinistro': random_date.isoformat(),
                'claim_probability': claim_prob
            }
            
            # Adicionar features derivadas específicas
            sample.update(self._add_derived_features(weather_data, property_data))
            
            samples.append(sample)
        
        df = pd.DataFrame(samples)
        
        # Balancear dataset (aproximadamente 30-40% de sinistros)
        positive_samples = df[df['sinistro_ocorreu'] == 1]
        negative_samples = df[df['sinistro_ocorreu'] == 0]
        
        # Limitar para ter boa proporção
        target_positive = int(n_samples * 0.35)
        target_negative = n_samples - target_positive
        
        if len(positive_samples) > target_positive:
            positive_samples = positive_samples.sample(n=target_positive)
        if len(negative_samples) > target_negative:
            negative_samples = negative_samples.sample(n=target_negative)
        
        balanced_df = pd.concat([positive_samples, negative_samples]).sample(frac=1).reset_index(drop=True)
        
        print(f"✅ Dataset gerado: {len(balanced_df)} amostras")
        print(f"   Sinistros: {balanced_df['sinistro_ocorreu'].sum()} ({balanced_df['sinistro_ocorreu'].mean():.1%})")
        
        return balanced_df
    
    def _generate_realistic_ceps(self, n: int) -> List[str]:
        """Gera CEPs brasileiros realistas"""
        # Distribuição baseada na população real
        regions = {
            'sp': 0.4,  # São Paulo
            'rj': 0.15, # Rio de Janeiro
            'mg': 0.1,  # Minas Gerais
            'rs': 0.08, # Rio Grande do Sul
            'pr': 0.07, # Paraná
            'other': 0.2 # Outras regiões
        }
        
        ceps = []
        for _ in range(n):
            region = np.random.choice(list(regions.keys()), p=list(regions.values()))
            
            if region == 'sp':
                prefix = np.random.choice(['01', '02', '03', '04', '05', '06', '07', '08', '09'])
            elif region == 'rj':
                prefix = np.random.choice(['20', '21', '22', '23', '24', '25', '26', '27', '28'])
            elif region == 'mg':
                prefix = np.random.choice(['30', '31', '32', '33', '34', '35', '36', '37', '38', '39'])
            elif region == 'rs':
                prefix = np.random.choice(['90', '91', '92', '93', '94', '95', '96', '97', '98', '99'])
            elif region == 'pr':
                prefix = np.random.choice(['80', '81', '82', '83', '84', '85', '86', '87'])
            else:
                prefix = f"{np.random.randint(40, 89):02d}"
            
            suffix = f"{np.random.randint(0, 999999):06d}"
            ceps.append(prefix + suffix)
        
        return ceps
    
    def _calculate_claim_probability(self, coverage_type: str, weather_data: Dict, 
                                   property_data: Dict) -> float:
        """Calcula probabilidade de sinistro baseada nas condições"""
        
        if coverage_type not in self.claim_probabilities:
            return 0.1
        
        config = self.claim_probabilities[coverage_type]
        probability = config['base_prob']
        
        # Aplicar multiplicadores baseados no tempo
        for weather_feature, thresholds in config['weather_multipliers'].items():
            if weather_feature in weather_data:
                value = weather_data[weather_feature]
                for threshold, multiplier in sorted(thresholds.items()):
                    if isinstance(threshold, bool):
                        if threshold == value:
                            probability *= multiplier
                    elif value >= threshold:
                        probability *= multiplier
                        break
        
        # Considerar dados da propriedade
        if property_data.get('regiao_metropolitana') and coverage_type == 'alagamento':
            probability *= 2.0
        
        if property_data.get('idade_imovel', 0) > 25:
            probability *= 1.3
        
        return min(probability, 0.95)  # Máximo 95%
    
    def _add_derived_features(self, weather_data: Dict, property_data: Dict) -> Dict:
        """Adiciona features derivadas"""
        derived = {}
        
        # Diferencial térmico
        if 'temperatura_maxima' in weather_data and 'temperatura_minima' in weather_data:
            derived['temperatura_diferencial'] = weather_data['temperatura_maxima'] - weather_data['temperatura_minima']
        
        # Gradiente de pressão (simulado)
        if 'pressao_atmosferica' in weather_data:
            derived['gradiente_pressao_24h'] = np.random.normal(-2, 8)  # Variação típica
        
        # Precipitação acumulada (simulada)
        if 'precipitacao_mm' in weather_data:
            derived['precipitacao_24h'] = weather_data['precipitacao_mm'] * np.random.uniform(1.2, 3.0)
            derived['precipitacao_7dias'] = derived['precipitacao_24h'] * np.random.uniform(2.0, 7.0)
        
        return derived
    
    def save_dataset(self, df: pd.DataFrame, coverage_type: str, filepath: str = None):
        """Salva dataset em arquivo"""
        if filepath is None:
            os.makedirs('data/training', exist_ok=True)
            filepath = f'data/training/{coverage_type}_training_data.csv'
        
        df.to_csv(filepath, index=False)
        print(f"💾 Dataset salvo em: {filepath}")
        
        # Salvar também estatísticas
        stats_path = filepath.replace('.csv', '_stats.txt')
        with open(stats_path, 'w') as f:
            f.write(f"Dataset Statistics - {coverage_type}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total samples: {len(df)}\n")
            f.write(f"Positive samples (claims): {df['sinistro_ocorreu'].sum()}\n")
            f.write(f"Negative samples (no claims): {(df['sinistro_ocorreu'] == 0).sum()}\n")
            f.write(f"Claim rate: {df['sinistro_ocorreu'].mean():.1%}\n\n")
            f.write("Feature statistics:\n")
            f.write(df.describe().to_string())
        
        print(f"📊 Estatísticas salvas em: {stats_path}")

def generate_all_coverage_datasets(samples_per_coverage: int = 5000):
    """Gera datasets para todas as coberturas"""
    
    print("🚀 INICIANDO GERAÇÃO DE DATASETS DE TREINAMENTO\n")
    
    generator = ClaimsDataGenerator()
    coverages = ['danos_eletricos', 'vendaval', 'granizo', 'alagamento']
    
    for coverage in coverages:
        print(f"\n🔄 Processando {coverage}...")
        
        # Gerar dataset
        df = generator.generate_training_dataset(coverage, samples_per_coverage)
        
        # Salvar
        generator.save_dataset(df, coverage)
        
        print(f"✅ {coverage} concluído!\n")
    
    print("🎉 TODOS OS DATASETS GERADOS COM SUCESSO!")

if __name__ == "__main__":
    # Gerar datasets para todas as coberturas
    generate_all_coverage_datasets(3000)  # 3000 amostras por cobertura
