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
    
    # Módulo Mapa de Calor
    from mapa_de_calor_completo import MapaCalorRiscos, OSMGeocoder
    
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
        self.mapa_calor = None  # Novo componente
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
            
            # 7. Inicializar Mapa de Calor
            self.logger.info("Inicializando sistema de mapa de calor...")
            try:
                geocoder = OSMGeocoder(cache_dir=str(ROOT_DIR / "cache"))
                self.mapa_calor = MapaCalorRiscos(geocoder)
                self.logger.info("✓ Mapa de calor inicializado com sucesso")
            except Exception as e:
                self.logger.warning(f"⚠ Mapa de calor não disponível: {e}")
                self.mapa_calor = None
            
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
    
    def generate_risk_heatmap(self, output_format: str = "html") -> bool:
        """Gera mapa de calor dos riscos por CEP"""
        self.logger.info("GERANDO MAPA DE CALOR DE RISCOS")
        self.logger.info("="*50)
        
        if not self.mapa_calor:
            self.logger.error("❌ Sistema de mapa de calor não inicializado")
            return False
        
        try:
            # 1. Buscar dados das apólices com predições
            self.logger.info("Carregando dados das apólices...")
            
            # Query para buscar apólices com CEPs válidos
            query = """
            SELECT 
                numero_apolice,
                cep,
                valor_segurado as insured_value,
                tipo_residencia,
                data_contratacao
            FROM apolices 
            WHERE cep IS NOT NULL 
            AND cep != '' 
            AND LENGTH(REPLACE(cep, '-', '')) = 8
            ORDER BY data_contratacao DESC
            """
            
            policies_data = self.db.execute_query(query)
            
            if not policies_data:
                self.logger.warning("⚠ Nenhuma apólice com CEP válido encontrada")
                return False
            
            self.logger.info(f"✓ {len(policies_data)} apólices carregadas")
            
            # 2. Gerar predições de risco para cada apólice
            self.logger.info("Calculando scores de risco...")
            
            if not self.model_predictor:
                self.logger.error("❌ Modelo preditor não inicializado")
                return False
            
            enriched_data = []
            success_count = 0
            
            for policy in policies_data:
                try:
                    # Preparar dados para predição
                    policy_input = {
                        'numero_apolice': policy[0],
                        'cep': policy[1],
                        'valor_segurado': policy[2],
                        'tipo_residencia': policy[3],
                        'data_contratacao': policy[4]
                    }
                    
                    # Fazer predição
                    prediction = self.model_predictor.predict_single_policy(policy_input)
                    
                    if prediction:
                        enriched_data.append({
                            'cep': policy[1],
                            'risk_score': prediction['risk_score'] * 100,  # Converter para 0-100
                            'insured_value': policy[2],
                            'policy_id': policy[0]
                        })
                        success_count += 1
                        
                except Exception as e:
                    self.logger.debug(f"Erro ao processar apólice {policy[0]}: {e}")
                    continue
            
            if not enriched_data:
                self.logger.error("❌ Nenhuma predição de risco foi gerada")
                return False
            
            self.logger.info(f"✓ {success_count} predições geradas com sucesso")
            
            # 3. Converter para DataFrame
            import pandas as pd
            policies_df = pd.DataFrame(enriched_data)
            
            # 4. Gerar mapa de calor
            self.logger.info("Gerando visualização do mapa...")
            
            if output_format == "html":
                # Gerar HTML do mapa
                map_html = self.mapa_calor.criar_mapa_calor(policies_df)
                
                # Salvar arquivo HTML
                output_dir = ROOT_DIR / "outputs"
                output_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                html_file = output_dir / f"mapa_calor_riscos_{timestamp}.html"
                
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Mapa de Calor - Radar de Sinistro</title>
                        <meta charset="utf-8">
                        <style>
                            body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
                            .header {{ text-align: center; margin-bottom: 20px; }}
                            .stats {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>🗺️ Mapa de Calor - Distribuição de Riscos</h1>
                            <p>Radar de Sinistro v3.0 - Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                        </div>
                        
                        <div class="stats">
                            <strong>📊 Estatísticas:</strong>
                            • {len(policies_df)} apólices analisadas
                            • {policies_df['cep'].nunique()} CEPs únicos
                            • Risco médio: {policies_df['risk_score'].mean():.1f}
                            • Valor total segurado: R$ {policies_df['insured_value'].sum():,.0f}
                        </div>
                        
                        {map_html}
                    </body>
                    </html>
                    """)
                
                self.logger.info(f"✅ Mapa salvo em: {html_file}")
                
                # Tentar abrir no navegador (Windows)
                try:
                    import webbrowser
                    webbrowser.open(f"file:///{html_file}")
                    self.logger.info("🌐 Mapa aberto no navegador")
                except:
                    self.logger.info("💡 Abra o arquivo HTML manualmente no navegador")
                    
            else:
                # Exibir estatísticas no console
                self._show_heatmap_stats(policies_df)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar mapa de calor: {e}")
            return False
    
    def _show_heatmap_stats(self, policies_df) -> None:
        """Exibe estatísticas do mapa de calor no console"""
        import pandas as pd
        
        self.logger.info("\n📊 ESTATÍSTICAS DO MAPA DE CALOR")
        self.logger.info("-" * 40)
        
        # Estatísticas gerais
        total_policies = len(policies_df)
        unique_ceps = policies_df['cep'].nunique()
        avg_risk = policies_df['risk_score'].mean()
        total_value = policies_df['insured_value'].sum()
        
        self.logger.info(f"📋 Total de apólices: {total_policies:,}")
        self.logger.info(f"📍 CEPs únicos: {unique_ceps:,}")
        self.logger.info(f"🎯 Risco médio: {avg_risk:.1f}")
        self.logger.info(f"💰 Valor total: R$ {total_value:,.0f}")
        
        # Distribuição por nível de risco
        risk_distribution = {
            'Muito Baixo (0-25)': len(policies_df[policies_df['risk_score'] < 25]),
            'Baixo (25-50)': len(policies_df[(policies_df['risk_score'] >= 25) & (policies_df['risk_score'] < 50)]),
            'Médio (50-75)': len(policies_df[(policies_df['risk_score'] >= 50) & (policies_df['risk_score'] < 75)]),
            'Alto (75-100)': len(policies_df[policies_df['risk_score'] >= 75])
        }
        
        self.logger.info("\n🎯 DISTRIBUIÇÃO POR NÍVEL DE RISCO:")
        for level, count in risk_distribution.items():
            percentage = (count / total_policies) * 100
            self.logger.info(f"  {level}: {count} apólices ({percentage:.1f}%)")
        
        # Top 5 CEPs com maior risco
        cep_stats = policies_df.groupby('cep').agg({
            'risk_score': 'mean',
            'insured_value': 'sum',
            'policy_id': 'count'
        }).round(2)
        cep_stats.columns = ['risk_medio', 'valor_total', 'num_apolices']
        
        top_risk_ceps = cep_stats.nlargest(5, 'risk_medio')
        
        self.logger.info(f"\n🔴 TOP 5 CEPs COM MAIOR RISCO:")
        for cep, data in top_risk_ceps.iterrows():
            self.logger.info(f"  {cep}: Risco {data['risk_medio']:.1f} - {data['num_apolices']} apólices")

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
    print("VISUALIZAÇÃO:")
    print("  7. Gerar Mapa de Calor (HTML)")
    print("  8. Estatísticas de Risco por CEP")
    print("")
    print("SISTEMA CLIMÁTICO:")
    print("  9. Status do Weather Service")
    print(" 10. Teste de conectividade da API")
    print("")
    print("DEMONSTRAÇÕES:")
    print(" 11. Demo completo (Full Pipeline)")
    print(" 12. Status geral do sistema")
    print("")
    print("UTILITÁRIOS:")
    print(" 13. Estatísticas do banco")
    print(" 14. Limpar cache climático")
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
            choice = input("\n📋 Escolha uma opção: ").strip()
            
            if choice == "0":
                print("\n👋 Encerrando sistema. Até logo!")
                break
                
            elif choice == "1":
                print("\n🚀 Inicializando sistema...")
                radar_system.initialize_system()
                
            elif choice == "2":
                print("\n📊 Gerando dados de exemplo...")
                radar_system.generate_sample_data()
                
            elif choice == "3":
                print("\n⚙️ Processando dados...")
                radar_system.process_data_pipeline()
                
            elif choice == "4":
                print("\n🤖 Treinando modelo com dados reais...")
                radar_system.train_ml_model(use_real_weather=True)
                
            elif choice == "5":
                print("\n🤖 Treinando modelo com dados simulados...")
                radar_system.train_ml_model(use_real_weather=False)
                
            elif choice == "6":
                print("\n🎯 Testando predições...")
                radar_system.test_predictions()
                
            elif choice == "7":
                print("\n🗺️ Gerando mapa de calor...")
                radar_system.generate_risk_heatmap(output_format="html")
                
            elif choice == "8":
                print("\n📊 Estatísticas de risco por CEP...")
                radar_system.generate_risk_heatmap(output_format="stats")
                
            elif choice == "9":
                print("\n🌤️ Verificando Weather Service...")
                if radar_system.weather_service:
                    health = radar_system.weather_service.health_check()
                    print(f"Status da API: {health['api_status']}")
                else:
                    print("Weather Service não inicializado")
                    
            elif choice == "10":
                print("\n🔗 Testando conectividade...")
                if radar_system.weather_service:
                    # Teste básico
                    test_result = radar_system.weather_service.get_current_weather(-23.5505, -46.6333)
                    if test_result:
                        print("✅ API funcionando corretamente")
                    else:
                        print("❌ Falha na conectividade")
                else:
                    print("Weather Service não inicializado")
                    
            elif choice == "11":
                print("\n🎭 Executando demo completo...")
                radar_system.run_full_demo()
                
            elif choice == "12":
                print("\n📊 Status do sistema...")
                radar_system.show_system_status()
                
            elif choice == "13":
                print("\n📈 Estatísticas do banco...")
                if radar_system.db:
                    stats = radar_system.db.get_database_stats()
                    for table, count in stats['tables'].items():
                        print(f"  {table}: {count} registros")
                else:
                    print("Banco não inicializado")
                    
            elif choice == "14":
                print("\n🧹 Limpando cache climático...")
                cache_dir = ROOT_DIR / "cache"
                if cache_dir.exists():
                    import shutil
                    shutil.rmtree(cache_dir)
                    print("✅ Cache limpo")
                else:
                    print("Cache não encontrado")
                    
            else:
                print("❌ Opção inválida! Tente novamente.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrompido pelo usuário. Até logo!")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    # Verificar versão Python
    if sys.version_info < (3, 8):
        print("ERRO - Este sistema requer Python 3.8 ou superior.")
        sys.exit(1)
    
    # Executar sistema
    main()