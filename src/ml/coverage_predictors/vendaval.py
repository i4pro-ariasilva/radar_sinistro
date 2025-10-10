#!/usr/bin/env python3
"""
Modelo específico para predição de risco de Vendaval.
Fatores principais: velocidade do vento, pressão atmosférica, sistemas meteorológicos.
"""

from typing import Dict, List
import numpy as np
from .base_predictor import CoverageSpecificPredictor

class VendavalPredictor(CoverageSpecificPredictor):
    """
    Modelo específico para predição de risco de Vendaval.
    Fatores principais: velocidade do vento, pressão atmosférica, sistemas meteorológicos.
    """
    
    def __init__(self):
        super().__init__("Vendaval")
        
        # Features de importância específicas para vendaval
        self.feature_importance = {
            'velocidade_vento': 0.35,
            'pressao_atmosferica': 0.25,
            'temperatura_diferencial': 0.15,
            'umidade_relativa': 0.10,
            'tipo_residencia': 0.10,
            'regiao_metropolitana': 0.05
        }
    
    def get_climate_features(self) -> List[str]:
        """Features climáticas relevantes para vendaval"""
        return [
            'velocidade_vento',
            'pressao_atmosferica',
            'temperatura_diferencial',
            'umidade_relativa',
            'direcao_vento',
            'cobertura_nuvens',
            'visibilidade',
            'mes',
            'estacao'
        ]
    
    def get_property_features(self) -> List[str]:
        """Features da propriedade relevantes para vendaval"""
        return [
            'tipo_residencia',
            'regiao_metropolitana',
            'faixa_valor',
            'risco_construcao',
            'idade_imovel'
        ]
    
    def calculate_risk_score(self, climate_data: Dict, property_data: Dict) -> float:
        """
        Calcula score de risco específico para vendaval
        Baseado em: velocidade do vento, gradientes de pressão, instabilidade atmosférica
        """
        risk_score = 0.0
        
        # Risco climático
        
        # Velocidade do vento (principal fator)
        vento = climate_data.get('velocidade_vento', 0)
        if vento > 80:  # Vendaval destrutivo
            risk_score += 0.6
        elif vento > 60:  # Vendaval forte
            risk_score += 0.45
        elif vento > 40:  # Vento muito forte
            risk_score += 0.3
        elif vento > 25:  # Vento forte
            risk_score += 0.15
        elif vento > 15:  # Vento moderado
            risk_score += 0.05
        
        # Pressão atmosférica (sistemas de baixa pressão = ventos fortes)
        pressao = climate_data.get('pressao_atmosferica', 1013.25)
        if pressao < 990:  # Pressão muito baixa (ciclone/tempestade severa)
            risk_score += 0.4
        elif pressao < 1000:  # Pressão baixa severa
            risk_score += 0.3
        elif pressao < 1010:  # Pressão baixa
            risk_score += 0.15
        
        # Gradiente de temperatura (instabilidade = ventos)
        temp_max = climate_data.get('temperatura_maxima', 25)
        temp_min = climate_data.get('temperatura_minima', 15)
        temp_diff = temp_max - temp_min
        if temp_diff > 15:  # Grande variação térmica
            risk_score += 0.2
        elif temp_diff > 10:
            risk_score += 0.1
        
        # Umidade (sistemas úmidos = mais energia)
        umidade = climate_data.get('umidade_relativa', 0)
        if umidade > 85:
            risk_score += 0.15
        elif umidade > 70:
            risk_score += 0.1
        
        # Cobertura de nuvens (sistemas meteorológicos)
        nuvens = climate_data.get('cobertura_nuvens', 0)
        if nuvens > 80:  # Sistemas nublados
            risk_score += 0.1
        
        # Visibilidade (tempestades reduzem visibilidade)
        visibilidade = climate_data.get('visibilidade', 10000)
        if visibilidade < 1000:  # Visibilidade muito baixa
            risk_score += 0.15
        elif visibilidade < 5000:  # Visibilidade baixa
            risk_score += 0.1
        
        # Sazonalidade (inverno/primavera = mais frentes frias)
        estacao = climate_data.get('estacao', 'verao')
        if estacao == 'inverno':
            risk_score += 0.15  # Frentes frias
        elif estacao == 'primavera':
            risk_score += 0.1   # Transição sazonal
        elif estacao == 'outono':
            risk_score += 0.05
        
        # Risco da propriedade
        
        # Tipo de residência (exposição ao vento)
        tipo = property_data.get('tipo_residencia', 'casa')
        if tipo == 'sobrado':
            risk_score += 0.2   # Maior altura = mais exposição
        elif tipo == 'casa':
            risk_score += 0.15  # Exposição moderada
        elif tipo == 'apartamento':
            risk_score += 0.05  # Menor exposição (estrutura robusta)
        
        # Região metropolitana (efeito ilha de calor = ventos)
        if property_data.get('regiao_metropolitana', False):
            risk_score += 0.1
        
        # Faixa de valor (qualidade construtiva)
        faixa_valor = property_data.get('faixa_valor', 'medio')
        if faixa_valor == 'baixo':
            risk_score += 0.15  # Construção menos resistente
        elif faixa_valor == 'medio':
            risk_score += 0.1
        elif faixa_valor == 'premium':
            risk_score -= 0.05  # Construção mais resistente
        
        # Risco de construção geral
        risco_construcao = property_data.get('risco_construcao', 0.5)
        risk_score += risco_construcao * 0.1
        
        return min(risk_score, 1.0)
    
    def get_specific_recommendations(self, risk_level: str, main_factors: List[Dict]) -> List[str]:
        """
        Recomendações específicas para vendaval
        """
        recommendations = []
        
        if risk_level in ['alto', 'medio']:
            recommendations.extend([
                "💨 Verificar fixação de telhas e coberturas",
                "🌳 Podar árvores próximas à residência",
                "🪟 Reforçar portas e janelas",
                "📺 Proteger antenas e equipamentos externos"
            ])
        
        # Recomendações baseadas nos fatores principais
        for factor in main_factors[:3]:
            feature = factor['feature']
            
            if feature == 'velocidade_vento' and factor['value'] > 60:
                recommendations.append("⚠️ ALERTA: Vendaval destrutivo previsto - buscar abrigo seguro")
            elif feature == 'velocidade_vento' and factor['value'] > 40:
                recommendations.append("💨 Vento forte - evitar exposição e proteger objetos soltos")
            elif feature == 'pressao_atmosferica' and factor['value'] < 1000:
                recommendations.append("🌪️ Sistema de baixa pressão severa - risco de vendaval intenso")
            elif feature == 'tipo_residencia' and factor['value'] == 'sobrado':
                recommendations.append("🏠 Residência em altura - verificar estrutura e cobertura")
        
        return list(set(recommendations))  # Remover duplicatas
    
    def calculate_seasonal_adjustment(self, month: int) -> float:
        """
        Ajuste sazonal para vendaval
        Inverno/primavera = mais frentes frias e sistemas de baixa pressão
        """
        seasonal_factors = {
            12: 0.9, 1: 0.8, 2: 0.8,   # Verão - menor atividade de frentes
            3: 1.0, 4: 1.1, 5: 1.2,    # Outono - aumento gradual
            6: 1.4, 7: 1.5, 8: 1.4,    # Inverno - pico (frentes frias)
            9: 1.3, 10: 1.2, 11: 1.0   # Primavera - transição
        }
        
        return seasonal_factors.get(month, 1.0)
    
    def calculate_wind_direction_risk(self, wind_direction: float, region: str) -> float:
        """
        Calcula risco baseado na direção do vento para diferentes regiões
        """
        # Direções de maior risco por região (ventos predominantes)
        risk_directions = {
            'sul': [180, 225, 270],      # S, SW, W - frentes frias
            'sudeste': [135, 180, 225],  # SE, S, SW - frentes oceânicas
            'nordeste': [90, 135],       # E, SE - ventos alísios
            'norte': [45, 90, 135],      # NE, E, SE - sistemas amazônicos
            'centro-oeste': [180, 225, 270]  # S, SW, W - frentes secas
        }
        
        if region not in risk_directions:
            return 0.0
        
        # Calcular proximidade das direções de risco
        risk_dirs = risk_directions[region]
        min_diff = min(abs(wind_direction - rd) for rd in risk_dirs)
        
        # Risco máximo quando vento está na direção exata, diminui com diferença
        if min_diff <= 15:  # Dentro de 15 graus
            return 0.2
        elif min_diff <= 30:  # Dentro de 30 graus
            return 0.1
        elif min_diff <= 45:  # Dentro de 45 graus
            return 0.05
        
        return 0.0