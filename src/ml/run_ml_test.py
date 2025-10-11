"""
Script para Executar e Testar o Módulo ML

Este script resolve os problemas de imports e executa o pipeline ML completo.
"""

import sys
import os
import traceback
from pathlib import Path

def setup_python_path():
    """Configura o PYTHONPATH para resolver imports"""
    # Obter diretório raiz do projeto
    current_dir = Path(__file__).parent.absolute()
    project_root = current_dir.parent.parent  # radar_sinistro/
    src_dir = project_root / 'src'
    
    # Adicionar diretórios ao Python path
    paths_to_add = [
        str(project_root),
        str(src_dir),
        str(src_dir / 'ml'),
        str(src_dir / 'database'),
        str(src_dir / 'data_processing')
    ]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    print(f"✅ Python path configurado:")
    for path in paths_to_add:
        print(f"   - {path}")

def test_imports():
    """Testa se todos os imports funcionam"""
    print("\n🔍 Testando imports dos módulos ML...")
    
    import_tests = []
    
    # Teste 1: Feature Engineering
    try:
        from feature_engineering import FeatureEngineer
        import_tests.append(("FeatureEngineer", True, None))
        print("✅ FeatureEngineer importado com sucesso")
    except Exception as e:
        import_tests.append(("FeatureEngineer", False, str(e)))
        print(f"❌ Erro ao importar FeatureEngineer: {e}")
    
    # Teste 2: Model Trainer
    try:
        from model_trainer import ModelTrainer
        import_tests.append(("ModelTrainer", True, None))
        print("✅ ModelTrainer importado com sucesso")
    except Exception as e:
        import_tests.append(("ModelTrainer", False, str(e)))
        print(f"❌ Erro ao importar ModelTrainer: {e}")
    
    # Teste 3: Model Predictor
    try:
        from model_predictor import ModelPredictor
        import_tests.append(("ModelPredictor", True, None))
        print("✅ ModelPredictor importado com sucesso")
    except Exception as e:
        import_tests.append(("ModelPredictor", False, str(e)))
        print(f"❌ Erro ao importar ModelPredictor: {e}")
    
    # Teste 4: Model Evaluator
    try:
        from model_evaluator import ModelEvaluator
        import_tests.append(("ModelEvaluator", True, None))
        print("✅ ModelEvaluator importado com sucesso")
    except Exception as e:
        import_tests.append(("ModelEvaluator", False, str(e)))
        print(f"❌ Erro ao importar ModelEvaluator: {e}")
    
    # Resumo dos imports
    successful_imports = sum(1 for _, success, _ in import_tests if success)
    total_imports = len(import_tests)
    
    print(f"\n📊 Resultado dos imports: {successful_imports}/{total_imports} sucessos")
    
    return import_tests

def run_basic_ml_test():
    """Executa teste básico do sistema ML"""
    print("\n🧪 Executando teste básico do sistema ML...")
    
    try:
        # Imports necessários
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        from feature_engineering import FeatureEngineer
        from model_trainer import ModelTrainer
        
        print("✅ Imports básicos carregados")
        
        # Gerar dados de teste simples
        print("\n📊 Gerando dados de teste...")
        np.random.seed(42)
        
        n_samples = 100
        test_data = []
        
        for i in range(n_samples):
            sample = {
                'numero_apolice': f'TEST_{i:03d}',
                'cep': np.random.choice(['01310-100', '22071-900', '30112-000']),
                'tipo_residencia': np.random.choice(['casa', 'apartamento']),
                'valor_segurado': np.random.normal(400000, 100000),
                'data_contratacao': (datetime.now() - timedelta(days=np.random.randint(1, 365))).strftime('%Y-%m-%d'),
                'latitude': -23.5 + np.random.normal(0, 0.1),
                'longitude': -46.6 + np.random.normal(0, 0.1),
                'sinistro_ocorreu': np.random.choice([0, 1], p=[0.8, 0.2])
            }
            test_data.append(sample)
        
        df = pd.DataFrame(test_data)
        print(f"✅ Dados gerados: {len(df)} amostras")
        
        # Teste Feature Engineering
        print("\n🔧 Testando Feature Engineering...")
        feature_engineer = FeatureEngineer()
        features_df = feature_engineer.create_features(df)
        
        # Separar features e target
        target_col = 'houve_sinistro'  # Nome correto do target
        y = features_df[target_col]
        X = features_df.drop(columns=[target_col])
        
        # Debug: mostrar tipos de dados
        print(f"   Colunas X: {list(X.columns)}")
        print(f"   Tipos de dados:")
        for col in X.columns:
            print(f"     {col}: {X[col].dtype}")
        
        # Filtrar apenas colunas numéricas para o XGBoost
        numeric_cols = X.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns
        X = X[numeric_cols]
        
        print(f"✅ Features preparadas: {X.shape[1]} colunas numéricas, {X.shape[0]} linhas")
        print(f"   Distribuição target: {y.mean():.1%} positivos")
        
        # Teste Model Training (versão simplificada)
        print("\n🎯 Testando Model Training...")
        trainer = ModelTrainer()
        
        # Dividir dados em treino e teste
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Treinamento para teste
        results = trainer.train_model(X_train, X_test, y_train, y_test)
        
        print(f"✅ Modelo treinado com sucesso!")
        print(f"   Resultados disponíveis: {list(results.keys())}")
        
        # Tentar acessar métricas de diferentes formas
        if 'test_metrics' in results:
            print(f"   Acurácia: {results['test_metrics']['accuracy']:.3f}")
            print(f"   F1-Score: {results['test_metrics']['f1_score']:.3f}")
        elif 'accuracy' in results:
            print(f"   Acurácia: {results['accuracy']:.3f}")
        else:
            print(f"   Métricas: {results}")
        
        # Verificar se modelo foi salvo
        model_path = os.path.join('models', 'radar_model.pkl')
        if os.path.exists(model_path):
            print(f"✅ Modelo salvo em: {model_path}")
        
        print("\n🎉 Teste básico do ML concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro no teste básico: {e}")
        print("\nDetalhes do erro:")
        traceback.print_exc()
        return False

def run_prediction_test():
    """Testa sistema de predições"""
    print("\n🔮 Testando sistema de predições...")
    
    try:
        from model_predictor import ModelPredictor
        
        # Verificar se modelo existe
        model_path = os.path.join('models', 'radar_model.pkl')
        if not os.path.exists(model_path):
            print("⚠️ Modelo não encontrado. Execute o treinamento primeiro.")
            return False
        
        # Inicializar predictor
        predictor = ModelPredictor()
        
        # Dados de teste para predição
        test_policy = {
            'numero_apolice': 'PRED_TEST_001',
            'cep': '22071-900',  # Rio - zona de risco
            'tipo_residencia': 'casa',
            'valor_segurado': 500000,
            'data_contratacao': '2024-01-15',
            'latitude': -22.9068,
            'longitude': -43.1729
        }
        
        # Fazer predição
        result = predictor.predict_single_policy(test_policy)
        
        if 'error' not in result:
            print(f"✅ Predição realizada:")
            print(f"   Apólice: {result['numero_apolice']}")
            print(f"   Score de Risco: {result['risk_score']:.1f}")
            print(f"   Nível: {result['risk_level']}")
            print(f"   Confiança: {result['model_confidence']}")
            return True
        else:
            print(f"❌ Erro na predição: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de predição: {e}")
        traceback.print_exc()
        return False

def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    print("\n📦 Verificando dependências...")
    
    # Mapeamento correto de nomes de pacotes
    required_packages = {
        'pandas': 'pandas',
        'numpy': 'numpy', 
        'sklearn': 'scikit-learn',  # sklearn é o nome de import do scikit-learn
        'xgboost': 'xgboost',
        'joblib': 'joblib',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn'
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - NÃO INSTALADO")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n⚠️ Pacotes faltando: {', '.join(missing_packages)}")
        print("Execute: pip install " + " ".join(missing_packages))
        return False
    else:
        print("\n✅ Todas as dependências estão instaladas!")
        return True

def create_models_directory():
    """Cria diretório models se não existir"""
    models_dir = Path('models')
    if not models_dir.exists():
        models_dir.mkdir(exist_ok=True)
        print(f"✅ Diretório 'models' criado")
    else:
        print(f"✅ Diretório 'models' já existe")

def main():
    """Função principal"""
    print("=" * 60)
    print("🚀 TESTE DO SISTEMA ML - RADAR DE SINISTRO")
    print("=" * 60)
    
    # 1. Configurar environment
    setup_python_path()
    
    # 2. Verificar dependências
    if not check_dependencies():
        print("\n❌ Instale as dependências primeiro!")
        return
    
    # 3. Criar diretório models
    create_models_directory()
    
    # 4. Testar imports
    import_results = test_imports()
    successful_imports = sum(1 for _, success, _ in import_results if success)
    
    if successful_imports < 4:
        print(f"\n⚠️ Apenas {successful_imports}/4 módulos importados com sucesso")
        print("Verifique os erros de import acima.")
        return
    
    # 5. Executar teste básico
    if run_basic_ml_test():
        print("\n✅ Sistema ML básico funcionando!")
        
        # 6. Testar predições
        if run_prediction_test():
            print("\n🎉 Sistema completo de ML testado com sucesso!")
        else:
            print("\n⚠️ Sistema de predições precisa de ajustes.")
    else:
        print("\n❌ Sistema ML tem problemas que precisam ser corrigidos.")
    
    print("\n" + "=" * 60)
    print("✅ Teste concluído!")

if __name__ == "__main__":
    main()
