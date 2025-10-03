"""
Gerador de dados de exemplo para o Sistema de Radar de Sinistro
"""

import random
import csv
from datetime import datetime, timedelta
from typing import List
import json

# Lista de CEPs reais do Brasil para exemplo
CEPS_EXEMPLO = [
    "01310-100", "20040-020", "30140-071", "40070-110", "50030-230",
    "60115-221", "70040-010", "80010-120", "90010-150", "13013-050",
    "14020-230", "15015-110", "16010-082", "17012-020", "18035-430",
    "19020-200", "21040-361", "22071-101", "23085-020", "24020-040",
    "25071-160", "26020-053", "27213-415", "28035-042", "29055-620"
]

TIPOS_RESIDENCIA = ["casa", "apartamento", "sobrado"]

TIPOS_SINISTRO = [
    "Enchente", "Vendaval", "Granizo", "Alagamento", 
    "Destelhamento", "Infiltração", "Queda de árvore"
]

CAUSAS_SINISTRO = [
    "Chuva intensa", "Vento forte", "Tempestade", "Granizo",
    "Alagamento urbano", "Transbordamento de rio", "Temporal"
]


class SampleDataGenerator:
    """Classe para gerar dados de exemplo"""
    
    def __init__(self):
        self.used_policy_numbers = set()
    
    def generate_sample_policies(self, n: int = 1000) -> List[dict]:
        """
        Gera dados de exemplo para apólices
        
        Args:
            n: Número de apólices para gerar
            
        Returns:
            Lista de dicionários com dados das apólices
        """
        policies = []
        
        for i in range(n):
            # Gera número único de apólice
            while True:
                policy_number = f"POL{random.randint(100000, 999999)}"
                if policy_number not in self.used_policy_numbers:
                    self.used_policy_numbers.add(policy_number)
                    break
            
            # Data de contratação entre 1 ano atrás e hoje
            start_date = datetime.now() - timedelta(days=365)
            end_date = datetime.now()
            contract_date = self._random_date(start_date, end_date)
            
            # Coordenadas aproximadas para CEPs brasileiros
            cep = random.choice(CEPS_EXEMPLO)
            lat, lon = self._get_approximate_coordinates(cep)
            
            policy = {
                'numero_apolice': policy_number,
                'cep': cep,
                'latitude': lat,
                'longitude': lon,
                'tipo_residencia': random.choice(TIPOS_RESIDENCIA),
                'valor_segurado': round(random.uniform(150000, 800000), 2),
                'data_contratacao': contract_date.strftime('%Y-%m-%d'),
                'ativa': random.choice([True] * 9 + [False])  # 90% ativas
            }
            
            policies.append(policy)
        
        return policies
    
    def generate_sample_claims(self, policies: List[dict], n: int = 200) -> List[dict]:
        """
        Gera sinistros históricos baseados nas apólices
        
        Args:
            policies: Lista de apólices para gerar sinistros
            n: Número de sinistros para gerar
            
        Returns:
            Lista de dicionários com dados dos sinistros
        """
        claims = []
        
        # Pega apenas apólices ativas
        active_policies = [p for p in policies if p['ativa']]
        
        for i in range(n):
            # Seleciona uma apólice aleatória
            policy = random.choice(active_policies)
            
            # Data do sinistro após a contratação
            contract_date = datetime.strptime(policy['data_contratacao'], '%Y-%m-%d')
            max_date = min(datetime.now(), contract_date + timedelta(days=300))
            claim_date = self._random_date(contract_date, max_date)
            
            # Tipo de sinistro e causa relacionada
            claim_type = random.choice(TIPOS_SINISTRO)
            cause = random.choice(CAUSAS_SINISTRO)
            
            # Valor do prejuízo baseado no valor segurado
            max_damage = policy['valor_segurado'] * 0.8  # Máximo 80% do valor segurado
            damage_value = round(random.uniform(5000, max_damage), 2)
            
            # Condições climáticas do dia
            weather_conditions = self._generate_weather_conditions()
            
            claim = {
                'numero_apolice': policy['numero_apolice'],
                'data_sinistro': claim_date.strftime('%Y-%m-%d %H:%M:%S'),
                'tipo_sinistro': claim_type,
                'valor_prejuizo': damage_value,
                'causa': cause,
                'condicoes_climaticas': json.dumps(weather_conditions),
                'precipitacao_mm': weather_conditions.get('precipitacao_mm'),
                'vento_kmh': weather_conditions.get('vento_kmh'),
                'temperatura_c': weather_conditions.get('temperatura_c')
            }
            
            claims.append(claim)
        
        return claims
    
    def generate_climate_data(self, n: int = 500) -> List[dict]:
        """
        Gera dados climáticos de exemplo
        
        Args:
            n: Número de registros climáticos
            
        Returns:
            Lista de dados climáticos
        """
        climate_data = []
        
        for i in range(n):
            # Data nos últimos 30 dias
            start_date = datetime.now() - timedelta(days=30)
            data_date = self._random_date(start_date, datetime.now())
            
            # Coordenadas aleatórias no Brasil
            cep = random.choice(CEPS_EXEMPLO)
            lat, lon = self._get_approximate_coordinates(cep)
            
            # Adiciona pequena variação nas coordenadas
            lat += random.uniform(-0.01, 0.01)
            lon += random.uniform(-0.01, 0.01)
            
            weather = self._generate_weather_conditions()
            
            data = {
                'latitude': round(lat, 6),
                'longitude': round(lon, 6),
                'data_coleta': data_date.strftime('%Y-%m-%d %H:%M:%S'),
                'temperatura_c': weather['temperatura_c'],
                'precipitacao_mm': weather['precipitacao_mm'],
                'vento_kmh': weather['vento_kmh'],
                'umidade_percent': random.randint(40, 95),
                'pressao_hpa': round(random.uniform(1000, 1025), 1),
                'fonte': random.choice(['OpenWeather', 'INMET', 'ClimaAPI'])
            }
            
            climate_data.append(data)
        
        return climate_data
    
    def save_to_csv(self, data: List[dict], filename: str):
        """Salva dados em arquivo CSV"""
        if not data:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    def _random_date(self, start: datetime, end: datetime) -> datetime:
        """Gera data aleatória entre start e end"""
        delta = end - start
        random_days = random.randint(0, delta.days)
        random_seconds = random.randint(0, 86400)  # Segundos em um dia
        return start + timedelta(days=random_days, seconds=random_seconds)
    
    def _get_approximate_coordinates(self, cep: str) -> tuple:
        """Retorna coordenadas aproximadas para CEPs brasileiros"""
        # Mapeamento básico de CEP para coordenadas aproximadas
        cep_coords = {
            "01310-100": (-23.5505, -46.6333),  # São Paulo - SP
            "20040-020": (-22.9068, -43.1729),  # Rio de Janeiro - RJ
            "30140-071": (-19.9167, -43.9345),  # Belo Horizonte - MG
            "40070-110": (-12.9714, -38.5014),  # Salvador - BA
            "50030-230": (-8.0476, -34.8770),   # Recife - PE
            "60115-221": (-3.7327, -38.5267),   # Fortaleza - CE
            "70040-010": (-15.7801, -47.9292),  # Brasília - DF
            "80010-120": (-25.4372, -49.2697),  # Curitiba - PR
            "90010-150": (-30.0346, -51.2177),  # Porto Alegre - RS
        }
        
        if cep in cep_coords:
            return cep_coords[cep]
        
        # Se CEP não mapeado, usa coordenadas do Brasil com variação
        return (
            random.uniform(-33.0, 5.0),   # Latitude Brasil
            random.uniform(-74.0, -32.0)  # Longitude Brasil
        )
    
    def _generate_weather_conditions(self) -> dict:
        """Gera condições climáticas realistas"""
        # Temperatura baseada em distribuição realista
        temp = round(random.normalvariate(25, 8), 1)
        temp = max(5, min(45, temp))  # Limita entre 5°C e 45°C
        
        # Precipitação com distribuição assimétrica (mais dias secos)
        if random.random() < 0.7:  # 70% chance de não chover
            precip = 0
        else:
            precip = round(random.expovariate(0.1), 1)  # Distribuição exponencial
            precip = min(precip, 150)  # Máximo 150mm
        
        # Vento correlacionado com precipitação
        if precip > 20:
            vento = round(random.uniform(15, 60), 1)  # Vento forte com chuva
        else:
            vento = round(random.uniform(2, 25), 1)   # Vento normal
        
        return {
            'temperatura_c': temp,
            'precipitacao_mm': precip,
            'vento_kmh': vento
        }


def generate_all_sample_data():
    """Gera todos os dados de exemplo e salva em CSVs"""
    generator = SampleDataGenerator()
    
    print("Gerando dados de exemplo...")
    
    # Gera apólices
    print("- Gerando apólices...")
    policies = generator.generate_sample_policies(1000)
    generator.save_to_csv(policies, 'data/sample/sample_policies.csv')
    
    # Gera sinistros baseados nas apólices
    print("- Gerando sinistros...")
    claims = generator.generate_sample_claims(policies, 200)
    generator.save_to_csv(claims, 'data/sample/sample_claims.csv')
    
    # Gera dados climáticos
    print("- Gerando dados climáticos...")
    climate = generator.generate_climate_data(500)
    generator.save_to_csv(climate, 'data/sample/sample_climate_data.csv')
    
    print("Dados de exemplo gerados com sucesso!")
    print(f"- {len(policies)} apólices")
    print(f"- {len(claims)} sinistros")
    print(f"- {len(climate)} registros climáticos")


if __name__ == "__main__":
    generate_all_sample_data()