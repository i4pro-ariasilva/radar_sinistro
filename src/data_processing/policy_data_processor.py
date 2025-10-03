"""
Processador principal de dados de apólices
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Union
import os
import logging
from .data_cleaner import DataCleaner
from .data_validator import DataValidator
from .file_loaders import FileLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolicyDataProcessor:
    """Classe principal para processamento de dados de apólices"""
    
    def __init__(self):
        self.cleaner = DataCleaner()
        self.validator = DataValidator()
        self.loader = FileLoader()
        self.quality_report = {}
    
    def load_and_process(self, file_path: str, file_type: str = 'auto') -> pd.DataFrame:
        """
        Carrega e processa dados de apólices completo
        
        Args:
            file_path: Caminho para o arquivo
            file_type: Tipo do arquivo ('csv', 'excel', 'json', 'auto')
            
        Returns:
            DataFrame processado e limpo
        """
        logger.info(f"Iniciando processamento de: {file_path}")
        
        # 1. Carregamento
        raw_data = self.loader.load_file(file_path, file_type)
        logger.info(f"Carregados {len(raw_data)} registros")
        
        # 2. Validação inicial do schema
        schema_valid = self.validate_schema(raw_data)
        if not schema_valid:
            raise ValueError("Schema do arquivo inválido")
        
        # 3. Limpeza dos dados
        clean_data = self.clean_data(raw_data)
        logger.info(f"Após limpeza: {len(clean_data)} registros")
        
        # 4. Validação final
        self.validate_final_data(clean_data)
        
        # 5. Gerar relatório de qualidade
        self.generate_quality_report(raw_data, clean_data)
        
        logger.info("Processamento concluído com sucesso")
        return clean_data
    
    def validate_schema(self, df: pd.DataFrame) -> bool:
        """
        Valida se o DataFrame possui as colunas necessárias
        
        Args:
            df: DataFrame para validar
            
        Returns:
            True se schema válido
        """
        required_columns = [
            'numero_apolice', 'cep', 'tipo_residencia', 
            'valor_segurado', 'data_contratacao'
        ]
        
        optional_columns = [
            'nome_segurado', 'latitude', 'longitude', 'ativa'
        ]
        
        # Verifica colunas obrigatórias
        missing_required = set(required_columns) - set(df.columns)
        if missing_required:
            logger.error(f"Colunas obrigatórias faltantes: {missing_required}")
            return False
        
        # Log das colunas opcionais encontradas
        found_optional = set(optional_columns) & set(df.columns)
        if found_optional:
            logger.info(f"Colunas opcionais encontradas: {found_optional}")
        
        return True
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Executa limpeza completa dos dados
        
        Args:
            df: DataFrame bruto
            
        Returns:
            DataFrame limpo
        """
        logger.info("Iniciando limpeza de dados...")
        
        # Criar cópia para não modificar original
        clean_df = df.copy()
        
        # 1. Limpeza de campos específicos
        if 'cep' in clean_df.columns:
            clean_df['cep'] = self.cleaner.clean_cep(clean_df['cep'])
        
        if 'tipo_residencia' in clean_df.columns:
            clean_df['tipo_residencia'] = self.cleaner.normalize_residence_type(clean_df['tipo_residencia'])
        
        if 'valor_segurado' in clean_df.columns:
            clean_df['valor_segurado'] = self.cleaner.clean_monetary_values(clean_df['valor_segurado'])
        
        if 'data_contratacao' in clean_df.columns:
            clean_df['data_contratacao'] = self.cleaner.clean_dates(clean_df['data_contratacao'])
        
        if 'numero_apolice' in clean_df.columns:
            clean_df['numero_apolice'] = self.cleaner.clean_policy_numbers(clean_df['numero_apolice'])
        
        # 2. Remoção de duplicatas
        initial_count = len(clean_df)
        clean_df = clean_df.drop_duplicates(subset=['numero_apolice'], keep='first')
        duplicates_removed = initial_count - len(clean_df)
        if duplicates_removed > 0:
            logger.warning(f"Removidas {duplicates_removed} apólices duplicadas")
        
        # 3. Tratamento de valores faltantes
        clean_df = self.cleaner.handle_missing_values(clean_df)
        
        # 4. Adição de campos padrão se não existirem
        if 'ativa' not in clean_df.columns:
            clean_df['ativa'] = True
        
        return clean_df
    
    def validate_final_data(self, df: pd.DataFrame) -> Dict[str, List[int]]:
        """
        Valida dados finais e retorna erros por linha
        
        Args:
            df: DataFrame limpo
            
        Returns:
            Dicionário com erros por tipo
        """
        logger.info("Validando dados finais...")
        
        validation_errors = {
            'cep_invalido': [],
            'valor_invalido': [],
            'data_invalida': [],
            'tipo_invalido': []
        }
        
        for idx, row in df.iterrows():
            # Validar CEP
            if not self.validator.validate_cep(row['cep']):
                validation_errors['cep_invalido'].append(idx)
            
            # Validar valor segurado
            if not self.validator.validate_insurance_value(row['valor_segurado']):
                validation_errors['valor_invalido'].append(idx)
            
            # Validar data
            if not self.validator.validate_date_format(row['data_contratacao']):
                validation_errors['data_invalida'].append(idx)
            
            # Validar tipo residência
            if not self.validator.validate_residence_type(row['tipo_residencia']):
                validation_errors['tipo_invalido'].append(idx)
        
        # Log dos erros encontrados
        total_errors = sum(len(errors) for errors in validation_errors.values())
        if total_errors > 0:
            logger.warning(f"Encontrados {total_errors} erros de validação:")
            for error_type, error_lines in validation_errors.items():
                if error_lines:
                    logger.warning(f"  - {error_type}: {len(error_lines)} registros")
        
        return validation_errors
    
    def generate_quality_report(self, raw_df: pd.DataFrame, clean_df: pd.DataFrame):
        """
        Gera relatório de qualidade dos dados
        
        Args:
            raw_df: DataFrame original
            clean_df: DataFrame após limpeza
        """
        self.quality_report = {
            'registros_originais': len(raw_df),
            'registros_finais': len(clean_df),
            'registros_removidos': len(raw_df) - len(clean_df),
            'taxa_sucesso': round(len(clean_df) / len(raw_df) * 100, 2),
            'colunas_originais': list(raw_df.columns),
            'colunas_finais': list(clean_df.columns),
            'valores_nulos_original': raw_df.isnull().sum().to_dict(),
            'valores_nulos_final': clean_df.isnull().sum().to_dict(),
            'data_processamento': pd.Timestamp.now().isoformat()
        }
        
        # Estatísticas por tipo de residência
        if 'tipo_residencia' in clean_df.columns:
            self.quality_report['distribuicao_tipos'] = clean_df['tipo_residencia'].value_counts().to_dict()
        
        # Estatísticas de valores segurados
        if 'valor_segurado' in clean_df.columns:
            self.quality_report['estatisticas_valores'] = {
                'media': round(clean_df['valor_segurado'].mean(), 2),
                'mediana': round(clean_df['valor_segurado'].median(), 2),
                'minimo': round(clean_df['valor_segurado'].min(), 2),
                'maximo': round(clean_df['valor_segurado'].max(), 2)
            }
    
    def get_quality_report(self) -> Dict:
        """Retorna o relatório de qualidade"""
        return self.quality_report
    
    def save_processed_data(self, df: pd.DataFrame, output_path: str, 
                          include_report: bool = True):
        """
        Salva dados processados em arquivo
        
        Args:
            df: DataFrame processado
            output_path: Caminho para salvar
            include_report: Se deve salvar relatório junto
        """
        # Salvar dados
        if output_path.endswith('.csv'):
            df.to_csv(output_path, index=False, encoding='utf-8')
        elif output_path.endswith('.xlsx'):
            df.to_excel(output_path, index=False)
        elif output_path.endswith('.json'):
            df.to_json(output_path, orient='records', date_format='iso')
        
        logger.info(f"Dados salvos em: {output_path}")
        
        # Salvar relatório se solicitado
        if include_report and self.quality_report:
            report_path = output_path.replace('.csv', '_report.json')
            report_path = report_path.replace('.xlsx', '_report.json')
            report_path = report_path.replace('.json', '_report.json')
            
            import json
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.quality_report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Relatório salvo em: {report_path}")
    
    def process_batch_files(self, input_directory: str, output_directory: str,
                          file_pattern: str = "*.csv") -> Dict[str, str]:
        """
        Processa múltiplos arquivos em lote
        
        Args:
            input_directory: Diretório de entrada
            output_directory: Diretório de saída
            file_pattern: Padrão dos arquivos a processar
            
        Returns:
            Dicionário com status de cada arquivo
        """
        import glob
        
        # Criar diretório de saída se não existir
        os.makedirs(output_directory, exist_ok=True)
        
        # Encontrar arquivos
        pattern_path = os.path.join(input_directory, file_pattern)
        files = glob.glob(pattern_path)
        
        results = {}
        
        for file_path in files:
            try:
                filename = os.path.basename(file_path)
                logger.info(f"Processando: {filename}")
                
                # Processar arquivo
                processed_df = self.load_and_process(file_path)
                
                # Gerar nome de saída
                output_filename = f"processed_{filename}"
                output_path = os.path.join(output_directory, output_filename)
                
                # Salvar resultado
                self.save_processed_data(processed_df, output_path)
                
                results[filename] = 'Sucesso'
                
            except Exception as e:
                logger.error(f"Erro ao processar {filename}: {e}")
                results[filename] = f'Erro: {str(e)}'
        
        return results


# Exemplo de uso
if __name__ == "__main__":
    processor = PolicyDataProcessor()
    
    # Exemplo de processamento
    try:
        df = processor.load_and_process("data/raw/apolices_exemplo.csv")
        processor.save_processed_data(df, "data/processed/apolices_clean.csv")
        
        # Exibir relatório
        report = processor.get_quality_report()
        print("Relatório de Qualidade:")
        for key, value in report.items():
            print(f"  {key}: {value}")
            
    except FileNotFoundError:
        print("Arquivo de exemplo não encontrado. Crie dados de exemplo primeiro.")
    except Exception as e:
        print(f"Erro no processamento: {e}")