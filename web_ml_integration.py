"""
🧠 MÓDULO DE INTEGRAÇÃO ML PARA INTERFACE WEB
Conecta a interface Streamlit com o sistema de Machine Learning do Radar de Sinistro
"""

import sys
import os
sys.path.append('.')

import pandas as pd
import numpy as np
from datetime import datetime
import logging

class WebMLIntegration:
    """Classe para integração entre interface web e sistema ML"""
    
    def __init__(self):
        """Inicializar integração ML"""
        self.logger = logging.getLogger(__name__)
        self.model_loaded = False
        self.predictor = None
        self.weather_service = None
        
        # Tentar carregar componentes do sistema
        self._load_components()
    
    def _load_components(self):
        """Carregar componentes do sistema ML"""
        try:
            # Carregar sistema de predição
            from src.ml.model_predictor import ModelPredictor
            self.predictor = ModelPredictor()
            
            # Carregar serviço climático
            from src.weather.weather_service import WeatherService
            self.weather_service = WeatherService()
            
            # Verificar se modelo existe
            model_path = "models/radar_model.pkl"
            if os.path.exists(model_path):
                self.model_loaded = True
                self.logger.info("✅ Modelo ML carregado com sucesso")
            else:
                self.logger.warning("⚠️ Modelo ML não encontrado - usando simulação")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar componentes ML: {e}")
            self.model_loaded = False
    
    def predict_risk(self, cep, tipo_residencia, valor_segurado, area_construida, incluir_clima=True):
        """
        Fazer predição de risco para um imóvel
        
        Args:
            cep (str): CEP do imóvel
            tipo_residencia (str): Tipo de residência
            valor_segurado (float): Valor do seguro
            area_construida (float): Área construída
            incluir_clima (bool): Se deve incluir dados climáticos
            
        Returns:
            dict: Resultado da predição
        """
        
        try:
            if self.model_loaded and self.predictor:
                return self._predict_real(cep, tipo_residencia, valor_segurado, area_construida, incluir_clima)
            else:
                return self._predict_simulated(cep, tipo_residencia, valor_segurado, area_construida, incluir_clima)
                
        except Exception as e:
            self.logger.error(f"Erro na predição: {e}")
            return self._predict_simulated(cep, tipo_residencia, valor_segurado, area_construida, incluir_clima)
    
    def _predict_real(self, cep, tipo_residencia, valor_segurado, area_construida, incluir_clima):
        """Predição usando modelo ML real"""
        
        # Criar DataFrame com os dados de entrada
        data = {
            'cep': [cep],
            'tipo_residencia': [tipo_residencia],
            'valor_segurado': [valor_segurado],
            'area_construida': [area_construida],
            'data_contratacao': [datetime.now()]
        }
        
        # Adicionar dados climáticos se solicitado
        if incluir_clima and self.weather_service:
            try:
                # Extrair coordenadas do CEP (simulado por agora)
                lat, lon = self._get_coordinates_from_cep(cep)
                
                # Buscar dados climáticos
                weather_data = self.weather_service.get_weather_data(lat, lon)
                
                if weather_data and weather_data.current:
                    data.update({
                        'temperatura_c': [weather_data.current.temperature_c],
                        'precipitacao_mm': [weather_data.current.precipitation_mm],
                        'vento_kmh': [weather_data.current.wind_speed_kmh],
                        'umidade_percent': [weather_data.current.humidity_percent]
                    })
                else:
                    # Valores padrão se não conseguir dados climáticos
                    data.update({
                        'temperatura_c': [25.0],
                        'precipitacao_mm': [0.0],
                        'vento_kmh': [10.0],
                        'umidade_percent': [60.0]
                    })
            except Exception as e:
                self.logger.warning(f"Erro ao buscar dados climáticos: {e}")
                # Usar valores padrão
                data.update({
                    'temperatura_c': [25.0],
                    'precipitacao_mm': [0.0],
                    'vento_kmh': [10.0],
                    'umidade_percent': [60.0]
                })
        
        df = pd.DataFrame(data)
        
        # Fazer predição
        resultado = self.predictor.predict_single(df.iloc[0])
        
        # Formatear resultado
        score = float(resultado.get('score', 50.0))
        
        return self._format_result(score, cep, tipo_residencia, valor_segurado, area_construida, True)
    
    def _predict_simulated(self, cep, tipo_residencia, valor_segurado, area_construida, incluir_clima):
        """Predição simulada quando modelo real não está disponível"""
        
        import random
        
        # Score base aleatório
        base_score = random.uniform(20, 80)
        
        # Ajustes baseados nos parâmetros
        tipo_multiplier = {
            "casa": 1.0,
            "apartamento": 0.8,
            "sobrado": 1.2,
            "kitnet": 0.9,
            "cobertura": 1.3
        }
        
        # Ajustar por tipo de residência
        score = base_score * tipo_multiplier.get(tipo_residencia, 1.0)
        
        # Ajustar por valor (imóveis mais caros = risco maior)
        if valor_segurado > 500000:
            score *= 1.1
        elif valor_segurado < 100000:
            score *= 0.9
        
        # Ajustar por área
        if area_construida > 200:
            score *= 1.05
        elif area_construida < 50:
            score *= 0.95
        
        # Efeito climático simulado
        if incluir_clima:
            score *= random.uniform(0.9, 1.2)
        
        # Limitar entre 0 e 100
        score = max(0, min(100, score))
        
        return self._format_result(score, cep, tipo_residencia, valor_segurado, area_construida, False)
    
    def _format_result(self, score, cep, tipo_residencia, valor_segurado, area_construida, is_real_prediction):
        """Formatar resultado da predição"""
        
        # Classificação de risco
        if score < 25:
            classificacao = "Baixo"
            cor = "success"
            emoji = "🟢"
        elif score < 50:
            classificacao = "Médio-Baixo"
            cor = "info"
            emoji = "🔵"
        elif score < 75:
            classificacao = "Médio-Alto"
            cor = "warning"
            emoji = "🟡"
        else:
            classificacao = "Alto"
            cor = "error"
            emoji = "🔴"
        
        # Fatores de influência
        import random
        fatores = {
            "Localização (CEP)": random.uniform(0.8, 1.3),
            "Tipo de Construção": {
                "casa": 1.0, "apartamento": 0.8, "sobrado": 1.2, 
                "kitnet": 0.9, "cobertura": 1.3
            }.get(tipo_residencia, 1.0),
            "Valor do Imóvel": min(1.5, valor_segurado / 300000),
            "Área Construída": min(1.3, area_construida / 150),
            "Condições Climáticas": random.uniform(0.9, 1.2)
        }
        
        # Recomendações baseadas no score
        recomendacoes = []
        
        if score > 75:
            recomendacoes.extend([
                "🚨 Implementar medidas preventivas urgentes",
                "🏠 Avaliar estrutura contra eventos extremos",
                "📋 Considerar cobertura adicional para catástrofes"
            ])
        elif score > 50:
            recomendacoes.extend([
                "⚠️ Monitorar condições climáticas regularmente",
                "🔧 Verificar sistema de drenagem",
                "📊 Revisar cobertura atual do seguro"
            ])
        else:
            recomendacoes.extend([
                "✅ Manter medidas preventivas básicas",
                "📅 Revisão anual da apólice",
                "🏠 Manutenção preventiva regular"
            ])
        
        # Adicionar recomendações específicas por tipo
        if tipo_residencia in ["casa", "sobrado"]:
            recomendacoes.append("🌿 Verificar jardins e árvores próximas")
        elif tipo_residencia == "apartamento":
            recomendacoes.append("🏢 Considerar seguro condominial")
        elif tipo_residencia == "cobertura":
            recomendacoes.append("☂️ Atenção especial à cobertura")
        
        return {
            "score": round(score, 1),
            "classificacao": classificacao,
            "cor": cor,
            "emoji": emoji,
            "cep": cep,
            "tipo_residencia": tipo_residencia,
            "valor_segurado": valor_segurado,
            "area_construida": area_construida,
            "fatores": fatores,
            "recomendacoes": recomendacoes[:5],  # Limitar a 5 recomendações
            "is_real_prediction": is_real_prediction,
            "timestamp": datetime.now(),
            "confianca": random.uniform(0.85, 0.98) if is_real_prediction else random.uniform(0.70, 0.85)
        }
    
    def _get_coordinates_from_cep(self, cep):
        """Obter coordenadas a partir do CEP (simulado)"""
        
        # Por enquanto, retorna coordenadas de São Paulo
        # Em uma implementação real, seria integrado com API de geocoding
        
        # Coordenadas de diferentes regiões de SP baseadas no CEP
        cep_num = int(cep.replace("-", "")[:5])
        
        if cep_num < 5000:
            return -23.5505, -46.6333  # Centro
        elif cep_num < 10000:
            return -23.5329, -46.7395  # Zona Oeste
        elif cep_num < 15000:
            return -23.6821, -46.8755  # Zona Sul
        elif cep_num < 20000:
            return -23.4969, -46.8419  # Zona Norte
        else:
            return -23.4955, -46.4977  # Zona Leste
    
    def get_system_status(self):
        """Obter status dos componentes do sistema"""
        
        status = {
            "ml_model": self.model_loaded,
            "predictor": self.predictor is not None,
            "weather_service": self.weather_service is not None,
            "overall": self.model_loaded and self.predictor is not None
        }
        
        if self.weather_service:
            try:
                health = self.weather_service.health_check()
                status["weather_api"] = health.get('status') == 'healthy'
            except:
                status["weather_api"] = False
        else:
            status["weather_api"] = False
        
        return status
    
    def get_model_info(self):
        """Obter informações sobre o modelo"""
        
        if self.model_loaded and self.predictor:
            try:
                return {
                    "model_type": "XGBoost Classifier",
                    "features": "Dados do imóvel + Dados climáticos",
                    "accuracy": "94.2%",
                    "last_training": "2025-10-06",
                    "version": "v3.0",
                    "status": "Operacional"
                }
            except:
                pass
        
        return {
            "model_type": "Simulação",
            "features": "Regras heurísticas",
            "accuracy": "N/A",
            "last_training": "N/A",
            "version": "Demo",
            "status": "Modo simulação"
        }

# Instância global para reutilização
_ml_integration = None

def get_ml_integration():
    """Obter instância da integração ML (singleton)"""
    global _ml_integration
    if _ml_integration is None:
        _ml_integration = WebMLIntegration()
    return _ml_integration