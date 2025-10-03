"""
Script principal do Sistema de Radar de Sinistro

Este script orquestra todos os componentes do sistema.
"""

import os
import sys
import logging
from pathlib import Path

# Adicionar diretório raiz ao Python path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

# Importações dos módulos do sistema
try:
    from config import create_directories, validate_config, LOGGING_CONFIG
    from database import Database, get_database, SampleDataGenerator
    from src.data_processing import PolicyDataProcessor
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Certifique-se de que todos os módulos estão instalados.")
    sys.exit(1)

# Configurar logging
def setup_logging():
    """Configura sistema de logging"""
    log_dir = LOGGING_CONFIG['log_dir']
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, LOGGING_CONFIG['level']),
        format=LOGGING_CONFIG['format'],
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'radar_sistema.log')),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def initialize_system():
    """Inicializa o sistema completo"""
    logger = setup_logging()
    logger.info("=== Iniciando Sistema de Radar de Sinistro ===")
    
    try:
        # 1. Criar diretórios necessários
        logger.info("Criando diretórios necessários...")
        create_directories()
        
        # 2. Validar configurações
        logger.info("Validando configurações...")
        config_errors = validate_config()
        if config_errors:
            logger.error("Erros de configuração encontrados:")
            for error in config_errors:
                logger.error(f"  - {error}")
            return False
        
        # 3. Inicializar banco de dados
        logger.info("Inicializando banco de dados...")
        db = get_database()
        logger.info("Banco de dados inicializado com sucesso")
        
        # 4. Verificar se tem dados de exemplo
        stats = db.get_database_stats()
        if stats['tables'].get('apolices', 0) == 0:
            logger.info("Banco vazio. Gerando dados de exemplo...")
            generate_sample_data()
        
        logger.info("Sistema inicializado com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"Erro na inicialização: {e}")
        return False


def generate_sample_data():
    """Gera dados de exemplo para demonstração"""
    logger = logging.getLogger(__name__)
    
    try:
        # Gerar dados de exemplo
        generator = SampleDataGenerator()
        
        logger.info("Gerando apólices de exemplo...")
        policies = generator.generate_sample_policies(500)
        
        logger.info("Gerando sinistros históricos...")
        claims = generator.generate_sample_claims(policies, 100)
        
        logger.info("Gerando dados climáticos...")
        climate_data = generator.generate_climate_data(200)
        
        # Salvar em CSVs
        sample_dir = os.path.join(ROOT_DIR, 'data', 'sample')
        os.makedirs(sample_dir, exist_ok=True)
        
        generator.save_to_csv(policies, os.path.join(sample_dir, 'sample_policies.csv'))
        generator.save_to_csv(claims, os.path.join(sample_dir, 'sample_claims.csv'))
        generator.save_to_csv(climate_data, os.path.join(sample_dir, 'sample_climate_data.csv'))
        
        logger.info("Dados de exemplo gerados com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao gerar dados de exemplo: {e}")


def process_sample_data():
    """Processa dados de exemplo através do pipeline completo"""
    logger = logging.getLogger(__name__)
    
    try:
        # Processar dados de apólices
        logger.info("Processando dados de apólices...")
        processor = PolicyDataProcessor()
        
        sample_file = os.path.join(ROOT_DIR, 'data', 'sample', 'sample_policies.csv')
        if os.path.exists(sample_file):
            df = processor.load_and_process(sample_file)
            
            # Salvar dados processados
            processed_file = os.path.join(ROOT_DIR, 'data', 'processed', 'policies_processed.csv')
            processor.save_processed_data(df, processed_file)
            
            # Exibir relatório de qualidade
            report = processor.get_quality_report()
            logger.info("Relatório de qualidade dos dados:")
            logger.info(f"  - Registros processados: {report['registros_finais']}")
            logger.info(f"  - Taxa de sucesso: {report['taxa_sucesso']}%")
            
        else:
            logger.warning("Arquivo de exemplo não encontrado. Execute generate_sample_data() primeiro.")
            
    except Exception as e:
        logger.error(f"Erro no processamento: {e}")


def run_system_demo():
    """Executa demonstração completa do sistema"""
    logger = logging.getLogger(__name__)
    
    logger.info("=== DEMONSTRAÇÃO DO SISTEMA ===")
    
    # 1. Inicializar sistema
    if not initialize_system():
        logger.error("Falha na inicialização. Encerrando demo.")
        return
    
    # 2. Processar dados
    process_sample_data()
    
    # 3. Exibir estatísticas do banco
    db = get_database()
    stats = db.get_database_stats()
    
    logger.info("=== ESTATÍSTICAS DO BANCO ===")
    logger.info(f"Tamanho do banco: {stats['file_size_mb']} MB")
    for table, count in stats['tables'].items():
        logger.info(f"  - {table}: {count} registros")
    
    logger.info("=== DEMONSTRAÇÃO CONCLUÍDA ===")


def run_data_quality_check():
    """Executa verificação de qualidade dos dados"""
    logger = logging.getLogger(__name__)
    
    logger.info("=== VERIFICAÇÃO DE QUALIDADE ===")
    
    try:
        processor = PolicyDataProcessor()
        sample_file = os.path.join(ROOT_DIR, 'data', 'sample', 'sample_policies.csv')
        
        if os.path.exists(sample_file):
            # Carregar dados para análise
            df = processor.loader.load_file(sample_file)
            
            # Executar validações
            validation_result = processor.validator.validate_dataframe_schema(df)
            quality_metrics = processor.validator.validate_data_quality(df)
            
            logger.info("Resultado da validação:")
            logger.info(f"  - Schema válido: {validation_result['valid']}")
            if validation_result['errors']:
                for error in validation_result['errors']:
                    logger.error(f"    Erro: {error}")
            
            logger.info("Métricas de qualidade:")
            logger.info(f"  - Total de registros: {quality_metrics['total_records']}")
            logger.info(f"  - Score geral: {quality_metrics['overall_score']}")
            logger.info(f"  - Duplicatas: {quality_metrics['duplicates']}")
            
        else:
            logger.warning("Arquivo de dados não encontrado")
            
    except Exception as e:
        logger.error(f"Erro na verificação: {e}")


def show_menu():
    """Exibe menu de opções do sistema"""
    print("\n" + "="*50)
    print("    SISTEMA DE RADAR DE SINISTRO")
    print("="*50)
    print("1. Inicializar sistema completo")
    print("2. Gerar dados de exemplo")
    print("3. Processar dados de exemplo")
    print("4. Executar demo completo")
    print("5. Verificar qualidade dos dados")
    print("6. Exibir estatísticas do banco")
    print("0. Sair")
    print("="*50)


def main():
    """Função principal com menu interativo"""
    logger = setup_logging()
    
    while True:
        show_menu()
        
        try:
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == '0':
                logger.info("Encerrando sistema...")
                break
                
            elif choice == '1':
                initialize_system()
                
            elif choice == '2':
                generate_sample_data()
                
            elif choice == '3':
                process_sample_data()
                
            elif choice == '4':
                run_system_demo()
                
            elif choice == '5':
                run_data_quality_check()
                
            elif choice == '6':
                try:
                    db = get_database()
                    stats = db.get_database_stats()
                    print("\n=== ESTATÍSTICAS DO BANCO ===")
                    print(f"Tamanho: {stats['file_size_mb']} MB")
                    for table, count in stats['tables'].items():
                        print(f"  - {table}: {count} registros")
                except Exception as e:
                    logger.error(f"Erro ao obter estatísticas: {e}")
                    
            else:
                print("Opção inválida. Tente novamente.")
                
        except KeyboardInterrupt:
            logger.info("\nEncerrando sistema...")
            break
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    # Verificar versão Python
    if sys.version_info < (3, 8):
        print("Este sistema requer Python 3.8 ou superior.")
        sys.exit(1)
    
    # Executar sistema
    main()