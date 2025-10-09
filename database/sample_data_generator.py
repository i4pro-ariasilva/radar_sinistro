"""
Gerador de dados de exemplo para o Sistema de Radar de Sinistro
"""

import random
import csv
from datetime import datetime, timedelta
from typing import List
import json

# Lista de CEPs reais do Brasil para exemplo com coordenadas mais precisas
CEPS_EXEMPLO = [
    "01310-100", "20040-020", "30140-071", "40070-110", "50030-230",
    "60115-221", "70040-010", "80010-120", "90010-150", "13013-050",
    "14020-230", "15015-110", "16010-082", "17012-020", "18035-430",
    "19020-200", "21040-361", "22071-101", "23085-020", "24020-040",
    "25071-160", "26020-053", "27213-415", "28035-042", "29055-620"
]

# Coordenadas de cidades brasileiras seguras (longe do mar)
COORDENADAS_CIDADES_BRASIL = [
    # São Paulo e região
    (-23.5505, -46.6333, "São Paulo - SP"),
    (-23.6821, -46.8755, "Carapicuíba - SP"),
    (-23.4273, -46.7453, "Guarulhos - SP"),
    (-23.6629, -46.5383, "Santo André - SP"),
    
    # Rio de Janeiro (interior)
    (-22.7519, -43.4654, "Nova Iguaçu - RJ"),
    (-22.8809, -43.2096, "Niterói - RJ"),
    (-22.5207, -43.1808, "Duque de Caxias - RJ"),
    
    # Minas Gerais
    (-19.9167, -43.9345, "Belo Horizonte - MG"),
    (-21.7594, -43.3486, "Juiz de Fora - MG"),
    (-19.7417, -47.9297, "Uberlândia - MG"),
    (-20.7596, -42.8735, "Governador Valadares - MG"),
    
    # Bahia (interior)
    (-12.9714, -38.5014, "Salvador - BA"),
    (-14.8615, -40.8442, "Vitória da Conquista - BA"),
    (-15.5989, -56.0949, "Cáceres - MT"),
    
    # Pernambuco
    (-8.0476, -34.8770, "Recife - PE"),
    (-8.2819, -35.9744, "Caruaru - PE"),
    
    # Ceará
    (-3.7327, -38.5267, "Fortaleza - CE"),
    (-7.2306, -39.3136, "Juazeiro do Norte - CE"),
    
    # Distrito Federal
    (-15.7801, -47.9292, "Brasília - DF"),
    (-15.8331, -48.0429, "Águas Claras - DF"),
    
    # Paraná
    (-25.4372, -49.2697, "Curitiba - PR"),
    (-23.3045, -51.1696, "Maringá - PR"),
    (-25.0916, -50.1668, "Ponta Grossa - PR"),
    
    # Rio Grande do Sul
    (-30.0346, -51.2177, "Porto Alegre - RS"),
    (-29.1678, -51.1794, "Caxias do Sul - RS"),
    (-28.2578, -52.4095, "Passo Fundo - RS"),
    
    # Santa Catarina
    (-27.5954, -48.5480, "Florianópolis - SC"),
    (-26.9194, -49.0661, "Blumenau - SC"),
    (-27.0965, -52.6181, "Chapecó - SC"),
    
    # Goiás
    (-16.6869, -49.2648, "Goiânia - GO"),
    (-16.4729, -49.1547, "Aparecida de Goiânia - GO"),
    
    # Espírito Santo
    (-20.3155, -40.3128, "Vitória - ES"),
    (-19.6326, -40.4034, "Linhares - ES"),
    
    # Mato Grosso
    (-15.6014, -56.0979, "Cuiabá - MT"),
    (-12.6819, -60.1187, "Vilhena - RO"),
    
    # Amazonas (cidades principais)
    (-3.1190, -60.0217, "Manaus - AM"),
    (-2.5307, -44.3068, "São Luís - MA"),
]

TIPOS_RESIDENCIA = ["casa", "apartamento", "sobrado"]

TIPOS_SINISTRO = [
    "Enchente", "Vendaval", "Granizo", "Queimadas", "Alagamento", 
    "Destelhamento", "Infiltração", "Queda de árvore", "Tempestade", 
    "Tornado", "Raio", "Seca"
]

CAUSAS_SINISTRO = [
    "Chuva intensa", "Vento forte", "Tempestade", "Granizo severo",
    "Alagamento urbano", "Transbordamento de rio", "Temporal",
    "Incêndio florestal", "Queimada descontrolada", "Seca prolongada",
    "Atividade elétrica", "Fenômeno climático extremo"
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
            
            # Coordenadas próximas à apólice (mesmo local com pequena variação)
            # Variação de até ~500m para simular endereços próximos
            lat_variation = random.uniform(-0.005, 0.005)  # ~500m
            lon_variation = random.uniform(-0.005, 0.005)  # ~500m
            
            sinistro_lat = policy['latitude'] + lat_variation
            sinistro_lon = policy['longitude'] + lon_variation
            
            # Condições climáticas do dia
            weather_conditions = self._generate_weather_conditions()
            
            claim = {
                'numero_apolice': policy['numero_apolice'],
                'data_sinistro': claim_date.strftime('%Y-%m-%d %H:%M:%S'),
                'tipo_sinistro': claim_type,
                'valor_prejuizo': damage_value,
                'causa': cause,
                'latitude': round(sinistro_lat, 6),
                'longitude': round(sinistro_lon, 6),
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
        """Retorna coordenadas terrestres seguras para CEPs brasileiros"""
        
        # Seleciona uma coordenada aleatória das cidades brasileiras
        lat_base, lon_base, cidade = random.choice(COORDENADAS_CIDADES_BRASIL)
        
        # Adiciona pequena variação para simular diferentes bairros
        # Máximo ~5km de variação (aproximadamente 0.05 graus)
        lat_variation = random.uniform(-0.05, 0.05)
        lon_variation = random.uniform(-0.05, 0.05)
        
        final_lat = lat_base + lat_variation
        final_lon = lon_base + lon_variation
        
        # Garantir que esteja dentro dos limites do Brasil
        final_lat = max(-33.5, min(5.2, final_lat))  # Limites do Brasil
        final_lon = max(-74.0, min(-28.8, final_lon))  # Limites do Brasil
        
        return (round(final_lat, 6), round(final_lon, 6))
    
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