"""
Módulo para carregamento de diferentes tipos de arquivo
"""

import pandas as pd
import json
import os
from typing import Union, Dict, Any
import logging
import chardet

logger = logging.getLogger(__name__)


class FileLoader:
    """Classe para carregamento de arquivos de diferentes formatos"""
    
    def __init__(self):
        self.supported_formats = ['csv', 'xlsx', 'xls', 'json', 'parquet']
    
    def load_file(self, file_path: str, file_type: str = 'auto') -> pd.DataFrame:
        """
        Carrega arquivo de qualquer formato suportado
        
        Args:
            file_path: Caminho para o arquivo
            file_type: Tipo do arquivo ('csv', 'excel', 'json', 'auto')
            
        Returns:
            DataFrame com os dados carregados
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        # Detectar tipo automaticamente se necessário
        if file_type == 'auto':
            file_type = self._detect_file_type(file_path)
        
        logger.info(f"Carregando arquivo {file_path} como {file_type}")
        
        # Carregar baseado no tipo
        if file_type == 'csv':
            return self._load_csv(file_path)
        elif file_type in ['xlsx', 'xls', 'excel']:
            return self._load_excel(file_path)
        elif file_type == 'json':
            return self._load_json(file_path)
        elif file_type == 'parquet':
            return self._load_parquet(file_path)
        else:
            raise ValueError(f"Tipo de arquivo não suportado: {file_type}")
    
    def _detect_file_type(self, file_path: str) -> str:
        """Detecta o tipo do arquivo pela extensão"""
        _, extension = os.path.splitext(file_path.lower())
        
        type_mapping = {
            '.csv': 'csv',
            '.xlsx': 'xlsx',
            '.xls': 'xls',
            '.json': 'json',
            '.parquet': 'parquet'
        }
        
        return type_mapping.get(extension, 'csv')
    
    def _detect_encoding(self, file_path: str) -> str:
        """Detecta encoding do arquivo automaticamente"""
        try:
            with open(file_path, 'rb') as file:
                sample = file.read(10000)  # Lê os primeiros 10KB
                result = chardet.detect(sample)
                encoding = result['encoding']
                confidence = result['confidence']
                
                logger.info(f"Encoding detectado: {encoding} (confiança: {confidence:.2f})")
                
                # Se confiança baixa, usar UTF-8 como padrão
                if confidence < 0.7:
                    logger.warning("Baixa confiança na detecção. Usando UTF-8 como padrão.")
                    return 'utf-8'
                
                return encoding
        except Exception as e:
            logger.warning(f"Erro na detecção de encoding: {e}. Usando UTF-8.")
            return 'utf-8'
    
    def _load_csv(self, file_path: str) -> pd.DataFrame:
        """Carrega arquivo CSV com detecção automática de parâmetros"""
        
        # Detectar encoding
        encoding = self._detect_encoding(file_path)
        
        # Tentar diferentes separadores
        separators = [',', ';', '\t', '|']
        
        for separator in separators:
            try:
                # Ler uma amostra para testar
                sample_df = pd.read_csv(
                    file_path, 
                    sep=separator, 
                    encoding=encoding,
                    nrows=5
                )
                
                # Se conseguiu ler e tem mais de 1 coluna, provavelmente é o separador correto
                if len(sample_df.columns) > 1:
                    logger.info(f"Separador detectado: '{separator}'")
                    
                    # Carregar arquivo completo
                    df = pd.read_csv(
                        file_path,
                        sep=separator,
                        encoding=encoding,
                        low_memory=False,
                        na_values=['', 'NA', 'N/A', 'null', 'NULL', 'None', '-']
                    )
                    
                    logger.info(f"CSV carregado: {len(df)} linhas, {len(df.columns)} colunas")
                    return df
                    
            except Exception as e:
                logger.debug(f"Falhou com separador '{separator}': {e}")
                continue
        
        # Se nenhum separador funcionou, tentar padrão
        try:
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                low_memory=False,
                na_values=['', 'NA', 'N/A', 'null', 'NULL', 'None', '-']
            )
            logger.info(f"CSV carregado com configuração padrão: {len(df)} linhas")
            return df
        except Exception as e:
            raise ValueError(f"Não foi possível carregar CSV: {e}")
    
    def _load_excel(self, file_path: str) -> pd.DataFrame:
        """Carrega arquivo Excel"""
        try:
            # Verificar se tem múltiplas planilhas
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            logger.info(f"Planilhas encontradas: {sheet_names}")
            
            # Se tem múltiplas planilhas, usar a primeira ou a que parece ter dados
            if len(sheet_names) > 1:
                # Tentar encontrar planilha com dados (maior que outras)
                largest_sheet = None
                max_rows = 0
                
                for sheet in sheet_names:
                    try:
                        temp_df = pd.read_excel(file_path, sheet_name=sheet, nrows=1000)
                        if len(temp_df) > max_rows:
                            max_rows = len(temp_df)
                            largest_sheet = sheet
                    except:
                        continue
                
                sheet_to_use = largest_sheet or sheet_names[0]
                logger.info(f"Usando planilha: {sheet_to_use}")
            else:
                sheet_to_use = sheet_names[0]
            
            # Carregar planilha selecionada
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_to_use,
                na_values=['', 'NA', 'N/A', 'null', 'NULL', 'None', '-']
            )
            
            logger.info(f"Excel carregado: {len(df)} linhas, {len(df.columns)} colunas")
            return df
            
        except Exception as e:
            raise ValueError(f"Erro ao carregar Excel: {e}")
    
    def _load_json(self, file_path: str) -> pd.DataFrame:
        """Carrega arquivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Se é lista de objetos, converter diretamente
            if isinstance(data, list):
                df = pd.DataFrame(data)
            
            # Se é objeto com chave que contém os dados
            elif isinstance(data, dict):
                # Procurar chave que parece conter dados tabulares
                possible_keys = ['data', 'records', 'items', 'results', 'apolices']
                
                data_key = None
                for key in possible_keys:
                    if key in data and isinstance(data[key], list):
                        data_key = key
                        break
                
                if data_key:
                    df = pd.DataFrame(data[data_key])
                    logger.info(f"Dados encontrados na chave: {data_key}")
                else:
                    # Tentar usar os dados como estão
                    df = pd.json_normalize(data)
            
            else:
                raise ValueError("Formato JSON não reconhecido")
            
            logger.info(f"JSON carregado: {len(df)} linhas, {len(df.columns)} colunas")
            return df
            
        except Exception as e:
            raise ValueError(f"Erro ao carregar JSON: {e}")
    
    def _load_parquet(self, file_path: str) -> pd.DataFrame:
        """Carrega arquivo Parquet"""
        try:
            df = pd.read_parquet(file_path)
            logger.info(f"Parquet carregado: {len(df)} linhas, {len(df.columns)} colunas")
            return df
        except Exception as e:
            raise ValueError(f"Erro ao carregar Parquet: {e}")
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Retorna informações sobre o arquivo
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Dicionário com informações
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        file_stats = os.stat(file_path)
        file_type = self._detect_file_type(file_path)
        
        info = {
            'path': file_path,
            'size_bytes': file_stats.st_size,
            'size_mb': round(file_stats.st_size / (1024 * 1024), 2),
            'type': file_type,
            'modified': file_stats.st_mtime,
            'exists': True
        }
        
        # Se é arquivo texto, detectar encoding
        if file_type in ['csv', 'json']:
            info['encoding'] = self._detect_encoding(file_path)
        
        return info
    
    def preview_file(self, file_path: str, rows: int = 5) -> pd.DataFrame:
        """
        Carrega apenas algumas linhas para preview
        
        Args:
            file_path: Caminho do arquivo
            rows: Número de linhas para carregar
            
        Returns:
            DataFrame com preview
        """
        file_type = self._detect_file_type(file_path)
        
        if file_type == 'csv':
            encoding = self._detect_encoding(file_path)
            return pd.read_csv(file_path, encoding=encoding, nrows=rows)
        
        elif file_type in ['xlsx', 'xls']:
            return pd.read_excel(file_path, nrows=rows)
        
        elif file_type == 'json':
            # Para JSON, carregar tudo e pegar primeiras linhas
            df = self._load_json(file_path)
            return df.head(rows)
        
        elif file_type == 'parquet':
            df = pd.read_parquet(file_path)
            return df.head(rows)
        
        else:
            raise ValueError(f"Tipo não suportado para preview: {file_type}")
    
    def validate_file_structure(self, file_path: str, 
                               expected_columns: list = None) -> Dict[str, Any]:
        """
        Valida estrutura básica do arquivo
        
        Args:
            file_path: Caminho do arquivo
            expected_columns: Lista de colunas esperadas
            
        Returns:
            Dicionário com resultado da validação
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'info': {}
        }
        
        try:
            # Carregar preview
            preview_df = self.preview_file(file_path, 10)
            
            result['info'] = {
                'columns': list(preview_df.columns),
                'column_count': len(preview_df.columns),
                'sample_rows': len(preview_df),
                'data_types': preview_df.dtypes.to_dict()
            }
            
            # Verificar colunas esperadas se fornecidas
            if expected_columns:
                missing_columns = set(expected_columns) - set(preview_df.columns)
                if missing_columns:
                    result['valid'] = False
                    result['errors'].append(f"Colunas faltantes: {missing_columns}")
                
                extra_columns = set(preview_df.columns) - set(expected_columns)
                if extra_columns:
                    result['warnings'].append(f"Colunas extras: {extra_columns}")
            
            # Verificar se tem dados
            if len(preview_df) == 0:
                result['valid'] = False
                result['errors'].append("Arquivo está vazio")
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Erro ao validar arquivo: {str(e)}")
        
        return result


# Exemplo de uso
if __name__ == "__main__":
    loader = FileLoader()
    
    # Testar com arquivo de exemplo
    try:
        # Informações do arquivo
        info = loader.get_file_info("data/sample/sample_policies.csv")
        print("Informações do arquivo:", info)
        
        # Preview
        preview = loader.preview_file("data/sample/sample_policies.csv", 3)
        print("\nPreview:")
        print(preview)
        
        # Carregamento completo
        df = loader.load_file("data/sample/sample_policies.csv")
        print(f"\nCarregado: {len(df)} registros")
        
    except Exception as e:
        print(f"Erro: {e}")
