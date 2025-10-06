"""
RADAR DE SINISTRO - Sistema Principal v3.0
==========================================

Sistema completo de análise de risco de sinistros com:
- Dados climáticos reais (OpenMeteo API)
- Machine Learning com XGBoost
- Feature Engineering avançado  
- Cache inteligente
- Pipeline completo de treinamento/predição

Versão: 3.0 - Compatibilidade Windows
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Adicionar diretório raiz ao Python path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Configurar logging sem emojis para compatibilidade Windows
def setup_logging():
    """Configura sistema de logging"""
    log_dir = ROOT_DIR / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'radar_sistema_{timestamp}.log'
    
    # Configurar encoding UTF-8 para evitar problemas
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

logger = setup_logging()

# Imports dos módulos do sistema
try:
    # Módulos básicos
    from config import create_directories, validate_config, LOGGING_CONFIG
    from database import Database, get_database, SampleDataGenerator
    from src.data_processing import PolicyDataProcessor
    
    # Módulos ML
    from src.ml.feature_engineering import FeatureEngineer
    from src.ml.model_trainer import ModelTrainer
    from src.ml.model_predictor import ModelPredictor
    from src.ml.model_evaluator import ModelEvaluator
    
    # Módulo Weather
    from src.weather.weather_service import WeatherService
    
    IMPORTS_OK = True
    logger.info("SUCESSO - Todos os módulos importados com sucesso")
    
except ImportError as e:
    logger.error(f"ERRO - Falha ao importar módulos: {e}")
    IMPORTS_OK = False

class RadarSinistroSystem:
    """Sistema principal do Radar de Sinistro"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = None
        self.weather_service = None
        self.feature_engineer = None
        self.model_trainer = None
        self.model_predictor = None
        self.initialized = False
        
    def initialize_system(self) -> bool:
        """Inicializa o sistema completo"""
        self.logger.info("INICIANDO SISTEMA RADAR DE SINISTRO v3.0")
        self.logger.info("="*60)
        
        try:
            # 1. Criar diretórios
            self.logger.info("Criando estrutura de diretórios...")
            create_directories()
            
            # 2. Validar configurações
            self.logger.info("Validando configurações...")
            config_errors = validate_config()
            if config_errors:
                self.logger.error("ERRO - Problemas de configuração:")
                for error in config_errors:
                    self.logger.error(f"   - {error}")
                return False
            
            # 3. Inicializar banco de dados
            self.logger.info("Inicializando banco de dados...")
            self.db = get_database()
            
            # 4. Inicializar Weather Service
            self.logger.info("Inicializando serviço climático...")
            self.weather_service = WeatherService(
                cache_ttl_hours=1,
                cache_db_path="weather_cache.db"
            )
            
            # Testar conectividade da API
            health = self.weather_service.health_check()
            if health['api_status'] == 'healthy':
                self.logger.info("SUCESSO - OpenMeteo API conectada e funcionando")
            else:
                self.logger.warning("AVISO - OpenMeteo API indisponível - usando fallback")
            
            # 5. Inicializar componentes ML
            self.logger.info("Inicializando componentes de Machine Learning...")
            self.feature_engineer = FeatureEngineer(
                use_real_weather=True,
                weather_cache_hours=1
            )
            self.model_trainer = ModelTrainer()
            
            # Verificar se modelo existe
            model_path = ROOT_DIR / 'models' / 'radar_model.pkl'
            if model_path.exists():
                self.model_predictor = ModelPredictor()
                self.logger.info("SUCESSO - Modelo pré-treinado encontrado")
            else:
                self.logger.info("AVISO - Modelo não encontrado - será necessário treinar")
            
            # 6. Verificar dados
            stats = self.db.get_database_stats()
            if stats['tables'].get('apolices', 0) == 0:
                self.logger.info("INFO - Banco vazio - será necessário gerar dados")
            else:
                self.logger.info(f"INFO - Banco com {stats['tables'].get('apolices', 0)} apólices")
            
            self.initialized = True
            self.logger.info("SUCESSO - Sistema inicializado com sucesso!")
            return True
            
        except Exception as e:
            self.logger.error(f"ERRO - Falha na inicialização: {e}")
            return False
    
    def generate_sample_data(self, num_policies: int = 500, num_claims: int = 100) -> bool:
        """Gera dados de exemplo otimizados"""
        self.logger.info(f"Gerando {num_policies} apólices e {num_claims} sinistros...")
        
        try:
            generator = SampleDataGenerator()
            
            # Gerar dados
            self.logger.info("Gerando apólices...")
            policies = generator.generate_sample_policies(num_policies)
            
            self.logger.info("Gerando sinistros...")
            claims = generator.generate_sample_claims(policies, num_claims)
            
            # Salvar CSVs
            sample_dir = ROOT_DIR / 'data' / 'sample'
            sample_dir.mkdir(parents=True, exist_ok=True)
            
            policies_file = sample_dir / 'sample_policies.csv'
            claims_file = sample_dir / 'sample_claims.csv'
            
            generator.save_to_csv(policies, policies_file)
            generator.save_to_csv(claims, claims_file)
            
            self.logger.info(f"SUCESSO - Dados salvos em {sample_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"ERRO - Falha ao gerar dados: {e}")
            return False
    
    def process_data_pipeline(self) -> bool:
        """Executa pipeline completo de processamento"""
        self.logger.info("EXECUTANDO PIPELINE DE PROCESSAMENTO")
        self.logger.info("="*50)
        
        try:
            # 1. Processar dados de apólices
            self.logger.info("Processando dados de apólices...")
            processor = PolicyDataProcessor()
            
            sample_file = ROOT_DIR / 'data' / 'sample' / 'sample_policies.csv'
            if not sample_file.exists():
                self.logger.error("ERRO - Arquivo de apólices não encontrado")
                return False

            df = processor.load_and_process(str(sample_file))            # Salvar dados processados
            processed_dir = ROOT_DIR / 'data' / 'processed'
            processed_dir.mkdir(parents=True, exist_ok=True)
            processed_file = processed_dir / 'policies_processed.csv'

            processor.save_processed_data(df, str(processed_file))
            
            # Relatório de qualidade
            report = processor.get_quality_report()
            self.logger.info("Relatório de qualidade:")
            self.logger.info(f"   • Registros processados: {report['registros_finais']}")
            self.logger.info(f"   • Taxa de sucesso: {report['taxa_sucesso']}%")
            
            return True
            
        except Exception as e:
            self.logger.error(f"ERRO - Falha no processamento: {e}")
            return False
    
    def train_ml_model(self, use_real_weather: bool = True) -> bool:
        """Treina modelo ML com dados climáticos reais ou simulados"""
        self.logger.info("TREINANDO MODELO DE MACHINE LEARNING")
        self.logger.info("="*50)
        
        weather_type = "DADOS CLIMÁTICOS REAIS" if use_real_weather else "DADOS SIMULADOS"
        self.logger.info(f"Usando: {weather_type}")
        
        try:
            # Carregar dados processados
            processed_file = ROOT_DIR / 'data' / 'processed' / 'policies_processed.csv'
            claims_file = ROOT_DIR / 'data' / 'sample' / 'sample_claims.csv'
            
            if not processed_file.exists():
                self.logger.error("ERRO - Dados processados não encontrados")
                return False
            
            # Configurar Feature Engineer
            self.feature_engineer = FeatureEngineer(
                use_real_weather=use_real_weather,
                weather_cache_hours=1
            )
            
            # Inicializar Model Trainer
            self.model_trainer = ModelTrainer()
            
            # Carregar dados
            import pandas as pd
            df_policies = pd.read_csv(processed_file)
            df_claims = pd.read_csv(claims_file) if claims_file.exists() else None
            
            self.logger.info(f"Dados carregados: {len(df_policies)} apólices")
            
            # Verificar compatibilidade entre apólices e sinistros
            if df_claims is not None:
                overlap = len(set(df_policies['numero_apolice']) & set(df_claims['numero_apolice']))
                if overlap == 0:
                    self.logger.warning("AVISO - Nenhuma correspondência entre apólices e sinistros")
                    self.logger.warning("AVISO - Usando dados simulados de sinistros")
                    df_claims = None
                else:
                    self.logger.info(f"INFO - {overlap} apólices com sinistros encontradas")
            
            # Feature Engineering
            self.logger.info("Executando feature engineering...")
            features_df = self.feature_engineer.create_features(df_policies, df_claims)
            
            self.logger.info(f"SUCESSO - Features criadas: {features_df.shape}")
            
            # Preparar dados para treinamento
            X_train, X_test, y_train, y_test = self.feature_engineer.prepare_model_data(
                features_df, test_size=0.2
            )
            
            # Treinar modelo
            self.logger.info("Iniciando treinamento do modelo...")
            results = self.model_trainer.train_model(
                X_train, X_test, y_train, y_test
            )
            
            # Salvar modelo e preprocessors
            models_dir = ROOT_DIR / 'models'
            models_dir.mkdir(exist_ok=True)
            
            self.model_trainer.save_model(models_dir / 'radar_model.pkl')
            self.feature_engineer.save_preprocessors(models_dir)
            
            # Log resultados
            self.logger.info("RESULTADOS DO TREINAMENTO:")
            for metric, value in results.items():
                if isinstance(value, float):
                    self.logger.info(f"   • {metric}: {value:.4f}")
            
            # Criar predictor
            self.model_predictor = ModelPredictor()
            
            self.logger.info("SUCESSO - Modelo treinado e salvo!")
            return True
            
        except Exception as e:
            self.logger.error(f"ERRO - Falha no treinamento: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_predictions(self, num_tests: int = 5) -> bool:
        """Testa predições com dados climáticos reais"""
        self.logger.info("TESTANDO PREDIÇÕES")
        self.logger.info("="*30)
        
        if not self.model_predictor:
            self.logger.error("ERRO - Modelo não disponível")
            return False
        
        # Dados de teste variados
        test_cases = [
            {
                'numero_apolice': 'TEST_SP_001',
                'cep': '01310-100',  # São Paulo - Centro
                'tipo_residencia': 'apartamento',
                'valor_segurado': 800000,
                'data_contratacao': '2024-01-15',
                'latitude': -23.5505,
                'longitude': -46.6333
            },
            {
                'numero_apolice': 'TEST_RJ_002', 
                'cep': '22071-900',  # Rio - Copacabana
                'tipo_residencia': 'casa',
                'valor_segurado': 1200000,
                'data_contratacao': '2023-08-20',
                'latitude': -22.9068,
                'longitude': -43.1729
            },
            {
                'numero_apolice': 'TEST_BSB_003',
                'cep': '70040-010',  # Brasília
                'tipo_residencia': 'casa',
                'valor_segurado': 600000,
                'data_contratacao': '2024-03-10',
                'latitude': -15.7942,
                'longitude': -47.8822
            },
            {
                'numero_apolice': 'TEST_POA_004',
                'cep': '90010-150',  # Porto Alegre
                'tipo_residencia': 'apartamento',
                'valor_segurado': 450000,
                'data_contratacao': '2023-12-01',
                'latitude': -30.0346,
                'longitude': -51.2177
            },
            {
                'numero_apolice': 'TEST_FOR_005',
                'cep': '60160-230',  # Fortaleza
                'tipo_residencia': 'casa',
                'valor_segurado': 350000,
                'data_contratacao': '2024-05-15',
                'latitude': -3.7327,
                'longitude': -38.5267
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases[:num_tests], 1):
            try:
                self.logger.info(f"\nTeste {i}: {test_case['numero_apolice']}")
                
                result = self.model_predictor.predict_single_policy(test_case)
                
                if 'error' not in result:
                    risk_score = result['risk_score']
                    risk_level = result['risk_level']
                    
                    self.logger.info(f"   • Score de Risco: {risk_score:.1f}")
                    self.logger.info(f"   • Nível: {risk_level}")
                    self.logger.info(f"   • Probabilidade: {result['probability']:.3f}")
                    
                    # Mostrar principais fatores de influência
                    if 'influence_factors' in result and result['influence_factors']:
                        top_factors = result['influence_factors'][:3]
                        self.logger.info("   • Top fatores:")
                        for factor in top_factors:
                            feature_name = factor['feature']
                            contribution = factor['contribution']
                            self.logger.info(f"     - {feature_name}: {contribution:.3f}")
                    
                    success_count += 1
                else:
                    self.logger.error(f"   ERRO: {result['error']}")
                    
            except Exception as e:
                self.logger.error(f"   ERRO no teste {i}: {e}")
        
        success_rate = (success_count / num_tests) * 100
        self.logger.info(f"\nTaxa de sucesso: {success_rate:.1f}% ({success_count}/{num_tests})")
        
        return success_count > 0
    
    def show_system_status(self) -> Dict[str, Any]:
        """Mostra status completo do sistema"""
        self.logger.info("STATUS DO SISTEMA")
        self.logger.info("="*40)
        
        status = {
            'initialized': self.initialized,
            'database': False,
            'weather_service': False,
            'ml_model': False,
            'weather_api_status': 'unknown'
        }
        
        try:
            # Status do banco
            if self.db:
                stats = self.db.get_database_stats()
                status['database'] = True
                
                self.logger.info("Banco de Dados:")
                self.logger.info(f"   • Tamanho: {stats.get('file_size_mb', 0):.1f} MB")
                for table, count in stats.get('tables', {}).items():
                    self.logger.info(f"   • {table}: {count} registros")
            
            # Status do Weather Service
            if self.weather_service:
                health = self.weather_service.health_check()
                weather_stats = self.weather_service.get_service_stats()
                
                status['weather_service'] = True
                status['weather_api_status'] = health['api_status']
                
                self.logger.info("Serviço Climático:")
                self.logger.info(f"   • API Status: {health['api_status']}")
                self.logger.info(f"   • Cache Hit Rate: {weather_stats['cache_hit_rate_percent']}%")
                self.logger.info(f"   • Total Requests: {weather_stats['total_requests']}")
            
            # Status do modelo ML
            models_dir = ROOT_DIR / 'models'
            model_files = {
                'radar_model.pkl': (models_dir / 'radar_model.pkl').exists(),
                'scaler.pkl': (models_dir / 'scaler.pkl').exists(),
                'feature_columns.pkl': (models_dir / 'feature_columns.pkl').exists(),
                'label_encoders.pkl': (models_dir / 'label_encoders.pkl').exists()
            }
            
            status['ml_model'] = all(model_files.values())
            
            self.logger.info("Modelo ML:")
            for file, exists in model_files.items():
                status_text = "OK" if exists else "FALTANDO"
                self.logger.info(f"   • {file}: {status_text}")
            
            if self.model_predictor:
                self.logger.info("   • Predictor: Ativo")
            else:
                self.logger.info("   • Predictor: Inativo")
        
        except Exception as e:
            self.logger.error(f"ERRO ao obter status: {e}")
        
        return status
    
    def run_full_demo(self) -> bool:
        """Executa demonstração completa do sistema"""
        self.logger.info("DEMONSTRAÇÃO COMPLETA DO RADAR DE SINISTRO")
        self.logger.info("="*60)
        
        try:
            # 1. Inicializar sistema
            if not self.initialize_system():
                return False
            
            # 2. Gerar dados se necessário
            stats = self.db.get_database_stats()
            if stats['tables'].get('apolices', 0) == 0:
                self.logger.info("Gerando dados de exemplo...")
                if not self.generate_sample_data():
                    return False
            
            # 3. Processar dados
            self.logger.info("Processando dados...")
            if not self.process_data_pipeline():
                return False
            
            # 4. Treinar modelo com dados reais
            model_path = ROOT_DIR / 'models' / 'radar_model.pkl'
            if not model_path.exists():
                self.logger.info("Treinando modelo com dados climáticos reais...")
                if not self.train_ml_model(use_real_weather=True):
                    return False
            else:
                self.logger.info("SUCESSO - Modelo existente carregado")
                self.model_predictor = ModelPredictor()
            
            # 5. Testar predições
            self.logger.info("Executando testes de predição...")
            if not self.test_predictions(5):
                return False
            
            # 6. Status final
            self.show_system_status()
            
            self.logger.info("DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
            return True
            
        except Exception as e:
            self.logger.error(f"ERRO na demonstração: {e}")
            return False

def show_enhanced_menu():
    """Menu principal atualizado"""
    print("\n" + "="*60)
    print("    RADAR DE SINISTRO v3.0 - SISTEMA PRINCIPAL")
    print("         Com Dados Climáticos Reais")
    print("="*60)
    print("DADOS E PROCESSAMENTO:")
    print("  1. Inicializar sistema completo")
    print("  2. Gerar dados de exemplo")
    print("  3. Processar dados (Pipeline)")
    print("")
    print("MACHINE LEARNING:")
    print("  4. Treinar modelo (Dados REAIS)")
    print("  5. Treinar modelo (Dados SIMULADOS)")
    print("  6. Testar predições")
    print("")
    print("SISTEMA CLIMÁTICO:")
    print("  7. Status do Weather Service")
    print("  8. Teste de conectividade da API")
    print("")
    print("DEMONSTRAÇÕES:")
    print("  9. Demo completo (Full Pipeline)")
    print(" 10. Status geral do sistema")
    print("")
    print("UTILITÁRIOS:")
    print(" 11. Estatísticas do banco")
    print(" 12. Limpar cache climático")
    print("")
    print("  0. Sair")
    print("="*60)

def main():
    """Função principal com menu interativo atualizado"""
    print("Iniciando Radar de Sinistro v3.0...")
    
    if not IMPORTS_OK:
        print("ERRO - Falha nos imports. Verifique as dependências.")
        return
    
    # Criar instância do sistema
    radar_system = RadarSinistroSystem()
    
    while True:
        show_enhanced_menu()
        
        try:
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == '0':
                logger.info("Encerrando sistema...")
                break
            
            elif choice == '1':
                radar_system.initialize_system()
            
            elif choice == '2':
                radar_system.generate_sample_data()
            
            elif choice == '3':
                radar_system.process_data_pipeline()
            
            elif choice == '4':
                radar_system.train_ml_model(use_real_weather=True)
            
            elif choice == '5':
                radar_system.train_ml_model(use_real_weather=False)
            
            elif choice == '6':
                radar_system.test_predictions()
            
            elif choice == '7':
                if not radar_system.weather_service:
                    print("Inicializando Weather Service...")
                    radar_system.weather_service = WeatherService(
                        cache_ttl_hours=1,
                        cache_db_path="weather_cache.db"
                    )
                
                try:
                    health = radar_system.weather_service.health_check()
                    stats = radar_system.weather_service.get_service_stats()
                    
                    print("\nSTATUS DO WEATHER SERVICE:")
                    print("="*50)
                    print(f"   • API Status: {health['api_status']}")
                    print(f"   • API Response Time: {health.get('response_time_ms', 'N/A')} ms")
                    print(f"   • Cache Hit Rate: {stats['cache_hit_rate_percent']}%")
                    print(f"   • Total Requests: {stats['total_requests']}")
                    
                    # Detalhes das requisições
                    requests_info = stats.get('requests', {})
                    print(f"   • Cache Hits: {requests_info.get('cache_hits', 0)}")
                    print(f"   • API Calls: {requests_info.get('api_calls', 0)}")
                    print(f"   • Fallbacks: {requests_info.get('fallbacks', 0)}")
                    print(f"   • Errors: {requests_info.get('errors', 0)}")
                    print(f"   • Error Rate: {stats['error_rate_percent']}%")
                    
                    # Detalhes do cache
                    cache_info = stats.get('cache_stats', {})
                    if cache_info:
                        print(f"   • Cache Entries: {cache_info.get('total_entries', 'N/A')}")
                        print(f"   • Cache Size: {cache_info.get('database_size_mb', 'N/A')} MB")
                        print(f"   • Cache TTL: {cache_info.get('ttl_hours', 'N/A')} horas")
                        print(f"   • Valid Entries: {cache_info.get('valid_entries', 'N/A')}")
                        print(f"   • Expired Entries: {cache_info.get('expired_entries', 'N/A')}")
                    
                    print("="*50)
                    
                except Exception as e:
                    print(f"ERRO ao obter status do Weather Service: {e}")
                    logger.error(f"Erro ao obter status do Weather Service: {e}")
            
            elif choice == '8':
                if not radar_system.weather_service:
                    radar_system.weather_service = WeatherService()
                
                print("Testando conectividade da OpenMeteo API...")
                health = radar_system.weather_service.health_check()
                
                if health['api_status'] == 'healthy':
                    print("SUCESSO - API OpenMeteo funcionando perfeitamente!")
                else:
                    print("ERRO - API OpenMeteo indisponível - usando fallback")
            
            elif choice == '9':
                radar_system.run_full_demo()
            
            elif choice == '10':
                radar_system.show_system_status()
            
            elif choice == '11':
                try:
                    if not radar_system.db:
                        radar_system.db = get_database()
                    
                    stats = radar_system.db.get_database_stats()
                    print("\nESTATÍSTICAS DO BANCO:")
                    print(f"   • Tamanho: {stats['file_size_mb']:.1f} MB")
                    for table, count in stats['tables'].items():
                        print(f"   • {table}: {count} registros")
                except Exception as e:
                    logger.error(f"Erro ao obter estatísticas: {e}")
            
            elif choice == '12':
                if radar_system.weather_service:
                    radar_system.weather_service.clear_cache(confirm=True)
                    print("SUCESSO - Cache climático limpo")
                else:
                    print("ERRO - Weather Service não disponível")
            
            else:
                print("ERRO - Opção inválida. Tente novamente.")
        
        except KeyboardInterrupt:
            logger.info("\nEncerrando sistema...")
            break
        except Exception as e:
            logger.error(f"ERRO inesperado: {e}")
        
        input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    # Verificar versão Python
    if sys.version_info < (3, 8):
        print("ERRO - Este sistema requer Python 3.8 ou superior.")
        sys.exit(1)
    
    # Executar sistema
    main()