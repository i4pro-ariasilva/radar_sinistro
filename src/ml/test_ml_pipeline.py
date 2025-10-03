"""
Script de Teste Integrado para o Sistema ML


Este script testa todo o pipeline de Machine Learning:
1. Feature Engineering
2. Model Training  
3. Model Prediction
4. Model Evaluation
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar diretórios ao path para imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

def generate_sample_data(n_samples: int = 1000) -> pd.DataFrame:
    """Gera dados de amostra para teste do pipeline"""
    logger.info(f"Gerando {n_samples} amostras de dados para teste")
    
    np.random.seed(42)
    
    # Gerar dados simulados realistas
    data = []
    
    for i in range(n_samples):
        # Dados básicos da apólice
        apolice = {
            'numero_apolice': f'TEST_{i:06d}',
            'cep': np.random.choice([
                '01310-100', '04038-001', '22071-900', '30112-000', 
                '40070-110', '51020-230', '70040-010', '80230-130'
            ]),
            'tipo_residencia': np.random.choice(['casa', 'apartamento'], p=[0.6, 0.4]),
            'valor_segurado': np.random.normal(400000, 200000),
            'data_contratacao': datetime.now() - timedelta(days=np.random.randint(1, 1095))
        }
        
        # Garantir valores positivos
        apolice['valor_segurado'] = max(100000, apolice['valor_segurado'])
        
        # Adicionar coordenadas simuladas baseadas no CEP
        cep_coords = {
            '01310-100': (-23.5505, -46.6333),  # São Paulo - Centro
            '04038-001': (-23.5629, -46.6544),  # São Paulo - Vila Olímpia
            '22071-900': (-22.9068, -43.1729),  # Rio de Janeiro - Copacabana
            '30112-000': (-19.9167, -43.9345),  # Belo Horizonte - Centro
            '40070-110': (-12.9714, -38.5014),  # Salvador - Centro
            '51020-230': (-8.0476, -34.8770),   # Recife - Boa Viagem
            '70040-010': (-15.7942, -47.8822),  # Brasília - Asa Norte
            '80230-130': (-25.4284, -49.2733)   # Curitiba - Centro
        }
        
        base_lat, base_lng = cep_coords.get(apolice['cep'], (-23.5505, -46.6333))
        apolice['latitude'] = base_lat + np.random.normal(0, 0.01)
        apolice['longitude'] = base_lng + np.random.normal(0, 0.01)
        
        # Simular ocorrência de sinistro baseado em fatores de risco
        risk_score = 0
        
        # Fator: valor segurado alto
        if apolice['valor_segurado'] > 600000:
            risk_score += 0.3
        elif apolice['valor_segurado'] > 400000:
            risk_score += 0.1
            
        # Fator: tipo de residência
        if apolice['tipo_residencia'] == 'casa':
            risk_score += 0.2
            
        # Fator: região (baseado no CEP)
        high_risk_ceps = ['22071-900', '40070-110']  # Rio e Salvador
        if apolice['cep'] in high_risk_ceps:
            risk_score += 0.3
            
        # Fator: tempo de contrato (novos contratos = mais risco)
        days_since_contract = (datetime.now() - apolice['data_contratacao']).days
        if days_since_contract < 180:
            risk_score += 0.2
        elif days_since_contract < 365:
            risk_score += 0.1
            
        # Adicionar ruído aleatório
        risk_score += np.random.normal(0, 0.1)
        risk_score = np.clip(risk_score, 0, 1)
        
        # Determinar se houve sinistro
        apolice['sinistro_ocorreu'] = np.random.random() < risk_score
        
        data.append(apolice)
    
    df = pd.DataFrame(data)
    
    # Converter data para string ISO
    df['data_contratacao'] = df['data_contratacao'].dt.strftime('%Y-%m-%d')
    
    logger.info(f"Dados gerados: {len(df)} amostras, {df['sinistro_ocorreu'].mean():.2%} com sinistro")
    
    return df

def test_feature_engineering():
    """Testa o módulo de feature engineering"""
    logger.info("=== TESTE: Feature Engineering ===")
    
    try:
        from ml.feature_engineering import FeatureEngineer
        
        # Gerar dados de teste
        data = generate_sample_data(500)
        
        # Inicializar feature engineer
        feature_engineer = FeatureEngineer()
        
        # Preparar dados
        X, y = feature_engineer.prepare_features(data)
        
        logger.info(f"Features criadas: {X.shape[1]} colunas, {X.shape[0]} linhas")
        logger.info(f"Distribuição target: {y.mean():.2%} positivos")
        logger.info(f"Primeiras 5 features: {list(X.columns[:5])}")
        
        return feature_engineer, X, y
        
    except Exception as e:
        logger.error(f"Erro no teste de feature engineering: {e}")
        raise

def test_model_training(feature_engineer, X, y):
    """Testa o treinamento do modelo"""
    logger.info("=== TESTE: Model Training ===")
    
    try:
        from ml.model_trainer import ModelTrainer
        
        # Inicializar trainer
        trainer = ModelTrainer()
        
        # Treinar modelo
        logger.info("Iniciando treinamento...")
        results = trainer.train_model(X, y)
        
        logger.info(f"Treinamento concluído!")
        logger.info(f"Acurácia: {results['test_metrics']['accuracy']:.4f}")
        logger.info(f"F1-Score: {results['test_metrics']['f1_score']:.4f}")
        logger.info(f"AUC-ROC: {results['test_metrics']['auc_roc']:.4f}")
        
        return trainer, results
        
    except Exception as e:
        logger.error(f"Erro no teste de treinamento: {e}")
        raise

def test_model_prediction():
    """Testa o sistema de predições"""
    logger.info("=== TESTE: Model Prediction ===")
    
    try:
        from ml.model_predictor import ModelPredictor
        
        # Inicializar predictor
        predictor = ModelPredictor()
        
        # Dados de teste para predição
        test_policies = [
            {
                'numero_apolice': 'PRED_001',
                'cep': '22071-900',  # Rio - zona de risco
                'tipo_residencia': 'casa',
                'valor_segurado': 800000,  # Alto valor
                'data_contratacao': '2024-01-15'
            },
            {
                'numero_apolice': 'PRED_002', 
                'cep': '01310-100',  # São Paulo - centro
                'tipo_residencia': 'apartamento',
                'valor_segurado': 300000,  # Valor médio
                'data_contratacao': '2022-05-10'
            },
            {
                'numero_apolice': 'PRED_003',
                'cep': '30112-000',  # BH
                'tipo_residencia': 'apartamento', 
                'valor_segurado': 200000,  # Baixo valor
                'data_contratacao': '2021-03-20'
            }
        ]
        
        # Testar predição individual
        logger.info("Testando predições individuais:")
        for policy in test_policies:
            result = predictor.predict_single_policy(policy)
            
            if 'error' not in result:
                logger.info(f"Apólice {result['numero_apolice']}: "
                          f"Score {result['risk_score']:.1f} ({result['risk_level']})")
            else:
                logger.warning(f"Erro na predição: {result['error']}")
        
        # Testar predição em lote
        logger.info("Testando predição em lote...")
        batch_results = predictor.predict_batch_policies(test_policies)
        
        valid_results = [r for r in batch_results if 'error' not in r]
        if valid_results:
            avg_score = np.mean([r['risk_score'] for r in valid_results])
            logger.info(f"Predições em lote: {len(valid_results)} sucessos, score médio: {avg_score:.1f}")
        
        return predictor, batch_results
        
    except Exception as e:
        logger.error(f"Erro no teste de predição: {e}")
        raise

def test_model_evaluation():
    """Testa o sistema de avaliação"""
    logger.info("=== TESTE: Model Evaluation ===")
    
    try:
        from ml.model_evaluator import ModelEvaluator
        
        # Inicializar evaluator
        evaluator = ModelEvaluator()
        
        # Testar avaliação com dados simulados
        logger.info("Avaliando com dados simulados...")
        evaluation = evaluator.evaluate_on_new_data()
        
        if 'error' not in evaluation:
            logger.info(f"Amostras avaliadas: {evaluation['n_samples']}")
            logger.info(f"Score médio: {evaluation['predictions']['mean_risk_score']:.1f}")
            logger.info(f"Alto risco: {evaluation['predictions']['high_risk_count']} "
                       f"({evaluation['predictions']['high_risk_percentage']:.1f}%)")
            
            # Distribuição por nível
            dist = evaluation['risk_distribution']
            logger.info(f"Distribuição: Baixo={dist['baixo']}, Médio={dist['medio']}, "
                       f"Alto={dist['alto']}, Crítico={dist['critico']}")
        else:
            logger.warning(f"Erro na avaliação: {evaluation['error']}")
        
        # Testar análise de feature importance
        logger.info("Analisando importância das features...")
        importance = evaluator.analyze_feature_importance()
        
        if 'error' not in importance:
            logger.info("Top 5 features mais importantes:")
            for i, feature in enumerate(importance.get('top_features', [])[:5], 1):
                logger.info(f"{i}. {feature['feature']}: {feature['importance']:.4f} "
                           f"({feature['percentage']:.1f}%)")
        
        return evaluator, evaluation
        
    except Exception as e:
        logger.error(f"Erro no teste de avaliação: {e}")
        raise

def run_full_pipeline_test():
    """Executa teste completo do pipeline ML"""
    logger.info("=" * 60)
    logger.info("INICIANDO TESTE COMPLETO DO PIPELINE ML")
    logger.info("=" * 60)
    
    try:
        # 1. Feature Engineering
        feature_engineer, X, y = test_feature_engineering()
        
        # 2. Model Training
        trainer, training_results = test_model_training(feature_engineer, X, y)
        
        # 3. Model Prediction  
        predictor, prediction_results = test_model_prediction()
        
        # 4. Model Evaluation
        evaluator, evaluation_results = test_model_evaluation()
        
        # Resumo final
        logger.info("=" * 60)
        logger.info("RESUMO DO TESTE COMPLETO")
        logger.info("=" * 60)
        logger.info("✅ Feature Engineering: Sucesso")
        logger.info("✅ Model Training: Sucesso") 
        logger.info("✅ Model Prediction: Sucesso")
        logger.info("✅ Model Evaluation: Sucesso")
        logger.info("")
        logger.info("Sistema ML está funcionando corretamente!")
        
        return True
        
    except Exception as e:
        logger.error(f"Falha no pipeline: {e}")
        logger.error("Sistema ML precisa de correções.")
        return False

def test_individual_components():
    """Testa componentes individualmente para debugging"""
    logger.info("=== TESTE INDIVIDUAL DE COMPONENTES ===")
    
    results = {
        'feature_engineering': False,
        'model_training': False, 
        'model_prediction': False,
        'model_evaluation': False
    }
    
    # Teste 1: Feature Engineering
    try:
        logger.info("Testando Feature Engineering...")
        feature_engineer, X, y = test_feature_engineering()
        results['feature_engineering'] = True
        logger.info("✅ Feature Engineering OK")
    except Exception as e:
        logger.error(f"❌ Feature Engineering falhou: {e}")
    
    # Teste 2: Model Training (apenas se feature engineering funcionou)
    if results['feature_engineering']:
        try:
            logger.info("Testando Model Training...")
            trainer, training_results = test_model_training(feature_engineer, X, y)
            results['model_training'] = True
            logger.info("✅ Model Training OK")
        except Exception as e:
            logger.error(f"❌ Model Training falhou: {e}")
    
    # Teste 3: Model Prediction (apenas se training funcionou)
    if results['model_training']:
        try:
            logger.info("Testando Model Prediction...")
            predictor, prediction_results = test_model_prediction()
            results['model_prediction'] = True
            logger.info("✅ Model Prediction OK")
        except Exception as e:
            logger.error(f"❌ Model Prediction falhou: {e}")
    
    # Teste 4: Model Evaluation (sempre testar)
    try:
        logger.info("Testando Model Evaluation...")
        evaluator, evaluation_results = test_model_evaluation()
        results['model_evaluation'] = True
        logger.info("✅ Model Evaluation OK")
    except Exception as e:
        logger.error(f"❌ Model Evaluation falhou: {e}")
    
    # Resumo
    logger.info("\n=== RESULTADO DOS TESTES ===")
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        logger.info(f"{status_icon} {component}: {'OK' if status else 'FALHOU'}")
    
    success_rate = sum(results.values()) / len(results) * 100
    logger.info(f"\nTaxa de sucesso: {success_rate:.0f}%")
    
    return results

if __name__ == "__main__":
    logger.info("Iniciando teste do sistema ML...")
    
    # Escolher tipo de teste
    test_type = input("Escolha o tipo de teste:\n1. Pipeline completo\n2. Componentes individuais\nOpção (1-2): ").strip()
    
    if test_type == "1":
        success = run_full_pipeline_test()
        if success:
            print("\n🎉 Pipeline ML testado com sucesso!")
        else:
            print("\n⚠️ Pipeline ML tem problemas que precisam ser corrigidos.")
    
    elif test_type == "2":
        results = test_individual_components()
        working_components = sum(results.values())
        total_components = len(results)
        print(f"\n📊 {working_components}/{total_components} componentes funcionando.")
    
    else:
        logger.info("Executando teste individual por padrão...")
        test_individual_components()