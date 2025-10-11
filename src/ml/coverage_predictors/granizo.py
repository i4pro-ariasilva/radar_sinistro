#!/usr/bin/env python3
"""
Modelo específico para predição de risco de Granizo.
Fatores principais: instabilidade atmosférica, temperatura, correntes de ar.
"""

from typing import Dict, List
import numpy as np
from .base_predictor import CoverageSpecificPredictor

class GranizoPredictor(CoverageSpecificPredictor):
    """
    Modelo específico para predição de risco de Granizo.
    Fatores principais: instabilidade atmosférica, temperatura, correntes de ar.
    """
    
    def __init__(self):
        super().__init__("Granizo")
        
        # Features de importância específicas para granizo
        self.feature_importance = {
            'temperatura_diferencial': 0.30,
            'umidade_relativa': 0.25,
            'pressao_atmosferica': 0.20,
            'velocidade_vento': 0.15,
            'tipo_residencia': 0.10
        }
    
    def get_climate_features(self) -> List[str]:
        """Features climáticas relevantes para granizo"""
        return [
            'temperatura_diferencial',
            'temperatura_maxima',
            'umidade_relativa',
            'pressao_atmosferica',
            'velocidade_vento',
            'cobertura_nuvens',
            'indice_uv',
            'mes',
            'estacao',
            'hora_dia'
        ]
    
    def get_property_features(self) -> List[str]:
        """Features da propriedade relevantes para granizo"""
        return [
            'tipo_residencia',
            'faixa_valor',
            'regiao_metropolitana',
            'risco_construcao'
        ]
    
    def calculate_risk_score(self, climate_data: Dict, property_data: Dict) -> float:
        """
        Calcula score de risco específico para granizo
        Baseado em: instabilidade atmosférica, correntes ascendentes, temperatura
        """
        risk_score = 0.0
        
        # Risco climático
        
        # Diferencial de temperatura (instabilidade atmosférica)
        temp_max = climate_data.get('temperatura_maxima', 25)
        temp_min = climate_data.get('temperatura_minima', 15)
        temp_diff = temp_max - temp_min
        if temp_diff > 20:  # Grande instabilidade
            risk_score += 0.4
        elif temp_diff > 15:  # Instabilidade moderada
            risk_score += 0.3
        elif temp_diff > 10:  # Instabilidade leve
            risk_score += 0.2
        
        # Temperatura máxima (calor = correntes ascendentes)
        if temp_max > 35:  # Muito quente
            risk_score += 0.3
        elif temp_max > 30:  # Quente
            risk_score += 0.2
        elif temp_max > 25:  # Morno
            risk_score += 0.1
        
        # Umidade alta (energia para formação de granizo)
        umidade = climate_data.get('umidade_relativa', 0)
        if umidade > 80:
            risk_score += 0.25
        elif umidade > 70:
            risk_score += 0.15
        elif umidade > 60:
            risk_score += 0.1
        
        # Pressão atmosférica (baixa pressão = sistemas convectivos)
        pressao = climate_data.get('pressao_atmosferica', 1013.25)
        if pressao < 1005:  # Baixa pressão (sistemas convectivos)
            risk_score += 0.25
        elif pressao < 1010:
            risk_score += 0.15
        
        # Velocidade do vento (correntes de ar)
        vento = climate_data.get('velocidade_vento', 0)
        if vento > 50:  # Vento muito forte (supercélulas)
            risk_score += 0.3
        elif vento > 30:  # Vento forte
            risk_score += 0.2
        elif vento > 15:  # Vento moderado
            risk_score += 0.1
        
        # Cobertura de nuvens (sistemas convectivos)
        nuvens = climate_data.get('cobertura_nuvens', 0)
        if nuvens > 70:  # Muito nublado
            risk_score += 0.15
        elif nuvens > 50:
            risk_score += 0.1
        
        # Índice UV alto (calor intenso)
        uv = climate_data.get('indice_uv', 0)
        if uv > 9:  # UV extremo
            risk_score += 0.15
        elif uv > 7:  # UV alto
            risk_score += 0.1
        
        # Hora do dia (tarde = pico de instabilidade)
        hora = climate_data.get('hora_dia', 12)
        if 14 <= hora <= 18:  # Pico da tarde
            risk_score += 0.2
        elif 12 <= hora <= 20:  # Período de risco
            risk_score += 0.1
        
        # Sazonalidade (final de primavera/início de verão)
        estacao = climate_data.get('estacao', 'verao')
        mes = climate_data.get('mes', 6)
        
        if estacao == 'primavera' and mes in [10, 11]:  # Final da primavera
            risk_score += 0.2
        elif estacao == 'verao' and mes in [12, 1]:  # Início do verão
            risk_score += 0.25
        elif estacao == 'verao':
            risk_score += 0.15
        elif estacao == 'primavera':
            risk_score += 0.1
        
        # Risco da propriedade
        
        # Tipo de residência (exposição)
        tipo = property_data.get('tipo_residencia', 'casa')
        if tipo == 'sobrado':
            risk_score += 0.15  # Maior área de cobertura exposta
        elif tipo == 'casa':
            risk_score += 0.1
        elif tipo == 'apartamento':
            risk_score += 0.02  # Menor exposição
        
        # Faixa de valor (qualidade da cobertura)
        faixa_valor = property_data.get('faixa_valor', 'medio')
        if faixa_valor == 'baixo':
            risk_score += 0.1   # Cobertura menos resistente
        elif faixa_valor == 'premium':
            risk_score -= 0.05  # Cobertura mais resistente
        
        # Região metropolitana (ilha de calor = mais instabilidade)
        if property_data.get('regiao_metropolitana', False):
            risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    def get_specific_recommendations(self, risk_level: str, main_factors: List[Dict]) -> List[str]:
        """
        Recomendações específicas para granizo
        """
        recommendations = []
        
        if risk_level in ['alto', 'medio']:
            recommendations.extend([
                "🚗 Proteger veículos em garagem coberta",
                "🏠 Verificar resistência da cobertura",
                "🌡️ Monitorar previsão de instabilidade atmosférica",
                "☂️ Evitar exposição ao ar livre durante tempestades"
            ])
        
        # Recomendações baseadas nos fatores principais
        for factor in main_factors[:3]:
            feature = factor['feature']
            
            if feature == 'temperatura_diferencial' and factor['value'] > 15:
                recommendations.append("🌡️ Grande variação térmica - alta instabilidade atmosférica")
            elif feature == 'umidade_relativa' and factor['value'] > 80:
                recommendations.append("💧 Umidade alta + calor = condições ideais para granizo")
            elif feature == 'velocidade_vento' and factor['value'] > 40:
                recommendations.append("💨 Ventos fortes podem indicar supercélulas com granizo")
            elif feature == 'hora_dia' and 14 <= factor['value'] <= 18:
                recommendations.append("🕐 Período de maior risco (tarde) - máxima instabilidade")
        
        return list(set(recommendations))  # Remover duplicatas
    
    def calculate_seasonal_adjustment(self, month: int) -> float:
        """
        Ajuste sazonal para granizo
        Final da primavera/início do verão = pico de granizo
        """
        seasonal_factors = {
            12: 1.4, 1: 1.3, 2: 1.1,   # Verão - pico no início
            3: 0.9, 4: 0.8, 5: 0.7,    # Outono - diminuição
            6: 0.6, 7: 0.6, 8: 0.7,    # Inverno - mínimo
            9: 0.8, 10: 1.2, 11: 1.3   # Primavera - aumento (pico em nov)
        }
        
        return seasonal_factors.get(month, 1.0)
    
    def calculate_instability_index(self, climate_data: Dict) -> float:
        """
        Calcula índice de instabilidade atmosférica para granizo
        """
        temp_max = climate_data.get('temperatura_maxima', 25)
        temp_min = climate_data.get('temperatura_minima', 15)
        umidade = climate_data.get('umidade_relativa', 70)
        pressao = climate_data.get('pressao_atmosferica', 1013.25)
        vento = climate_data.get('velocidade_vento', 10)
        
        # Índice baseado em parâmetros meteorológicos
        temp_diff = temp_max - temp_min
        
        # Fórmula simplificada de instabilidade
        instability = (
            (temp_diff / 20.0) * 0.3 +          # Gradiente térmico
            (umidade / 100.0) * 0.25 +          # Umidade
            ((1020 - pressao) / 30.0) * 0.25 +  # Pressão baixa
            (min(vento, 60) / 60.0) * 0.2       # Vento (limitado)
        )
        
        return min(instability, 1.0)
    
    def get_hail_size_probability(self, risk_score: float) -> Dict[str, float]:
        """
        Estima probabilidade de diferentes tamanhos de granizo
        """
        if risk_score < 0.3:
            return {
                'pequeno': 0.7,    # < 1cm
                'medio': 0.3,      # 1-3cm  
                'grande': 0.0,     # 3-5cm
                'muito_grande': 0.0 # > 5cm
            }
        elif risk_score < 0.6:
            return {
                'pequeno': 0.5,
                'medio': 0.4,
                'grande': 0.1,
                'muito_grande': 0.0
            }
        else:
            return {
                'pequeno': 0.3,
                'medio': 0.4,
                'grande': 0.25,
                'muito_grande': 0.05
            }
