#!/usr/bin/env python3
"""
Modelo específico para predição de risco de Danos Elétricos.
Fatores principais: tempestades, raios, variações de tensão, surtos elétricos.
"""

from typing import Dict, List
import numpy as np
from .base_predictor import CoverageSpecificPredictor

class DanosEletricosPredictor(CoverageSpecificPredictor):
    """
    Modelo específico para predição de risco de Danos Elétricos.
    Fatores principais: tempestades, raios, variações de tensão.
    """
    
    def __init__(self):
        super().__init__("Danos Elétricos")
        
        # Features de importância específicas para danos elétricos
        self.feature_importance = {
            'velocidade_vento': 0.25,
            'indice_uv': 0.20,
            'pressao_atmosferica': 0.18,
            'umidade_relativa': 0.15,
            'idade_imovel': 0.12,
            'tipo_residencia': 0.10
        }
    
    def get_climate_features(self) -> List[str]:
        """Features climáticas relevantes para danos elétricos"""
        return [
            'velocidade_vento',
            'indice_uv',
            'pressao_atmosferica',
            'umidade_relativa',
            'temperatura_diferencial',
            'cobertura_nuvens',
            'precipitacao_mm',
            'mes',
            'estacao'
        ]
    
    def get_property_features(self) -> List[str]:
        """Features da propriedade relevantes para danos elétricos"""
        return [
            'idade_imovel',
            'tipo_residencia',
            'faixa_valor',
            'regiao_metropolitana',
            'risco_construcao'
        ]
    
    def calculate_risk_score(self, climate_data: Dict, property_data: Dict) -> float:
        """
        Calcula score de risco específico para danos elétricos
        Baseado em: tempestades, raios, instalações antigas
        """
        risk_score = 0.0
        
        # Risco climático
        
        # Velocidade do vento (tempestades)
        vento = climate_data.get('velocidade_vento', 0)
        if vento > 60:  # Vento muito forte (tempestade severa)
            risk_score += 0.4
        elif vento > 40:  # Vento forte
            risk_score += 0.25
        elif vento > 20:  # Vento moderado
            risk_score += 0.1
        
        # Índice UV (atividade atmosférica)
        uv = climate_data.get('indice_uv', 0)
        if uv > 8:  # UV muito alto (alta atividade atmosférica)
            risk_score += 0.2
        elif uv > 6:
            risk_score += 0.1
        
        # Pressão atmosférica (sistemas de baixa pressão = tempestades)
        pressao = climate_data.get('pressao_atmosferica', 1013.25)
        if pressao < 1000:  # Baixa pressão severa
            risk_score += 0.3
        elif pressao < 1010:  # Baixa pressão moderada
            risk_score += 0.15
        
        # Umidade alta + temperatura = instabilidade
        umidade = climate_data.get('umidade_relativa', 0)
        if umidade > 85:
            risk_score += 0.15
        elif umidade > 70:
            risk_score += 0.1
        
        # Cobertura de nuvens (tempestades)
        nuvens = climate_data.get('cobertura_nuvens', 0)
        if nuvens > 80:
            risk_score += 0.1
        
        # Precipitação (tempestades com raios)
        precipitacao = climate_data.get('precipitacao_mm', 0)
        if precipitacao > 10:  # Chuva forte
            risk_score += 0.2
        elif precipitacao > 5:  # Chuva moderada
            risk_score += 0.1
        
        # Sazonalidade (verão = mais tempestades)
        estacao = climate_data.get('estacao', 'verao')
        if estacao == 'verao':
            risk_score += 0.15
        elif estacao == 'primavera':
            risk_score += 0.1
        
        # Risco da propriedade
        
        # Idade do imóvel (instalações antigas)
        idade = property_data.get('idade_imovel', 0)
        if idade > 30:
            risk_score += 0.25  # Instalações muito antigas
        elif idade > 20:
            risk_score += 0.15
        elif idade > 10:
            risk_score += 0.1
        
        # Tipo de residência
        tipo = property_data.get('tipo_residencia', 'casa')
        if tipo == 'sobrado':
            risk_score += 0.15  # Mais exposição a raios
        elif tipo == 'casa':
            risk_score += 0.1
        elif tipo == 'apartamento':
            risk_score += 0.05  # Menor exposição
        
        # Faixa de valor (qualidade da instalação)
        faixa_valor = property_data.get('faixa_valor', 'medio')
        if faixa_valor == 'baixo':
            risk_score += 0.2  # Instalações de menor qualidade
        elif faixa_valor == 'medio':
            risk_score += 0.1
        elif faixa_valor == 'premium':
            risk_score -= 0.05  # Instalações de melhor qualidade
        
        # Região metropolitana (mais instabilidade na rede)
        if property_data.get('regiao_metropolitana', False):
            risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    def get_specific_recommendations(self, risk_level: str, main_factors: List[Dict]) -> List[str]:
        """
        Recomendações específicas para danos elétricos
        """
        recommendations = []
        
        if risk_level in ['alto', 'medio']:
            recommendations.extend([
                "⚡ Instalar protetor contra surtos elétricos",
                "🔌 Verificar condições da instalação elétrica",
                "⛈️ Desligar equipamentos durante tempestades"
            ])
        
        # Recomendações baseadas nos fatores principais
        for factor in main_factors[:3]:
            feature = factor['feature']
            
            if feature == 'velocidade_vento' and factor['value'] > 40:
                recommendations.append("💨 Alto risco de tempestade - proteger equipamentos eletrônicos")
            elif feature == 'idade_imovel' and factor['value'] > 20:
                recommendations.append("🏠 Considerar atualização da instalação elétrica antiga")
            elif feature == 'pressao_atmosferica' and factor['value'] < 1010:
                recommendations.append("🌩️ Sistema de baixa pressão - risco de tempestades elétricas")
        
        return list(set(recommendations))  # Remover duplicatas
    
    def calculate_seasonal_adjustment(self, month: int) -> float:
        """
        Ajuste sazonal para danos elétricos
        Verão = mais tempestades com raios
        """
        seasonal_factors = {
            12: 1.3, 1: 1.4, 2: 1.3,  # Verão - pico de tempestades
            3: 1.1, 4: 0.9, 5: 0.8,   # Outono - diminuição
            6: 0.7, 7: 0.6, 8: 0.7,   # Inverno - menor risco
            9: 0.9, 10: 1.1, 11: 1.2  # Primavera - aumento gradual
        }
        
        return seasonal_factors.get(month, 1.0)
