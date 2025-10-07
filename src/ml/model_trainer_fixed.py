"""
Treinamento do Modelo XGBoost para Sistema de Radar de Sinistro
"""

import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import joblib
import os
import logging
from typing import Tuple, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Classe responsável pelo treinamento do modelo XGBoost"""
    
    def __init__(self, model_dir: str = 'models'):
        self.model_dir = model_dir
        self.model = None
        self.training_history = {}
        self.feature_importance = {}
        
        # Configurações padrão do XGBoost para protótipo
        self.default_params = {
            'n_estimators': 100,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
            'eval_metric': 'logloss',
            'use_label_encoder': False
        }
        
        # Criar diretório de modelos
        os.makedirs(self.model_dir, exist_ok=True)
    
    def train_model(self, X_train: pd.DataFrame, X_test: pd.DataFrame,
                   y_train: pd.Series, y_test: pd.Series,
                   custom_params: Dict = None) -> Dict[str, Any]:
        """
        Treina o modelo XGBoost
        
        Args:
            X_train, X_test: Features de treino e teste
            y_train, y_test: Target de treino e teste
            custom_params: Parâmetros customizados (opcional)
            
        Returns:
            Dicionário com métricas de performance
        """
        logger.info("Iniciando treinamento do modelo XGBoost...")
        
        # Usar parâmetros customizados ou padrão
        params = self.default_params.copy()
        if custom_params:
            params.update(custom_params)
        
        # Inicializar modelo
        self.model = XGBClassifier(**params)
        
        # Treinar modelo
        self.model.fit(X_train, y_train)
        
        # Avaliar performance
        results = self._evaluate_model(X_train, X_test, y_train, y_test)
        
        # Salvar histórico
        self.training_history = {
            'training_date': datetime.now().isoformat(),
            'train_size': len(X_train),
            'test_size': len(X_test),
            'feature_count': len(X_train.columns),
            'feature_names': list(X_train.columns),
            'target_distribution': {
                'train': y_train.value_counts().to_dict(),
                'test': y_test.value_counts().to_dict()
            },
            'model_params': params,
            'performance': results
        }
        
        # Salvar feature importance
        self.feature_importance = dict(zip(
            X_train.columns,
            self.model.feature_importances_
        ))
        
        logger.info(f"Modelo treinado com AUC: {results['auc_roc']:.3f}")
        return results
    
    def _evaluate_model(self, X_train: pd.DataFrame, X_test: pd.DataFrame,
                       y_train: pd.Series, y_test: pd.Series) -> Dict[str, Any]:
        """Avalia performance do modelo"""
        
        # Predições
        y_train_pred = self.model.predict(X_train)
        y_test_pred = self.model.predict(X_test)
        
        # Probabilidades
        y_train_proba = self.model.predict_proba(X_train)[:, 1]
        y_test_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Métricas
        results = {
            'auc_roc_train': roc_auc_score(y_train, y_train_proba),
            'auc_roc': roc_auc_score(y_test, y_test_proba),
            'confusion_matrix_train': confusion_matrix(y_train, y_train_pred).tolist(),
            'confusion_matrix_test': confusion_matrix(y_test, y_test_pred).tolist()
        }
        
        # Relatórios de classificação
        train_report = classification_report(y_train, y_train_pred, output_dict=True)
        test_report = classification_report(y_test, y_test_pred, output_dict=True)
        
        results['classification_report_train'] = train_report
        results['classification_report_test'] = test_report
        
        # M�tricas principais para f�cil acesso - verificar se classe '1' existe
        if '1' in test_report:
            results['precision'] = test_report['1']['precision']
            results['recall'] = test_report['1']['recall']
            results['f1_score'] = test_report['1']['f1-score']
        else:
            # Se s� existe classe '0', usar m�tricas gerais
            results['precision'] = test_report.get('macro avg', {}).get('precision', 0.0)
            results['recall'] = test_report.get('macro avg', {}).get('recall', 0.0)
            results['f1_score'] = test_report.get('macro avg', {}).get('f1-score', 0.0)
            logger.warning("Classe '1' n�o encontrada nos dados de teste. Usando m�tricas gerais.")
        
        
        return results
    
    def save_model(self, model_name: str = 'radar_model.pkl'):
        """Salva o modelo treinado"""
        if self.model is None:
            raise ValueError("Modelo não foi treinado ainda")
        
        model_path = os.path.join(self.model_dir, model_name)
        joblib.dump(self.model, model_path)
        
        # Salvar metadados
        metadata_path = os.path.join(self.model_dir, 'model_metadata.pkl')
        metadata = {
            'training_history': self.training_history,
            'feature_importance': self.feature_importance,
            'model_version': '1.0.0',
            'saved_at': datetime.now().isoformat()
        }
        joblib.dump(metadata, metadata_path)
        
        logger.info(f"Modelo salvo em {model_path}")
        return model_path
    
    def load_model(self, model_name: str = 'radar_model.pkl'):
        """Carrega modelo salvo"""
        model_path = os.path.join(self.model_dir, model_name)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo não encontrado: {model_path}")
        
        self.model = joblib.load(model_path)
        
        # Carregar metadados se existirem
        metadata_path = os.path.join(self.model_dir, 'model_metadata.pkl')
        if os.path.exists(metadata_path):
            metadata = joblib.load(metadata_path)
            self.training_history = metadata.get('training_history', {})
            self.feature_importance = metadata.get('feature_importance', {})
        
        logger.info(f"Modelo carregado de {model_path}")
    
    def get_feature_importance(self, top_n: int = 10) -> Dict[str, float]:
        """Retorna as features mais importantes"""
        if not self.feature_importance:
            return {}
        
        # Ordenar por importância
        sorted_features = sorted(
            self.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return dict(sorted_features[:top_n])
    
    def print_training_summary(self):
        """Imprime resumo do treinamento"""
        if not self.training_history:
            print("Modelo não foi treinado ainda")
            return
        
        history = self.training_history
        perf = history['performance']
        
        print("="*50)
        print("    RESUMO DO TREINAMENTO")
        print("="*50)
        print(f"Data: {history['training_date']}")
        print(f"Amostras treino: {history['train_size']}")
        print(f"Amostras teste: {history['test_size']}")
        print(f"Features: {history['feature_count']}")
        
        print("\n--- PERFORMANCE ---")
        print(f"AUC-ROC: {perf['auc_roc']:.3f}")
        print(f"Precision: {perf['precision']:.3f}")
        print(f"Recall: {perf['recall']:.3f}")
        print(f"F1-Score: {perf['f1_score']:.3f}")
        print(f"Accuracy: {perf['accuracy']:.3f}")
        
        print("\n--- TOP 5 FEATURES ---")
        top_features = self.get_feature_importance(5)
        for feature, importance in top_features.items():
            print(f"{feature}: {importance:.3f}")
        
        print("\n--- DISTRIBUIÇÃO TARGET ---")
        train_dist = history['target_distribution']['train']
        test_dist = history['target_distribution']['test']
        print(f"Treino - Sem sinistro: {train_dist.get(0, 0)}, Com sinistro: {train_dist.get(1, 0)}")
        print(f"Teste - Sem sinistro: {test_dist.get(0, 0)}, Com sinistro: {test_dist.get(1, 0)}")
        print("="*50)
    
    def quick_train(self, df_features: pd.DataFrame, 
                   test_size: float = 0.3) -> Dict[str, Any]:
        """
        Treinamento rápido para protótipo
        
        Args:
            df_features: DataFrame com features e target
            test_size: Proporção para teste
            
        Returns:
            Métricas de performance
        """
        from .feature_engineering import FeatureEngineer
        
        # Preparar dados usando feature engineer
        fe = FeatureEngineer()
        X_train, X_test, y_train, y_test = fe.prepare_model_data(df_features, test_size)
        
        # Treinar modelo
        results = self.train_model(X_train, X_test, y_train, y_test)
        
        # Salvar feature engineer e modelo
        fe.save_preprocessors(self.model_dir)
        self.save_model()
        
        # Mostrar resumo
        self.print_training_summary()
        
        return results
    
    def predict_batch(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Faz predições em lote
        
        Returns:
            (predictions, probabilities)
        """
        if self.model is None:
            raise ValueError("Modelo não foi treinado ou carregado")
        
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)[:, 1]
        
        return predictions, probabilities
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo"""
        if not self.training_history:
            return {'status': 'not_trained'}
        
        return {
            'status': 'trained',
            'training_date': self.training_history['training_date'],
            'performance': {
                'auc_roc': self.training_history['performance']['auc_roc'],
                'precision': self.training_history['performance']['precision'],
                'recall': self.training_history['performance']['recall'],
                'f1_score': self.training_history['performance']['f1_score']
            },
            'feature_count': self.training_history['feature_count'],
            'train_size': self.training_history['train_size']
        }


# Exemplo de uso
if __name__ == "__main__":
    # Teste com dados simulados
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    try:
        from .feature_engineering import FeatureEngineer
        from database import SampleDataGenerator
        
        # Gerar dados de exemplo
        generator = SampleDataGenerator()
        policies = generator.generate_sample_policies(500)
        claims = generator.generate_sample_claims(policies, 50)
        
        df_policies = pd.DataFrame(policies)
        df_claims = pd.DataFrame(claims)
        
        # Criar features
        fe = FeatureEngineer()
        features_df = fe.create_features(df_policies, df_claims)
        
        # Treinar modelo
        trainer = ModelTrainer()
        results = trainer.quick_train(features_df)
        
        print("Treinamento concluído!")
        
    except Exception as e:
        print(f"Erro no teste: {e}")
        print("Execute através do sistema principal.")
