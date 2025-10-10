#!/usr/bin/env python3
"""
Script para treinar modelos de cobertura com dados simulados.
Treina modelos RandomForest para cada tipo de cobertura usando dados sintéticos.
"""

import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import sys

# Adicionar ao path para imports
sys.path.append('.')

from src.ml.coverage_predictors.base_predictor import CoverageSpecificPredictor
from src.ml.coverage_predictors.danos_eletricos import DanosEletricosPredictor
from src.ml.coverage_predictors.vendaval import VendavalPredictor
from src.ml.coverage_predictors.granizo import GranizoPredictor
from src.ml.coverage_predictors.alagamento import AlagamentoPredictor

class CoverageModelTrainer:
    """Treina modelos específicos de cobertura com dados sintéticos"""
    
    def __init__(self):
        self.models = {
            'danos_eletricos': DanosEletricosPredictor(),
            'vendaval': VendavalPredictor(),
            'granizo': GranizoPredictor(),
            'alagamento': AlagamentoPredictor()
        }
        
        # Criar diretório para modelos treinados
        os.makedirs('models/trained', exist_ok=True)
        os.makedirs('models/reports', exist_ok=True)
    
    def prepare_features(self, df: pd.DataFrame, predictor: CoverageSpecificPredictor) -> tuple:
        """
        Prepara features para treinamento baseado nas features específicas do preditor
        """
        # Obter features relevantes do preditor
        climate_features = predictor.get_climate_features()
        property_features = predictor.get_property_features()
        
        # Combinar todas as features
        all_features = climate_features + property_features
        
        # Filtrar apenas features que existem no DataFrame
        available_features = [f for f in all_features if f in df.columns]
        
        if len(available_features) == 0:
            raise ValueError(f"Nenhuma feature relevante encontrada no dataset para {predictor.coverage_name}")
        
        print(f"  📊 Features selecionadas ({len(available_features)}): {available_features}")
        
        # Preparar dados
        X = df[available_features].copy()
        y = df['sinistro_ocorreu'].copy()
        
        # Tratar valores categóricos
        label_encoders = {}
        for col in X.columns:
            if X[col].dtype == 'object':
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
                label_encoders[col] = le
        
        # Tratar valores ausentes
        X = X.fillna(X.median())
        
        return X, y, available_features, label_encoders
    
    def train_model(self, coverage_type: str, test_size: float = 0.2) -> dict:
        """
        Treina modelo para uma cobertura específica
        
        Args:
            coverage_type: Tipo de cobertura
            test_size: Proporção dos dados para teste
        
        Returns:
            Dicionário com métricas de performance
        """
        
        print(f"\n🔄 Treinando modelo para {coverage_type}...")
        
        # Carregar dataset
        data_path = f'data/training/{coverage_type}_training_data.csv'
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Dataset não encontrado: {data_path}")
        
        df = pd.read_csv(data_path)
        print(f"  📋 Dataset carregado: {len(df)} amostras")
        print(f"  ⚖️ Balanceamento: {df['sinistro_ocorreu'].mean():.1%} sinistros")
        
        # Obter preditor específico
        predictor = self.models[coverage_type]
        
        # Preparar features
        X, y, feature_names, label_encoders = self.prepare_features(df, predictor)
        
        # Dividir dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        print(f"  🔨 Dados de treino: {len(X_train)} amostras")
        print(f"  🧪 Dados de teste: {len(X_test)} amostras")
        
        # Treinar modelo
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            class_weight='balanced'  # Lidar com desbalanceamento
        )
        
        print("  🤖 Treinando RandomForest...")
        model.fit(X_train, y_train)
        
        # Avaliar modelo
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Métricas
        accuracy = model.score(X_test, y_test)
        auc_score = roc_auc_score(y_test, y_pred_proba)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='roc_auc')
        
        print(f"  ✅ Acurácia: {accuracy:.3f}")
        print(f"  📈 AUC-ROC: {auc_score:.3f}")
        print(f"  🔄 CV AUC (média): {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        # Importância das features
        feature_importance = dict(zip(feature_names, model.feature_importances_))
        
        # Atualizar preditor com modelo treinado
        predictor.model = model
        predictor.scaler = StandardScaler()  # Criar novo scaler
        predictor.scaler.fit(X_train)  # Treinar o scaler
        predictor.feature_importance = feature_importance
        predictor.label_encoders = label_encoders
        predictor.is_trained = True
        
        # Salvar modelo
        predictor.save_model()
        
        # Gerar relatório detalhado
        report = self._generate_detailed_report(
            coverage_type, model, X_test, y_test, y_pred, y_pred_proba, 
            feature_names, feature_importance, cv_scores
        )
        
        return {
            'coverage_type': coverage_type,
            'accuracy': accuracy,
            'auc_score': auc_score,
            'cv_scores': cv_scores,
            'feature_importance': feature_importance,
            'n_train_samples': len(X_train),
            'n_test_samples': len(X_test),
            'report': report
        }
    
    def _generate_detailed_report(self, coverage_type: str, model, X_test, y_test, 
                                y_pred, y_pred_proba, feature_names, 
                                feature_importance, cv_scores) -> str:
        """Gera relatório detalhado do modelo"""
        
        report_lines = []
        report_lines.append(f"RELATÓRIO DE TREINAMENTO - {coverage_type.upper()}")
        report_lines.append("=" * 60)
        report_lines.append(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Métricas gerais
        report_lines.append("MÉTRICAS DE PERFORMANCE:")
        report_lines.append(f"Acurácia: {model.score(X_test, y_test):.3f}")
        report_lines.append(f"AUC-ROC: {roc_auc_score(y_test, y_pred_proba):.3f}")
        report_lines.append(f"Cross-Validation AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        report_lines.append("")
        
        # Relatório de classificação
        report_lines.append("RELATÓRIO DE CLASSIFICAÇÃO:")
        class_report = classification_report(y_test, y_pred)
        report_lines.append(class_report)
        report_lines.append("")
        
        # Matriz de confusão
        report_lines.append("MATRIZ DE CONFUSÃO:")
        cm = confusion_matrix(y_test, y_pred)
        report_lines.append(f"TN: {cm[0,0]}, FP: {cm[0,1]}")
        report_lines.append(f"FN: {cm[1,0]}, TP: {cm[1,1]}")
        report_lines.append("")
        
        # Importância das features
        report_lines.append("IMPORTÂNCIA DAS FEATURES:")
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        for i, (feature, importance) in enumerate(sorted_features[:15]):  # Top 15
            report_lines.append(f"{i+1:2d}. {feature:<25} {importance:.4f}")
        report_lines.append("")
        
        # Estatísticas dos dados
        report_lines.append("ESTATÍSTICAS DOS DADOS:")
        report_lines.append(f"Total de amostras de teste: {len(X_test)}")
        report_lines.append(f"Classe positiva (sinistros): {y_test.sum()} ({y_test.mean():.1%})")
        report_lines.append(f"Classe negativa (sem sinistro): {(y_test == 0).sum()} ({(y_test == 0).mean():.1%})")
        report_lines.append("")
        
        # Distribuição de probabilidades preditas
        report_lines.append("DISTRIBUIÇÃO DE PROBABILIDADES:")
        prob_bins = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        prob_hist, _ = np.histogram(y_pred_proba, bins=prob_bins)
        for i in range(len(prob_bins)-1):
            report_lines.append(f"{prob_bins[i]:.1f}-{prob_bins[i+1]:.1f}: {prob_hist[i]} amostras")
        
        report_content = "\n".join(report_lines)
        
        # Salvar relatório
        report_path = f'models/reports/{coverage_type}_training_report.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"  📄 Relatório salvo em: {report_path}")
        
        return report_content
    
    def train_all_models(self) -> dict:
        """Treina modelos para todas as coberturas"""
        
        print("🚀 INICIANDO TREINAMENTO DE TODOS OS MODELOS\n")
        
        results = {}
        coverages = ['danos_eletricos', 'vendaval', 'granizo', 'alagamento']
        
        for coverage in coverages:
            try:
                result = self.train_model(coverage)
                results[coverage] = result
                print(f"✅ {coverage} treinado com sucesso!")
                
            except Exception as e:
                print(f"❌ Erro ao treinar {coverage}: {e}")
                results[coverage] = {'error': str(e)}
        
        # Gerar sumário geral
        self._generate_summary_report(results)
        
        return results
    
    def _generate_summary_report(self, results: dict):
        """Gera relatório sumário de todos os modelos"""
        
        summary_lines = []
        summary_lines.append("SUMÁRIO DE TREINAMENTO - TODOS OS MODELOS")
        summary_lines.append("=" * 60)
        summary_lines.append(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append("")
        
        total_models = len(results)
        successful_models = sum(1 for r in results.values() if 'error' not in r)
        
        summary_lines.append(f"RESUMO GERAL:")
        summary_lines.append(f"Total de modelos: {total_models}")
        summary_lines.append(f"Treinados com sucesso: {successful_models}")
        summary_lines.append(f"Com erro: {total_models - successful_models}")
        summary_lines.append("")
        
        summary_lines.append("PERFORMANCE POR MODELO:")
        summary_lines.append(f"{'Cobertura':<20} {'Acurácia':<10} {'AUC-ROC':<10} {'CV AUC':<15} {'Amostras':<10}")
        summary_lines.append("-" * 70)
        
        for coverage, result in results.items():
            if 'error' not in result:
                cv_mean = result['cv_scores'].mean()
                summary_lines.append(
                    f"{coverage:<20} {result['accuracy']:<10.3f} "
                    f"{result['auc_score']:<10.3f} {cv_mean:<15.3f} "
                    f"{result['n_train_samples']:<10}"
                )
            else:
                summary_lines.append(f"{coverage:<20} {'ERRO':<10} {'-':<10} {'-':<15} {'-':<10}")
        
        summary_lines.append("")
        summary_lines.append("TOP 5 FEATURES MAIS IMPORTANTES (geral):")
        
        # Agregar importância de features
        all_features = {}
        for coverage, result in results.items():
            if 'error' not in result:
                for feature, importance in result['feature_importance'].items():
                    if feature not in all_features:
                        all_features[feature] = []
                    all_features[feature].append(importance)
        
        # Calcular importância média
        avg_importance = {f: np.mean(imp) for f, imp in all_features.items()}
        top_features = sorted(avg_importance.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for i, (feature, importance) in enumerate(top_features):
            summary_lines.append(f"{i+1}. {feature:<25} {importance:.4f}")
        
        summary_content = "\n".join(summary_lines)
        
        # Salvar sumário
        summary_path = 'models/reports/training_summary.txt'
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        print(f"\n📊 Sumário geral salvo em: {summary_path}")

def main():
    """Função principal para executar o treinamento"""
    
    print("🤖 SISTEMA DE TREINAMENTO DE MODELOS DE COBERTURA")
    print("=" * 55)
    print()
    
    # Verificar se os datasets existem
    coverages = ['danos_eletricos', 'vendaval', 'granizo', 'alagamento']
    missing_datasets = []
    
    for coverage in coverages:
        data_path = f'data/training/{coverage}_training_data.csv'
        if not os.path.exists(data_path):
            missing_datasets.append(coverage)
    
    if missing_datasets:
        print("❌ Datasets não encontrados para:")
        for dataset in missing_datasets:
            print(f"   - {dataset}")
        print("\n💡 Execute primeiro o gerador de dados:")
        print("   python src/ml/data_simulator.py")
        return
    
    # Iniciar treinamento
    trainer = CoverageModelTrainer()
    results = trainer.train_all_models()
    
    print("\n🎉 TREINAMENTO CONCLUÍDO!")
    print("\n📋 Resumo dos resultados:")
    
    for coverage, result in results.items():
        if 'error' not in result:
            print(f"✅ {coverage}: AUC = {result['auc_score']:.3f}")
        else:
            print(f"❌ {coverage}: {result['error']}")
    
    print(f"\n📁 Modelos salvos em: models/")
    print(f"📄 Relatórios em: models/reports/")

if __name__ == "__main__":
    main()
