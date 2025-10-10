"""
Módulo de limpeza e normalização de dados
"""

import pandas as pd
import numpy as np
import re
from typing import Union, List
import logging

logger = logging.getLogger(__name__)


class DataCleaner:
    """Classe responsável pela limpeza e normalização de dados"""
    
    def __init__(self):
        self.residence_type_mapping = {
            'casa': 'casa',
            'casas': 'casa',
            'residencia': 'casa',
            'térrea': 'casa',
            'terrea': 'casa',
            'apartamento': 'apartamento',
            'apto': 'apartamento',
            'apt': 'apartamento',
            'ap': 'apartamento',
            'flat': 'apartamento',
            'sobrado': 'sobrado',
            'duplex': 'sobrado',
            'cobertura': 'apartamento'
        }
    
    def clean_cep(self, cep_series: pd.Series) -> pd.Series:
        """
        Limpa e normaliza CEPs para formato XXXXX-XXX
        
        Args:
            cep_series: Serie com CEPs
            
        Returns:
            Serie com CEPs normalizados
        """
        def normalize_single_cep(cep):
            if pd.isna(cep):
                return None
            
            # Converter para string e remover espaços
            cep_str = str(cep).strip()
            
            # Remover todos os caracteres não numéricos
            cep_digits = re.sub(r'[^\d]', '', cep_str)
            
            # Verificar se tem 8 dígitos
            if len(cep_digits) != 8:
                logger.warning(f"CEP inválido (não tem 8 dígitos): {cep}")
                return None
            
            # Formatar como XXXXX-XXX
            return f"{cep_digits[:5]}-{cep_digits[5:]}"
        
        return cep_series.apply(normalize_single_cep)
    
    def normalize_residence_type(self, type_series: pd.Series) -> pd.Series:
        """
        Normaliza tipos de residência
        
        Args:
            type_series: Serie com tipos de residência
            
        Returns:
            Serie com tipos normalizados
        """
        def normalize_single_type(residence_type):
            if pd.isna(residence_type):
                return None
            
            # Converter para string e limpar
            type_str = str(residence_type).lower().strip()
            
            # Remover acentos e caracteres especiais
            type_str = re.sub(r'[^\w\s]', '', type_str)
            
            # Buscar no mapeamento
            for key, value in self.residence_type_mapping.items():
                if key in type_str:
                    return value
            
            logger.warning(f"Tipo de residência não reconhecido: {residence_type}")
            return 'casa'  # Valor padrão
        
        return type_series.apply(normalize_single_type)
    
    def clean_monetary_values(self, value_series: pd.Series) -> pd.Series:
        """
        Limpa valores monetários removendo símbolos e formatação
        
        Args:
            value_series: Serie com valores monetários
            
        Returns:
            Serie com valores numéricos limpos
        """
        def clean_single_value(value):
            if pd.isna(value):
                return None
            
            # Se já é numérico, retornar como float
            if isinstance(value, (int, float)):
                return float(value)
            
            # Converter para string
            value_str = str(value).strip()
            
            # Remover símbolos de moeda (R$, $, etc.)
            value_str = re.sub(r'[R$\s]', '', value_str)
            
            # Tratar separadores decimais brasileiros (vírgula)
            # Se tem ponto E vírgula, assumir que vírgula é decimal
            if '.' in value_str and ',' in value_str:
                value_str = value_str.replace('.', '').replace(',', '.')
            elif ',' in value_str and value_str.count(',') == 1:
                # Se só tem uma vírgula, pode ser decimal
                parts = value_str.split(',')
                if len(parts[1]) <= 2:  # Máximo 2 casas decimais
                    value_str = value_str.replace(',', '.')
                else:
                    value_str = value_str.replace(',', '')
            
            # Tentar converter para float
            try:
                cleaned_value = float(value_str)
                if cleaned_value < 0:
                    logger.warning(f"Valor negativo encontrado: {value}")
                    return None
                return cleaned_value
            except ValueError:
                logger.warning(f"Não foi possível converter valor: {value}")
                return None
        
        return value_series.apply(clean_single_value)
    
    def clean_dates(self, date_series: pd.Series) -> pd.Series:
        """
        Limpa e normaliza datas para formato YYYY-MM-DD
        
        Args:
            date_series: Serie com datas
            
        Returns:
            Serie com datas normalizadas
        """
        def clean_single_date(date_value):
            if pd.isna(date_value):
                return None
            
            # Se já é datetime, converter para string
            if isinstance(date_value, pd.Timestamp):
                return date_value.strftime('%Y-%m-%d')
            
            # Converter para string
            date_str = str(date_value).strip()
            
            # Tentar vários formatos comuns
            formats_to_try = [
                '%Y-%m-%d',      # 2024-01-15
                '%d/%m/%Y',      # 15/01/2024
                '%d-%m-%Y',      # 15-01-2024
                '%d/%m/%y',      # 15/01/24
                '%d-%m-%y',      # 15-01-24
                '%Y/%m/%d',      # 2024/01/15
                '%Y.%m.%d',      # 2024.01.15
                '%d.%m.%Y',      # 15.01.2024
            ]
            
            for date_format in formats_to_try:
                try:
                    parsed_date = pd.to_datetime(date_str, format=date_format)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # Tentar parsing automático do pandas
            try:
                parsed_date = pd.to_datetime(date_str, dayfirst=True)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                logger.warning(f"Não foi possível converter data: {date_value}")
                return None
        
        return date_series.apply(clean_single_date)
    
    def clean_policy_numbers(self, policy_series: pd.Series) -> pd.Series:
        """
        Limpa números de apólice removendo espaços e caracteres inválidos
        
        Args:
            policy_series: Serie com números de apólice
            
        Returns:
            Serie com números limpos
        """
        def clean_single_policy(policy_number):
            if pd.isna(policy_number):
                return None
            
            # Converter para string e remover espaços
            policy_str = str(policy_number).strip().upper()
            
            # Remover caracteres especiais, manter apenas letras e números
            policy_str = re.sub(r'[^A-Z0-9]', '', policy_str)
            
            if len(policy_str) == 0:
                logger.warning(f"Número de apólice vazio após limpeza: {policy_number}")
                return None
            
            return policy_str
        
        return policy_series.apply(clean_single_policy)
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Trata valores faltantes de acordo com regras de negócio
        
        Args:
            df: DataFrame com dados
            
        Returns:
            DataFrame com valores faltantes tratados
        """
        df_clean = df.copy()
        
        # Para campos obrigatórios, remover linhas com valores nulos
        required_fields = ['numero_apolice', 'cep', 'tipo_residencia', 'valor_segurado']
        
        initial_count = len(df_clean)
        for field in required_fields:
            if field in df_clean.columns:
                df_clean = df_clean.dropna(subset=[field])
        
        removed_count = initial_count - len(df_clean)
        if removed_count > 0:
            logger.warning(f"Removidas {removed_count} linhas por campos obrigatórios vazios")
        
        # Para campos opcionais, preencher com valores padrão
        if 'ativa' in df_clean.columns:
            df_clean['ativa'] = df_clean['ativa'].fillna(True)
        
        # Coordenadas podem ficar nulas (serão preenchidas pelo geocoding)
        # Nome do segurado pode ficar nulo
        
        return df_clean
    
    def remove_outliers(self, df: pd.DataFrame, column: str, 
                       method: str = 'iqr', factor: float = 1.5) -> pd.DataFrame:
        """
        Remove outliers de uma coluna numérica
        
        Args:
            df: DataFrame
            column: Nome da coluna
            method: Método ('iqr' ou 'zscore')
            factor: Fator de tolerância
            
        Returns:
            DataFrame sem outliers
        """
        if column not in df.columns:
            return df
        
        df_clean = df.copy()
        initial_count = len(df_clean)
        
        if method == 'iqr':
            Q1 = df_clean[column].quantile(0.25)
            Q3 = df_clean[column].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - factor * IQR
            upper_bound = Q3 + factor * IQR
            
            df_clean = df_clean[
                (df_clean[column] >= lower_bound) & 
                (df_clean[column] <= upper_bound)
            ]
        
        elif method == 'zscore':
            from scipy import stats
            z_scores = np.abs(stats.zscore(df_clean[column]))
            df_clean = df_clean[z_scores < factor]
        
        removed_count = initial_count - len(df_clean)
        if removed_count > 0:
            logger.info(f"Removidos {removed_count} outliers da coluna {column}")
        
        return df_clean
    
    def standardize_text_fields(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Padroniza campos de texto (maiúscula, sem espaços extras)
        
        Args:
            df: DataFrame
            columns: Lista de colunas para padronizar
            
        Returns:
            DataFrame com campos padronizados
        """
        df_clean = df.copy()
        
        for column in columns:
            if column in df_clean.columns:
                df_clean[column] = df_clean[column].astype(str).str.strip().str.title()
        
        return df_clean
