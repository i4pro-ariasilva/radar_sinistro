"""
Sistema de Avaliação de Modelos para Radar de Sinistro

"""

import pandas as pd
import numpy as np
import joblib
import os
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Tuple
from datetime import datetime
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve, precision_recall_curve
)

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Classe para avaliação e monitoramento de modelos"""
    
    def __init__(self, model_dir: str = 'models'):
        self.model_dir = model_dir
        self.model = None
        self.feature_engineer = None
        self.evaluation_results = {}
    
    def load_model_and_preprocessors(self):
        """Carrega modelo e preprocessors para avaliação"""
        try:
            model_path = os.path.join(self.model_dir, 'radar_model.pkl')
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Modelo não encontrado: {model_path}")
            
            self.model = joblib.load(model_path)
            
            from .feature_engineering import FeatureEngineer
            self.feature_engineer = FeatureEngineer()
            self.feature_engineer.load_preprocessors(self.model_dir)
            
            logger.info("Modelo carregado para avaliação")
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            raise
    
    def evaluate_model_performance(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, Any]:
        """
        Avalia performance completa do modelo
        
        Args:
            X_test: Features de teste
            y_test: Labels de teste
            
        Returns:
            Dicionário com métricas de avaliação
        """
        if self.model is None:
            self.load_model_and_preprocessors()
        
        try:
            # Fazer predições
            y_pred = self.model.predict(X_test)
            y_prob = self.model.predict_proba(X_test)[:, 1]
            
            # Calcular métricas básicas
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='binary')
            recall = recall_score(y_test, y_pred, average='binary')
            f1 = f1_score(y_test, y_pred, average='binary')
            auc_roc = roc_auc_score(y_test, y_prob)
            
            # Matriz de confusão
            cm = confusion_matrix(y_test, y_pred)
            tn, fp, fn, tp = cm.ravel()
            
            # Métricas derivadas
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
            npv = tn / (tn + fn) if (tn + fn) > 0 else 0  # Negative Predictive Value
            
            # Relatório de classificação
            class_report = classification_report(
                y_test, y_pred, 
                target_names=['Sem Sinistro', 'Com Sinistro'],
                output_dict=True
            )
            
            # Distribuição de scores por classe
            score_distribution = self._analyze_score_distribution(y_test, y_prob)
            
            evaluation_results = {
                'timestamp': datetime.now().isoformat(),
                'dataset_info': {
                    'n_samples': len(y_test),
                    'n_features': X_test.shape[1],
                    'positive_rate': y_test.mean(),
                    'negative_rate': 1 - y_test.mean()
                },
                'basic_metrics': {
                    'accuracy': round(accuracy, 4),
                    'precision': round(precision, 4),
                    'recall': round(recall, 4),
                    'f1_score': round(f1, 4),
                    'specificity': round(specificity, 4),
                    'npv': round(npv, 4),
                    'auc_roc': round(auc_roc, 4)
                },
                'confusion_matrix': {
                    'true_negative': int(tn),
                    'false_positive': int(fp),
                    'false_negative': int(fn),
                    'true_positive': int(tp)
                },
                'classification_report': class_report,
                'score_distribution': score_distribution,
                'feature_importance': self._get_feature_importance_analysis()
            }
            
            self.evaluation_results = evaluation_results
            
            # Salvar resultados
            self._save_evaluation_results(evaluation_results)
            
            logger.info(f"Avaliação concluída - AUC: {auc_roc:.4f}, F1: {f1:.4f}")
            
            return evaluation_results
            
        except Exception as e:
            logger.error(f"Erro na avaliação: {e}")
            raise
    
    def evaluate_on_new_data(self, new_data_path: str = None) -> Dict[str, Any]:
        """
        Avalia modelo com novos dados (simulação de dados em produção)
        
        Args:
            new_data_path: Caminho para novos dados (opcional)
            
        Returns:
            Resultado da avaliação
        """
        try:
            if new_data_path and os.path.exists(new_data_path):
                # Carregar dados externos
                data = pd.read_csv(new_data_path)
            else:
                # Gerar dados simulados para teste
                data = self._generate_simulation_data()
            
            # Preparar dados
            if 'sinistro_ocorreu' in data.columns:
                y_true = data['sinistro_ocorreu']
                X = data.drop('sinistro_ocorreu', axis=1)
            else:
                # Se não há target, apenas fazer predições
                X = data
                y_true = None
            
            # Aplicar transformações
            if self.feature_engineer is None:
                self.load_model_and_preprocessors()
            
            X_processed = self.feature_engineer.transform_new_data(X)
            
            # Fazer predições
            y_pred = self.model.predict(X_processed)
            y_prob = self.model.predict_proba(X_processed)[:, 1]
            
            # Calcular scores de risco
            risk_scores = 100 * np.sqrt(np.clip(y_prob, 0, 1))
            
            results = {
                'timestamp': datetime.now().isoformat(),
                'n_samples': len(X),
                'predictions': {
                    'mean_risk_score': round(risk_scores.mean(), 2),
                    'median_risk_score': round(np.median(risk_scores), 2),
                    'max_risk_score': round(risk_scores.max(), 2),
                    'min_risk_score': round(risk_scores.min(), 2),
                    'high_risk_count': int((risk_scores >= 70).sum()),
                    'high_risk_percentage': round((risk_scores >= 70).mean() * 100, 2)
                },
                'risk_distribution': {
                    'baixo': int((risk_scores < 25).sum()),
                    'medio': int(((risk_scores >= 25) & (risk_scores < 50)).sum()),
                    'alto': int(((risk_scores >= 50) & (risk_scores < 75)).sum()),
                    'critico': int((risk_scores >= 75).sum())
                }
            }
            
            # Se temos labels verdadeiros, calcular métricas
            if y_true is not None:
                performance = self.evaluate_model_performance(X_processed, y_true)
                results['performance_metrics'] = performance['basic_metrics']
            
            return results
            
        except Exception as e:
            logger.error(f"Erro na avaliação com novos dados: {e}")
            return {'error': str(e)}
    
    def analyze_feature_importance(self, top_n: int = 15) -> Dict[str, Any]:
        """
        Analisa importância das features do modelo
        
        Args:
            top_n: Número de features mais importantes para retornar
            
        Returns:
            Análise de feature importance
        """
        if self.model is None:
            self.load_model_and_preprocessors()
        
        try:
            # Obter feature importance
            feature_names = self.feature_engineer.feature_columns
            importances = self.model.feature_importances_
            
            # Criar DataFrame ordenado
            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False)
            
            # Top features
            top_features = importance_df.head(top_n)
            
            # Categorizar features
            feature_categories = self._categorize_features(feature_names)
            
            # Importância por categoria
            category_importance = {}
            for category, features in feature_categories.items():
                cat_importance = importance_df[
                    importance_df['feature'].isin(features)
                ]['importance'].sum()
                category_importance[category] = round(cat_importance, 4)
            
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'total_features': len(feature_names),
                'top_features': [
                    {
                        'feature': row['feature'],
                        'importance': round(row['importance'], 4),
                        'percentage': round(row['importance'] / importances.sum() * 100, 2)
                    }
                    for _, row in top_features.iterrows()
                ],
                'category_importance': category_importance,
                'statistics': {
                    'mean_importance': round(importances.mean(), 4),
                    'std_importance': round(importances.std(), 4),
                    'top_10_contribution': round(
                        importance_df.head(10)['importance'].sum() / importances.sum() * 100, 2
                    )
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro na análise de feature importance: {e}")
            return {'error': str(e)}
    
    def monitor_model_drift(self, reference_data: pd.DataFrame, current_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Monitora drift do modelo comparando distribuições
        
        Args:
            reference_data: Dados de referência (treino)
            current_data: Dados atuais (produção)
            
        Returns:
            Análise de drift
        """
        try:
            # Processar ambos os datasets
            if self.feature_engineer is None:
                self.load_model_and_preprocessors()
            
            X_ref = self.feature_engineer.transform_new_data(reference_data)
            X_curr = self.feature_engineer.transform_new_data(current_data)
            
            # Calcular drift para cada feature
            feature_drift = {}
            for col in X_ref.columns:
                if col in X_curr.columns:
                    # KS test para detectar mudanças na distribuição
                    from scipy.stats import ks_2samp
                    ks_stat, p_value = ks_2samp(X_ref[col], X_curr[col])
                    
                    # Diferença nas médias
                    mean_diff = abs(X_curr[col].mean() - X_ref[col].mean())
                    mean_diff_pct = mean_diff / abs(X_ref[col].mean()) * 100 if X_ref[col].mean() != 0 else 0
                    
                    feature_drift[col] = {
                        'ks_statistic': round(ks_stat, 4),
                        'p_value': round(p_value, 4),
                        'significant_drift': p_value < 0.05,
                        'mean_difference': round(mean_diff, 4),
                        'mean_difference_pct': round(mean_diff_pct, 2)
                    }
            
            # Detectar features com drift significativo
            drifted_features = [
                feature for feature, stats in feature_drift.items()
                if stats['significant_drift']
            ]
            
            # Score geral de drift
            drift_scores = [stats['ks_statistic'] for stats in feature_drift.values()]
            overall_drift_score = np.mean(drift_scores)
            
            drift_analysis = {
                'timestamp': datetime.now().isoformat(),
                'overall_drift_score': round(overall_drift_score, 4),
                'drift_level': self._classify_drift_level(overall_drift_score),
                'features_with_drift': len(drifted_features),
                'total_features_analyzed': len(feature_drift),
                'drift_percentage': round(len(drifted_features) / len(feature_drift) * 100, 2),
                'drifted_features': drifted_features[:10],  # Top 10
                'feature_drift_details': {
                    k: v for k, v in sorted(
                        feature_drift.items(),
                        key=lambda x: x[1]['ks_statistic'],
                        reverse=True
                    )[:10]
                }
            }
            
            return drift_analysis
            
        except Exception as e:
            logger.error(f"Erro no monitoramento de drift: {e}")
            return {'error': str(e)}
    
    def generate_evaluation_report(self) -> str:
        """Gera relatório completo de avaliação em formato texto"""
        if not self.evaluation_results:
            return "Nenhuma avaliação disponível. Execute evaluate_model_performance() primeiro."
        
        results = self.evaluation_results
        
        report = f"""
=== RELATÓRIO DE AVALIAÇÃO DO MODELO ===
Gerado em: {results['timestamp']}

INFORMAÇÕES DO DATASET:
- Amostras: {results['dataset_info']['n_samples']:,}
- Features: {results['dataset_info']['n_features']}
- Taxa de Positivos: {results['dataset_info']['positive_rate']:.2%}

MÉTRICAS DE PERFORMANCE:
- Acurácia: {results['basic_metrics']['accuracy']:.2%}
- Precisão: {results['basic_metrics']['precision']:.2%}
- Recall: {results['basic_metrics']['recall']:.2%}
- F1-Score: {results['basic_metrics']['f1_score']:.4f}
- AUC-ROC: {results['basic_metrics']['auc_roc']:.4f}
- Especificidade: {results['basic_metrics']['specificity']:.2%}

MATRIZ DE CONFUSÃO:
                    Predito
                Não    Sim
Real    Não    {results['confusion_matrix']['true_negative']:4d}   {results['confusion_matrix']['false_positive']:4d}
        Sim    {results['confusion_matrix']['false_negative']:4d}   {results['confusion_matrix']['true_positive']:4d}

DISTRIBUIÇÃO DE SCORES:
- Sem Sinistro: Média {results['score_distribution']['class_0']['mean']:.2f} (±{results['score_distribution']['class_0']['std']:.2f})
- Com Sinistro: Média {results['score_distribution']['class_1']['mean']:.2f} (±{results['score_distribution']['class_1']['std']:.2f})

TOP 5 FEATURES MAIS IMPORTANTES:
"""
        
        if 'top_features' in results['feature_importance']:
            for i, feature in enumerate(results['feature_importance']['top_features'][:5], 1):
                report += f"{i}. {feature['feature']}: {feature['importance']:.4f} ({feature['percentage']:.1f}%)\n"
        
        return report
    
    def _analyze_score_distribution(self, y_true: pd.Series, y_prob: np.ndarray) -> Dict[str, Any]:
        """Analisa distribuição de scores por classe"""
        scores_0 = y_prob[y_true == 0]  # Sem sinistro
        scores_1 = y_prob[y_true == 1]  # Com sinistro
        
        return {
            'class_0': {
                'mean': round(scores_0.mean(), 4),
                'std': round(scores_0.std(), 4),
                'min': round(scores_0.min(), 4),
                'max': round(scores_0.max(), 4)
            },
            'class_1': {
                'mean': round(scores_1.mean(), 4),
                'std': round(scores_1.std(), 4),
                'min': round(scores_1.min(), 4),
                'max': round(scores_1.max(), 4)
            }
        }
    
    def _get_feature_importance_analysis(self) -> Dict[str, Any]:
        """Análise detalhada de feature importance"""
        try:
            return self.analyze_feature_importance()
        except:
            return {}
    
    def _categorize_features(self, feature_names: List[str]) -> Dict[str, List[str]]:
        """Categoriza features por tipo"""
        categories = {
            'geographic': [],
            'property': [],
            'temporal': [],
            'climate': [],
            'encoded': [],
            'other': []
        }
        
        for feature in feature_names:
            feature_lower = feature.lower()
            if any(geo in feature_lower for geo in ['lat', 'lng', 'distancia', 'regiao']):
                categories['geographic'].append(feature)
            elif any(prop in feature_lower for prop in ['valor', 'tipo', 'residencia']):
                categories['property'].append(feature)
            elif any(temp in feature_lower for temp in ['dias', 'ano', 'mes', 'tempo']):
                categories['temporal'].append(feature)
            elif any(clim in feature_lower for clim in ['temp', 'precip', 'vento', 'clima']):
                categories['climate'].append(feature)
            elif any(enc in feature_lower for enc in ['encoded', '_enc']):
                categories['encoded'].append(feature)
            else:
                categories['other'].append(feature)
        
        return categories
    
    def _classify_drift_level(self, drift_score: float) -> str:
        """Classifica nível de drift"""
        if drift_score > 0.5:
            return 'crítico'
        elif drift_score > 0.3:
            return 'alto'
        elif drift_score > 0.1:
            return 'moderado'
        else:
            return 'baixo'
    
    def _generate_simulation_data(self) -> pd.DataFrame:
        """Gera dados simulados para teste"""
        np.random.seed(42)
        n_samples = 1000
        
        # Dados básicos
        data = {
            'numero_apolice': [f'SIM_{i:04d}' for i in range(n_samples)],
            'cep': np.random.choice(['01310-100', '04038-001', '22071-900'], n_samples),
            'tipo_residencia': np.random.choice(['casa', 'apartamento'], n_samples),
            'valor_segurado': np.random.normal(400000, 150000, n_samples),
            'data_contratacao': pd.date_range('2023-01-01', periods=n_samples, freq='D')[:n_samples]
        }
        
        # Target simulado baseado em algumas regras
        risk_factors = []
        for i in range(n_samples):
            risk = 0
            if data['valor_segurado'][i] > 500000:
                risk += 0.3
            if data['tipo_residencia'][i] == 'casa':
                risk += 0.2
            if data['cep'][i] == '22071-900':  # Zona de risco
                risk += 0.4
            
            risk_factors.append(np.random.random() < risk)
        
        data['sinistro_ocorreu'] = risk_factors
        
        return pd.DataFrame(data)
    
    def _save_evaluation_results(self, results: Dict[str, Any]):
        """Salva resultados da avaliação"""
        try:
            results_path = os.path.join(self.model_dir, 'evaluation_results.json')
            
            import json
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Resultados salvos em: {results_path}")
            
        except Exception as e:
            logger.warning(f"Erro ao salvar resultados: {e}")


# Exemplo de uso
if __name__ == "__main__":
    try:
        evaluator = ModelEvaluator()
        
        # Avaliação com dados simulados
        evaluation = evaluator.evaluate_on_new_data()
        print("Avaliação em dados simulados:")
        print(f"Score médio de risco: {evaluation['predictions']['mean_risk_score']}")
        print(f"Políticas de alto risco: {evaluation['predictions']['high_risk_count']}")
        
        # Análise de feature importance
        importance = evaluator.analyze_feature_importance()
        print("\nTop 5 features mais importantes:")
        for feature in importance.get('top_features', [])[:5]:
            print(f"- {feature['feature']}: {feature['importance']:.4f}")
        
    except Exception as e:
        print(f"Erro no teste: {e}")
        print("Certifique-se de que o modelo foi treinado primeiro.")