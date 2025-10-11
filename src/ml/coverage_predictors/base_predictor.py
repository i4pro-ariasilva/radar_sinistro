#!/usr/bin/env python3
"""
Classe base para modelos específicos de predição de risco por cobertura.
Integra dados da apólice com dados climáticos em tempo real.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any
import joblib
import os
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoverageSpecificPredictor(ABC):
    """
    Classe base para modelos específicos de predição de risco por cobertura.
    Integra dados da apólice com dados climáticos em tempo real.
    """
    
    def __init__(self, coverage_name: str):
        self.coverage_name = coverage_name
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_importance = {}
        self.model_path = f"models/{coverage_name.lower()}_model.pkl"
        self.is_trained = False
        
        # Criar diretório de modelos se não existir
        os.makedirs("models", exist_ok=True)
        
    @abstractmethod
    def get_climate_features(self) -> List[str]:
        """Retorna lista de features climáticas relevantes para esta cobertura"""
        pass
    
    @abstractmethod
    def get_property_features(self) -> List[str]:
        """Retorna lista de features da propriedade relevantes para esta cobertura"""
        pass
    
    @abstractmethod
    def calculate_risk_score(self, climate_data: Dict, property_data: Dict) -> float:
        """Calcula score de risco específico baseado nos dados"""
        pass
    
    def get_current_weather_data(self, latitude: float, longitude: float) -> Dict:
        """
        Obtém dados climáticos atuais para a localização da apólice
        """
        try:
            from src.weather.weather_service import WeatherService
            
            weather_service = WeatherService()
            current_weather = weather_service.get_current_weather(latitude, longitude)
            
            if current_weather:
                # Converter WeatherData para formato padronizado
                weather_data = {
                    'temperatura_atual': getattr(current_weather, 'temperature_current', 25.0),
                    'temperatura_maxima': getattr(current_weather, 'temperature_max', 30.0),
                    'temperatura_minima': getattr(current_weather, 'temperature_min', 20.0),
                    'umidade_relativa': getattr(current_weather, 'humidity', 60.0),
                    'pressao_atmosferica': getattr(current_weather, 'pressure', 1013.25),
                    'velocidade_vento': getattr(current_weather, 'wind_speed', 10.0),
                    'direcao_vento': getattr(current_weather, 'wind_direction', 180.0),
                    'precipitacao_mm': getattr(current_weather, 'precipitation', 0.0),
                    'visibilidade': getattr(current_weather, 'visibility', 10.0),
                    'cobertura_nuvens': getattr(current_weather, 'cloud_cover', 50.0),
                    'indice_uv': getattr(current_weather, 'uv_index', 3.0),
                    'sensacao_termica': getattr(current_weather, 'temperature_apparent', 
                                               getattr(current_weather, 'temperature_current', 25.0)),
                    'ponto_orvalho': getattr(current_weather, 'dew_point', 
                                           getattr(current_weather, 'temperature_current', 25.0) - 5)
                }
                
                return weather_data
            else:
                logger.warning("Dados climáticos não disponíveis, usando padrão")
                return self._get_default_weather_data()
                
        except Exception as e:
            logger.warning(f"Erro ao obter dados climáticos: {e}")
            # Retornar dados padrão em caso de erro
            return self._get_default_weather_data()
    
    def _get_default_weather_data(self) -> Dict:
        """Dados climáticos padrão para fallback"""
        return {
            'temperatura_atual': 22.0,
            'temperatura_maxima': 28.0,
            'temperatura_minima': 16.0,
            'umidade_relativa': 65.0,
            'pressao_atmosferica': 1013.25,
            'velocidade_vento': 5.0,
            'direcao_vento': 180.0,
            'precipitacao_mm': 0.0,
            'visibilidade': 10000.0,
            'cobertura_nuvens': 30.0,
            'indice_uv': 5.0,
            'sensacao_termica': 22.0,
            'ponto_orvalho': 12.0
        }
    
    def extract_property_features(self, policy_data: Dict) -> Dict:
        """
        Extrai features da propriedade relevantes para análise de risco
        """
        property_features = {}
        
        # Idade do imóvel (estimada pela data de construção ou padrão)
        ano_construcao = policy_data.get('ano_construcao')
        if ano_construcao:
            property_features['idade_imovel'] = datetime.now().year - int(ano_construcao)
        else:
            # Estimar idade baseada no tipo de residência
            tipo_residencia = policy_data.get('tipo_residencia', 'casa').lower()
            if tipo_residencia == 'apartamento':
                property_features['idade_imovel'] = 15  # Média para apartamentos
            else:
                property_features['idade_imovel'] = 25  # Média para casas
        
        # Tipo de imóvel
        property_features['tipo_residencia'] = policy_data.get('tipo_residencia', 'casa').lower()
        
        # Valor segurado (proxy para padrão da construção)
        valor_segurado = float(policy_data.get('valor_segurado', 100000))
        property_features['valor_segurado'] = valor_segurado
        property_features['faixa_valor'] = self._categorize_property_value(valor_segurado)
        
        # Localização
        cep = policy_data.get('cep', '00000000')
        property_features['cep_prefixo'] = cep[:5] if len(cep) >= 5 else '00000'
        property_features['regiao_metropolitana'] = self._is_metropolitan_area(cep)
        
        # Features derivadas
        property_features['risco_construcao'] = self._calculate_construction_risk(
            property_features['idade_imovel'],
            property_features['tipo_residencia'],
            property_features['faixa_valor']
        )
        
        return property_features
    
    def _categorize_property_value(self, valor: float) -> str:
        """Categoriza o valor da propriedade"""
        if valor < 100000:
            return 'baixo'
        elif valor < 300000:
            return 'medio'
        elif valor < 500000:
            return 'alto'
        else:
            return 'premium'
    
    def _is_metropolitan_area(self, cep: str) -> bool:
        """Verifica se o CEP está em região metropolitana"""
        if len(cep) < 2:
            return False
        
        # Principais regiões metropolitanas do Brasil
        metro_prefixes = ['01', '02', '03', '04', '05', '06', '07', '08', '09',  # SP
                         '20', '21', '22', '23', '24', '25', '26', '27', '28',  # RJ
                         '30', '31', '32',  # BH
                         '40', '41', '42',  # Salvador
                         '50', '51', '52',  # Recife
                         '60', '61',        # Fortaleza
                         '70', '71', '72',  # Brasília
                         '80', '81', '82',  # Curitiba
                         '90', '91', '92']  # Porto Alegre
        
        return cep[:2] in metro_prefixes
    
    def _calculate_construction_risk(self, idade: int, tipo: str, faixa_valor: str) -> float:
        """Calcula risco de construção baseado em características da propriedade"""
        risk_score = 0.0
        
        # Risco por idade
        if idade > 30:
            risk_score += 0.3
        elif idade > 20:
            risk_score += 0.2
        elif idade > 10:
            risk_score += 0.1
        
        # Risco por tipo
        type_risk = {
            'casa': 0.2,
            'sobrado': 0.3,
            'apartamento': 0.1,
            'kitnet': 0.15
        }
        risk_score += type_risk.get(tipo, 0.2)
        
        # Risco por faixa de valor (valor baixo = maior risco)
        value_risk = {
            'baixo': 0.3,
            'medio': 0.2,
            'alto': 0.1,
            'premium': 0.05
        }
        risk_score += value_risk.get(faixa_valor, 0.2)
        
        return min(risk_score, 1.0)
    
    def prepare_features(self, policy_data: Dict) -> Dict:
        """
        Prepara todas as features necessárias para predição
        """
        # Obter coordenadas da apólice
        latitude = policy_data.get('latitude', -15.0)  # Centro do Brasil como padrão
        longitude = policy_data.get('longitude', -47.0)
        
        # Obter dados climáticos atuais
        climate_data = self.get_current_weather_data(latitude, longitude)
        
        # Obter dados da propriedade
        property_data = self.extract_property_features(policy_data)
        
        # Combinar todas as features
        all_features = {**climate_data, **property_data}
        
        # Adicionar features temporais
        now = datetime.now()
        all_features['mes'] = now.month
        all_features['estacao'] = self._get_season(now.month)
        all_features['hora_dia'] = now.hour
        
        # Codificar variáveis categóricas
        all_features = self._encode_categorical_features(all_features)
        
        return all_features
    
    def _encode_categorical_features(self, features: Dict) -> Dict:
        """
        Codifica variáveis categóricas para valores numéricos
        """
        encoded_features = features.copy()
        
        # Codificar estação
        estacao_encoding = {
            'verao': 0,
            'outono': 1, 
            'inverno': 2,
            'primavera': 3
        }
        if 'estacao' in encoded_features:
            encoded_features['estacao'] = estacao_encoding.get(encoded_features['estacao'], 3)
        
        # Codificar tipo de residência
        tipo_encoding = {
            'casa': 0,
            'apartamento': 1,
            'sobrado': 2,
            'cobertura': 3
        }
        if 'tipo_residencia' in encoded_features:
            encoded_features['tipo_residencia'] = tipo_encoding.get(encoded_features['tipo_residencia'], 0)
        
        # Codificar faixa de valor
        valor_encoding = {
            'baixo': 0,
            'medio': 1,
            'alto': 2,
            'premium': 3
        }
        if 'faixa_valor' in encoded_features:
            encoded_features['faixa_valor'] = valor_encoding.get(encoded_features['faixa_valor'], 1)
        
        # Converter variáveis booleanas para numérico
        if 'regiao_metropolitana' in encoded_features:
            encoded_features['regiao_metropolitana'] = int(encoded_features['regiao_metropolitana'])
        
        # Tratar valores None - substitui por médias/valores padrão seguros
        none_replacements = {
            'temperatura_maxima': 25.0,
            'temperatura_minima': 15.0,
            'visibilidade': 10000.0,  # 10km em metros
            'probabilidade_chuva': 0.0,
            'indice_qualidade_ar': 50.0,  # Moderado
            'nebulosidade': 50.0,  # 50%
        }
        
        for key, default_value in none_replacements.items():
            if key in encoded_features and encoded_features[key] is None:
                encoded_features[key] = default_value
        
        # Remover features não numéricas que podem causar problemas no modelo
        non_numeric_keys = []
        for key, value in encoded_features.items():
            if isinstance(value, str):
                non_numeric_keys.append(key)
        
        for key in non_numeric_keys:
            # Converter CEP para código numérico se possível
            if 'cep' in key.lower():
                try:
                    encoded_features[key] = int(encoded_features[key])
                except (ValueError, TypeError):
                    # Se não conseguir converter, usar código padrão
                    encoded_features[key] = 0
            else:
                # Remover outras strings que não podem ser convertidas
                del encoded_features[key]
        
        return encoded_features
    
    def _get_season(self, month: int) -> str:
        """Retorna a estação do ano baseada no mês (hemisfério sul)"""
        if month in [12, 1, 2]:
            return 'verao'
        elif month in [3, 4, 5]:
            return 'outono'
        elif month in [6, 7, 8]:
            return 'inverno'
        else:
            return 'primavera'
    
    def predict_risk(self, policy_data: Dict) -> Dict:
        """
        Prediz o risco de sinistro para a cobertura específica
        """
        if not self.is_trained:
            logger.warning(f"Modelo {self.coverage_name} não foi treinado. Usando cálculo heurístico.")
            return self._heuristic_prediction(policy_data)
        
        try:
            # Preparar features
            features = self.prepare_features(policy_data)
            
            # Selecionar apenas features relevantes
            relevant_features = self.get_climate_features() + self.get_property_features()
            feature_vector = []
            
            for feature_name in relevant_features:
                if feature_name in features:
                    feature_vector.append(features[feature_name])
                else:
                    feature_vector.append(0.0)  # Valor padrão
            
            # Fazer predição
            feature_array = np.array(feature_vector).reshape(1, -1)
            
            # Aplicar escalonamento se o modelo foi treinado
            if hasattr(self, 'scaler') and self.scaler:
                feature_array = self.scaler.transform(feature_array)
            
            # Predição de probabilidade
            probability = self.model.predict_proba(feature_array)[0][1]  # Classe positiva
            
            # Calcular score de risco customizado
            risk_score = self.calculate_risk_score(
                {k: v for k, v in features.items() if k in self.get_climate_features()},
                {k: v for k, v in features.items() if k in self.get_property_features()}
            )
            
            # Combinar predição do modelo com score customizado
            final_probability = (probability + risk_score) / 2
            
            return {
                'coverage': self.coverage_name,
                'probability': min(final_probability, 1.0),
                'risk_score': final_probability * 100,
                'risk_level': self._classify_risk_level(final_probability),
                'model_prediction': probability,
                'heuristic_score': risk_score,
                'main_factors': self._get_main_risk_factors(features)
            }
            
        except Exception as e:
            logger.error(f"Erro na predição para {self.coverage_name}: {e}")
            return self._heuristic_prediction(policy_data)
    
    def _heuristic_prediction(self, policy_data: Dict) -> Dict:
        """Predição heurística quando o modelo não está disponível"""
        features = self.prepare_features(policy_data)
        
        climate_data = {k: v for k, v in features.items() if k in self.get_climate_features()}
        property_data = {k: v for k, v in features.items() if k in self.get_property_features()}
        
        risk_score = self.calculate_risk_score(climate_data, property_data)
        
        return {
            'coverage': self.coverage_name,
            'probability': risk_score,
            'risk_score': risk_score * 100,
            'risk_level': self._classify_risk_level(risk_score),
            'model_prediction': None,
            'heuristic_score': risk_score,
            'main_factors': self._get_main_risk_factors(features)
        }
    
    def _classify_risk_level(self, probability: float) -> str:
        """Classifica o nível de risco baseado na probabilidade"""
        if probability >= 0.7:
            return 'alto'
        elif probability >= 0.4:
            return 'medio'
        elif probability >= 0.2:
            return 'baixo'
        else:
            return 'muito_baixo'
    
    def _get_main_risk_factors(self, features: Dict) -> List[Dict]:
        """Identifica os principais fatores de risco"""
        factors = []
        
        # Adicionar fatores baseados nas features mais relevantes
        relevant_features = self.get_climate_features() + self.get_property_features()
        
        for feature in relevant_features[:5]:  # Top 5 features
            if feature in features:
                importance = self.feature_importance.get(feature, 0.1)
                factors.append({
                    'feature': feature,
                    'value': features[feature],
                    'importance': importance
                })
        
        return sorted(factors, key=lambda x: x['importance'], reverse=True)
    
    def save_model(self):
        """Salva o modelo treinado"""
        if self.model is not None:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'label_encoders': self.label_encoders,
                'feature_importance': self.feature_importance,
                'coverage_name': self.coverage_name,
                'is_trained': self.is_trained
            }
            
            joblib.dump(model_data, self.model_path)
            logger.info(f"Modelo {self.coverage_name} salvo em {self.model_path}")
    
    def load_model(self) -> bool:
        """Carrega modelo salvo"""
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.label_encoders = model_data['label_encoders']
                self.feature_importance = model_data['feature_importance']
                self.is_trained = model_data.get('is_trained', True)
                
                # Log controlado para evitar spam
                if not hasattr(self.__class__, '_models_logged'):
                    self.__class__._models_logged = set()
                    
                if self.coverage_name not in self.__class__._models_logged:
                    logger.info(f"Modelo {self.coverage_name} carregado de {self.model_path}")
                    self.__class__._models_logged.add(self.coverage_name)
                    
                return True
            else:
                logger.warning(f"Arquivo de modelo não encontrado: {self.model_path}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao carregar modelo {self.coverage_name}: {e}")
            return False
