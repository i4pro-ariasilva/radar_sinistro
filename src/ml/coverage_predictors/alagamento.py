#!/usr/bin/env python3
"""
Modelo específico para predição de risco de Alagamento.
Fatores principais: precipitação, topografia, drenagem urbana.
"""

from typing import Dict, List
import numpy as np
from .base_predictor import CoverageSpecificPredictor

class AlagamentoPredictor(CoverageSpecificPredictor):
    """
    Modelo específico para predição de risco de Alagamento.
    Fatores principais: precipitação, topografia, drenagem urbana.
    """
    
    def __init__(self):
        super().__init__("Alagamento")
        
        # Features de importância específicas para alagamento
        self.feature_importance = {
            'precipitacao_mm': 0.40,
            'regiao_metropolitana': 0.20,
            'umidade_relativa': 0.15,
            'pressao_atmosferica': 0.10,
            'tipo_residencia': 0.10,
            'faixa_valor': 0.05
        }
    
    def get_climate_features(self) -> List[str]:
        """Features climáticas relevantes para alagamento"""
        return [
            'precipitacao_mm',
            'umidade_relativa',
            'pressao_atmosferica',
            'temperatura_atual',
            'cobertura_nuvens',
            'velocidade_vento',
            'mes',
            'estacao'
        ]
    
    def get_property_features(self) -> List[str]:
        """Features da propriedade relevantes para alagamento"""
        return [
            'regiao_metropolitana',
            'tipo_residencia',
            'faixa_valor',
            'cep_prefixo',
            'risco_construcao'
        ]
    
    def calculate_risk_score(self, climate_data: Dict, property_data: Dict) -> float:
        """
        Calcula score de risco específico para alagamento
        Baseado em: precipitação, drenagem urbana, topografia
        """
        risk_score = 0.0
        
        # Risco climático
        
        # Precipitação (principal fator)
        precipitacao = climate_data.get('precipitacao_mm', 0)
        if precipitacao > 50:  # Chuva muito forte
            risk_score += 0.6
        elif precipitacao > 25:  # Chuva forte
            risk_score += 0.4
        elif precipitacao > 10:  # Chuva moderada
            risk_score += 0.2
        elif precipitacao > 5:  # Chuva leve
            risk_score += 0.1
        
        # Umidade alta (persistência da chuva)
        umidade = climate_data.get('umidade_relativa', 0)
        if umidade > 90:  # Umidade muito alta
            risk_score += 0.2
        elif umidade > 80:
            risk_score += 0.15
        elif umidade > 70:
            risk_score += 0.1
        
        # Pressão atmosférica (sistemas estacionários)
        pressao = climate_data.get('pressao_atmosferica', 1013.25)
        if pressao < 1005:  # Pressão muito baixa (sistemas persistentes)
            risk_score += 0.2
        elif pressao < 1010:
            risk_score += 0.1
        
        # Cobertura de nuvens (sistemas nublados persistentes)
        nuvens = climate_data.get('cobertura_nuvens', 0)
        if nuvens > 85:  # Muito nublado
            risk_score += 0.15
        elif nuvens > 70:
            risk_score += 0.1
        
        # Temperatura (chuvas quentes = mais intensas)
        temperatura = climate_data.get('temperatura_atual', 25)
        if temperatura > 25:  # Chuva quente
            risk_score += 0.1
        
        # Velocidade do vento baixa (sistemas estacionários)
        vento = climate_data.get('velocidade_vento', 10)
        if vento < 5:  # Vento fraco (sistema estacionário)
            risk_score += 0.1
        
        # Sazonalidade (verão = chuvas intensas)
        estacao = climate_data.get('estacao', 'verao')
        mes = climate_data.get('mes', 6)
        
        if estacao == 'verao':
            risk_score += 0.2  # Chuvas de verão
        elif estacao == 'primavera' and mes in [10, 11]:
            risk_score += 0.15  # Chuvas de primavera
        elif estacao == 'outono' and mes in [3, 4]:
            risk_score += 0.1   # Chuvas de outono
        
        # Risco da propriedade e localização
        
        # Região metropolitana (drenagem inadequada)
        if property_data.get('regiao_metropolitana', False):
            risk_score += 0.25  # Fator crítico para alagamento
        
        # Tipo de residência (altura/exposição)
        tipo = property_data.get('tipo_residencia', 'casa')
        if tipo == 'casa':
            risk_score += 0.15  # Nível do solo
        elif tipo == 'sobrado':
            risk_score += 0.1   # Primeiro andar pode alagar
        elif tipo == 'kitnet':
            risk_score += 0.12  # Geralmente térreo
        elif tipo == 'apartamento':
            risk_score += 0.02  # Menor risco (altura)
        
        # Análise por CEP (regiões conhecidas de alagamento)
        cep_prefixo = property_data.get('cep_prefixo', '00000')
        risk_score += self._get_flood_risk_by_cep(cep_prefixo)
        
        # Faixa de valor (infraestrutura do bairro)
        faixa_valor = property_data.get('faixa_valor', 'medio')
        if faixa_valor == 'baixo':
            risk_score += 0.15  # Bairros com drenagem deficiente
        elif faixa_valor == 'medio':
            risk_score += 0.1
        elif faixa_valor == 'alto':
            risk_score += 0.05
        elif faixa_valor == 'premium':
            risk_score -= 0.05  # Bairros com melhor infraestrutura
        
        return min(risk_score, 1.0)
    
    def _get_flood_risk_by_cep(self, cep_prefixo: str) -> float:
        """
        Retorna risco de alagamento baseado no CEP (regiões conhecidas)
        """
        # Regiões com histórico de alagamento no Brasil
        high_risk_areas = {
            # São Paulo
            '01': 0.2, '02': 0.15, '03': 0.25, '04': 0.2, '05': 0.15,
            '06': 0.1, '07': 0.15, '08': 0.25, '09': 0.2,
            
            # Rio de Janeiro  
            '20': 0.3, '21': 0.25, '22': 0.2, '23': 0.25, '24': 0.15,
            '25': 0.1, '26': 0.15, '27': 0.1, '28': 0.05,
            
            # Belo Horizonte
            '30': 0.2, '31': 0.15, '32': 0.1,
            
            # Salvador
            '40': 0.2, '41': 0.15, '42': 0.1,
            
            # Recife
            '50': 0.25, '51': 0.2, '52': 0.15,
            
            # Fortaleza
            '60': 0.2, '61': 0.15,
            
            # Brasília
            '70': 0.1, '71': 0.05, '72': 0.05,
            
            # Curitiba
            '80': 0.15, '81': 0.1, '82': 0.1,
            
            # Porto Alegre
            '90': 0.2, '91': 0.15, '92': 0.1
        }
        
        return high_risk_areas.get(cep_prefixo[:2], 0.05)  # Risco base baixo
    
    def get_specific_recommendations(self, risk_level: str, main_factors: List[Dict]) -> List[str]:
        """
        Recomendações específicas para alagamento
        """
        recommendations = []
        
        if risk_level in ['alto', 'medio']:
            recommendations.extend([
                "🌊 Verificar sistema de drenagem da propriedade",
                "🚧 Manter ralos e bueiros desobstruídos",
                "📦 Elevar objetos de valor do nível do solo",
                "🚗 Evitar áreas baixas com veículos"
            ])
        
        # Recomendações baseadas nos fatores principais
        for factor in main_factors[:3]:
            feature = factor['feature']
            
            if feature == 'precipitacao_mm' and factor['value'] > 25:
                recommendations.append("☔ Chuva intensa - risco elevado de alagamento rápido")
            elif feature == 'regiao_metropolitana' and factor['value']:
                recommendations.append("🏙️ Região metropolitana - atenção à drenagem urbana")
            elif feature == 'umidade_relativa' and factor['value'] > 85:
                recommendations.append("💧 Umidade alta - chuvas podem persistir")
            elif feature == 'tipo_residencia' and factor['value'] in ['casa', 'kitnet']:
                recommendations.append("🏠 Imóvel térreo - maior vulnerabilidade a alagamentos")
        
        return list(set(recommendations))  # Remover duplicatas
    
    def calculate_seasonal_adjustment(self, month: int) -> float:
        """
        Ajuste sazonal para alagamento
        Verão = pico de chuvas intensas
        """
        seasonal_factors = {
            12: 1.4, 1: 1.5, 2: 1.3,   # Verão - pico de chuvas
            3: 1.2, 4: 1.0, 5: 0.8,    # Outono - diminuição gradual
            6: 0.6, 7: 0.5, 8: 0.6,    # Inverno - período seco
            9: 0.8, 10: 1.0, 11: 1.2   # Primavera - aumento gradual
        }
        
        return seasonal_factors.get(month, 1.0)
    
    def calculate_drainage_capacity_risk(self, precipitation: float, urban_area: bool) -> float:
        """
        Calcula risco baseado na capacidade de drenagem vs precipitação
        """
        # Capacidade de drenagem estimada (mm/h)
        if urban_area:
            drainage_capacity = 20  # Sistemas urbanos limitados
        else:
            drainage_capacity = 35  # Drenagem natural melhor
        
        # Risco baseado na razão precipitação/capacidade
        if precipitation > drainage_capacity * 2:
            return 0.8  # Sistema sobrecarregado
        elif precipitation > drainage_capacity:
            return 0.6  # Sistema no limite
        elif precipitation > drainage_capacity * 0.7:
            return 0.3  # Sistema sob pressão
        else:
            return 0.1  # Sistema adequado
    
    def get_flood_duration_estimate(self, risk_score: float, urban_area: bool) -> str:
        """
        Estima duração potencial do alagamento
        """
        if risk_score < 0.3:
            return "Rápida drenagem (< 30 min)"
        elif risk_score < 0.6:
            if urban_area:
                return "Drenagem lenta (1-3 horas)"
            else:
                return "Drenagem moderada (30-60 min)"
        else:
            if urban_area:
                return "Drenagem muito lenta (> 6 horas)"
            else:
                return "Drenagem lenta (2-4 horas)"