"""
Módulo de Machine Learning - Sistema de Radar de Sinistro
"""

from .feature_engineering import FeatureEngineer
from .model_trainer import ModelTrainer
from .model_predictor import ModelPredictor
from .model_evaluator import ModelEvaluator

__all__ = [
    'FeatureEngineer',
    'ModelTrainer', 
    'ModelPredictor',
    'ModelEvaluator'
]

# Versão do módulo ML
__version__ = '1.0.0'

# Configurações padrão para o protótipo
DEFAULT_CONFIG = {
    'model_type': 'xgboost',
    'test_size': 0.3,
    'random_state': 42,
    'n_estimators': 100,
    'max_depth': 6,
    'learning_rate': 0.1
}
