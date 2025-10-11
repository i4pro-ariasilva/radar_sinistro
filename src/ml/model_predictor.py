"""
Sistema de Predição de Risco para Radar de Sinistro
"""

import pandas as pd
import numpy as np
import joblib
import os
import logging
from typing import Dict, List, Any, Union, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelPredictor:
    """Classe responsável por predições de risco em produção"""
    
    def __init__(self, model_dir: str = 'models'):
        self.model_dir = model_dir
        self.model = None
        self.feature_engineer = None
        self.is_loaded = False
        
        # Configurações de scoring
        self.risk_thresholds = {
            'baixo': 25,
            'medio': 50,
            'alto': 75,
            'critico': 100
        }
    
    def load_model_and_preprocessors(self):
        """Carrega modelo e preprocessors salvos"""
        try:
            # Carregar modelo
            model_path = os.path.join(self.model_dir, 'radar_model.pkl')
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Modelo não encontrado: {model_path}")
            
            self.model = joblib.load(model_path)
            
            # Carregar preprocessors
            from .feature_engineering import FeatureEngineer
            self.feature_engineer = FeatureEngineer()
            self.feature_engineer.load_preprocessors(self.model_dir)
            
            self.is_loaded = True
            logger.info("Modelo e preprocessors carregados com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            raise
    
    def predict_single_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prediz risco para uma única apólice
        
        Args:
            policy_data: Dicionário com dados da apólice
            
        Returns:
            Dicionário com score de risco e detalhes
        """
        if not self.is_loaded:
            self.load_model_and_preprocessors()
        
        try:
            # Converter para DataFrame
            df = pd.DataFrame([policy_data])
            
            # Aplicar transformações
            X = self.feature_engineer.transform_new_data(df)
            
            # Fazer predição
            probability = self.model.predict_proba(X)[0, 1]
            prediction = self.model.predict(X)[0]
            
            # Converter para score 0-100
            risk_score = self._probability_to_score(probability)
            risk_level = self._score_to_level(risk_score)
            
            # Obter fatores de influência
            influence_factors = self._get_influence_factors(X.iloc[0])
            
            result = {
                'numero_apolice': policy_data.get('numero_apolice', 'N/A'),
                'risk_score': round(risk_score, 1),
                'risk_level': risk_level,
                'probability': round(probability, 3),
                'prediction': int(prediction),
                'influence_factors': influence_factors,
                'prediction_date': datetime.now().isoformat(),
                'model_confidence': self._calculate_confidence(probability)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na predição: {e}")
            return {
                'numero_apolice': policy_data.get('numero_apolice', 'N/A'),
                'error': str(e),
                'risk_score': 0,
                'risk_level': 'erro'
            }
    
    def predict_batch_policies(self, policies_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prediz risco para múltiplas apólices em lote
        
        Args:
            policies_data: Lista de dicionários com dados das apólices
            
        Returns:
            Lista de dicionários com scores de risco
        """
        if not self.is_loaded:
            self.load_model_and_preprocessors()
        
        results = []
        
        try:
            # Converter para DataFrame
            df = pd.DataFrame(policies_data)
            
            # Aplicar transformações
            X = self.feature_engineer.transform_new_data(df)
            
            # Fazer predições em lote
            probabilities = self.model.predict_proba(X)[:, 1]
            predictions = self.model.predict(X)
            
            # Processar resultados
            for i, policy in enumerate(policies_data):
                probability = probabilities[i]
                prediction = predictions[i]
                
                risk_score = self._probability_to_score(probability)
                risk_level = self._score_to_level(risk_score)
                
                result = {
                    'numero_apolice': policy.get('numero_apolice', f'Policy_{i}'),
                    'risk_score': round(risk_score, 1),
                    'risk_level': risk_level,
                    'probability': round(probability, 3),
                    'prediction': int(prediction),
                    'model_confidence': self._calculate_confidence(probability)
                }
                
                results.append(result)
            
            logger.info(f"Processadas {len(results)} predições em lote")
            
        except Exception as e:
            logger.error(f"Erro na predição em lote: {e}")
            # Retornar erro para cada apólice
            for policy in policies_data:
                results.append({
                    'numero_apolice': policy.get('numero_apolice', 'N/A'),
                    'error': str(e),
                    'risk_score': 0,
                    'risk_level': 'erro'
                })
        
        return results
    
    def predict_from_database(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Faz predições para apólices ativas do banco de dados
        
        Args:
            limit: Limitar número de apólices (opcional)
            
        Returns:
            Lista com predições
        """
        try:
            # Importar aqui para evitar dependência circular
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            from database import get_database, CRUDOperations
            
            # Buscar apólices ativas
            db = get_database()
            crud = CRUDOperations(db)
            
            # Buscar todas ou limitadas
            if limit:
                apolices = crud.get_apolices_by_region()[:limit]
            else:
                apolices = crud.get_apolices_by_region()
            
            if not apolices:
                logger.warning("Nenhuma apólice encontrada no banco")
                return []
            
            # Converter para formato de dicionário
            policies_data = []
            for apolice in apolices:
                policy_dict = {
                    'numero_apolice': apolice.numero_apolice,
                    'cep': apolice.cep,
                    'tipo_residencia': apolice.tipo_residencia,
                    'valor_segurado': apolice.valor_segurado,
                    'data_contratacao': apolice.data_contratacao.isoformat() if apolice.data_contratacao else None,
                    'latitude': apolice.latitude,
                    'longitude': apolice.longitude
                }
                policies_data.append(policy_dict)
            
            # Fazer predições
            results = self.predict_batch_policies(policies_data)
            
            # Salvar predições no banco (opcional)
            self._save_predictions_to_database(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Erro ao processar apólices do banco: {e}")
            return []
    
    def get_high_risk_policies(self, min_score: float = 70.0) -> List[Dict[str, Any]]:
        """
        Retorna apólices com alto risco
        
        Args:
            min_score: Score mínimo para considerar alto risco
            
        Returns:
            Lista de apólices de alto risco
        """
        all_predictions = self.predict_from_database()
        
        high_risk = [
            pred for pred in all_predictions 
            if pred.get('risk_score', 0) >= min_score and 'error' not in pred
        ]
        
        # Ordenar por score decrescente
        high_risk.sort(key=lambda x: x['risk_score'], reverse=True)
        
        logger.info(f"Encontradas {len(high_risk)} apólices com alto risco")
        return high_risk
    
    def _probability_to_score(self, probability: float) -> float:
        """Converte probabilidade (0-1) para score (0-100)"""
        # Aplicar transformação não-linear para melhor distribuição
        # Score = 100 * sqrt(probability) para dar mais peso a riscos altos
        score = 100 * np.sqrt(np.clip(probability, 0, 1))
        return np.clip(score, 0, 100)
    
    def _score_to_level(self, score: float) -> str:
        """Converte score numérico para nível de risco"""
        if score < self.risk_thresholds['baixo']:
            return 'baixo'
        elif score < self.risk_thresholds['medio']:
            return 'medio'
        elif score < self.risk_thresholds['alto']:
            return 'alto'
        else:
            return 'critico'
    
    def _calculate_confidence(self, probability: float) -> str:
        """Calcula nível de confiança da predição"""
        # Confiança baseada na distância do threshold 0.5
        distance_from_threshold = abs(probability - 0.5)
        
        if distance_from_threshold > 0.4:
            return 'alta'
        elif distance_from_threshold > 0.2:
            return 'media'
        else:
            return 'baixa'
    
    def _get_influence_factors(self, X_row: pd.Series) -> List[Dict[str, Any]]:
        """Identifica principais fatores que influenciam a predição"""
        try:
            # Obter feature importance do modelo
            feature_importance = dict(zip(
                self.feature_engineer.feature_columns,
                self.model.feature_importances_
            ))
            
            # Calcular contribuição de cada feature
            contributions = []
            for feature, value in X_row.items():
                importance = feature_importance.get(feature, 0)
                contribution = importance * abs(value)  # Valor normalizado
                
                contributions.append({
                    'feature': feature,
                    'value': round(float(value), 3),
                    'importance': round(importance, 3),
                    'contribution': round(contribution, 3)
                })
            
            # Ordenar por contribuição e retornar top 5
            contributions.sort(key=lambda x: x['contribution'], reverse=True)
            return contributions[:5]
            
        except Exception as e:
            logger.warning(f"Erro ao calcular fatores de influência: {e}")
            return []
    
    def _save_predictions_to_database(self, predictions: List[Dict[str, Any]]):
        """Salva predições no banco de dados"""
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            from database import get_database, CRUDOperations
            from database.models import PrevisaoRisco
            
            db = get_database()
            crud = CRUDOperations(db)
            
            # Buscar IDs das apólices
            for pred in predictions:
                if 'error' in pred:
                    continue
                
                numero_apolice = pred['numero_apolice']
                apolice = crud.get_apolice_by_numero(numero_apolice)
                
                if apolice:
                    previsao = PrevisaoRisco(
                        apolice_id=apolice.id,
                        data_previsao=datetime.now(),
                        score_risco=pred['risk_score'],
                        nivel_risco=pred['risk_level'],
                        fatores_risco=str(pred.get('influence_factors', [])),
                        modelo_versao='XGBoost_1.0'
                    )
                    
                    crud.insert_previsao(previsao)
            
            logger.info("Predições salvas no banco de dados")
            
        except Exception as e:
            logger.warning(f"Erro ao salvar predições no banco: {e}")
    
    def generate_risk_report(self) -> Dict[str, Any]:
        """Gera relatório consolidado de riscos"""
        try:
            predictions = self.predict_from_database()
            
            if not predictions:
                return {'error': 'Nenhuma predição disponível'}
            
            # Estatísticas gerais
            valid_predictions = [p for p in predictions if 'error' not in p]
            scores = [p['risk_score'] for p in valid_predictions]
            
            # Distribuição por nível
            level_distribution = {}
            for level in ['baixo', 'medio', 'alto', 'critico']:
                count = len([p for p in valid_predictions if p['risk_level'] == level])
                level_distribution[level] = count
            
            # Top 10 apólices de maior risco
            top_risk = sorted(valid_predictions, key=lambda x: x['risk_score'], reverse=True)[:10]
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'total_policies': len(predictions),
                'valid_predictions': len(valid_predictions),
                'statistics': {
                    'mean_score': round(np.mean(scores), 2) if scores else 0,
                    'median_score': round(np.median(scores), 2) if scores else 0,
                    'max_score': round(np.max(scores), 2) if scores else 0,
                    'min_score': round(np.min(scores), 2) if scores else 0
                },
                'distribution_by_level': level_distribution,
                'high_risk_count': len([s for s in scores if s >= 70]),
                'top_risk_policies': top_risk
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
            return {'error': str(e)}


# Exemplo de uso
if __name__ == "__main__":
    # Teste do sistema de predição
    try:
        predictor = ModelPredictor()
        
        # Teste com dados simulados
        test_policy = {
            'numero_apolice': 'TEST123',
            'cep': '01310-100',
            'tipo_residencia': 'casa',
            'valor_segurado': 350000,
            'data_contratacao': '2024-01-15'
        }
        
        # Fazer predição
        result = predictor.predict_single_policy(test_policy)
        print("Resultado da predição:")
        print(f"Score: {result['risk_score']}")
        print(f"Nível: {result['risk_level']}")
        
    except Exception as e:
        print(f"Erro no teste: {e}")
        print("Execute o treinamento do modelo primeiro.")
