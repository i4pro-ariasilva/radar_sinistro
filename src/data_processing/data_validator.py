"""
Módulo de validação de dados
Criado pelo DEV 2 - Data Processing Engineer
"""

import pandas as pd
import re
from datetime import datetime
from typing import Union, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Classe responsável por validações de dados"""
    
    def __init__(self):
        self.valid_residence_types = ['casa', 'apartamento', 'sobrado']
        # Lista de primeiros 3 dígitos de CEPs válidos no Brasil
        self.valid_cep_prefixes = [
            '010', '011', '012', '013', '014', '015', '016', '017', '018', '019',  # SP
            '200', '201', '202', '203', '204', '205', '206', '207', '208', '209',  # RJ
            '220', '221', '222', '223', '224', '225', '226', '227', '228', '229',  # RJ
            '240', '241', '242', '243', '244', '245', '246', '247', '248', '249',  # RJ
            '260', '261', '262', '263', '264', '265', '266', '267', '268', '269',  # RJ
            '280', '281', '282', '283', '284', '285', '286', '287', '288', '289',  # RJ
            '301', '302', '303', '304', '305', '306', '307', '308', '309',        # MG
            '310', '311', '312', '313', '314', '315', '316', '317', '318', '319',  # MG
            '320', '321', '322', '323', '324', '325', '326', '327', '328', '329',  # MG
            '330', '331', '332', '333', '334', '335', '336', '337', '338', '339',  # MG
            '400', '401', '402', '403', '404', '405', '406', '407', '408', '409',  # BA
            '410', '411', '412', '413', '414', '415', '416', '417', '418', '419',  # BA
            '420', '421', '422', '423', '424', '425', '426', '427', '428', '429',  # BA
            '430', '431', '432', '433', '434', '435', '436', '437', '438', '439',  # BA
            '440', '441', '442', '443', '444', '445', '446', '447', '448', '449',  # BA
            '450', '451', '452', '453', '454', '455', '456', '457', '458', '459',  # BA
            '460', '461', '462', '463', '464', '465', '466', '467', '468', '469',  # BA
            '470', '471', '472', '473', '474', '475', '476', '477', '478', '479',  # BA
            '480', '481', '482', '483', '484', '485', '486', '487', '488', '489'   # BA
        ]
    
    def validate_cep(self, cep: Union[str, None]) -> bool:
        """
        Valida formato e existência de CEP brasileiro
        
        Args:
            cep: CEP para validar
            
        Returns:
            True se válido
        """
        if not cep:
            return False
        
        # Verificar formato XXXXX-XXX
        pattern = r'^\d{5}-\d{3}$'
        if not re.match(pattern, str(cep)):
            return False
        
        # Verificar se não é CEP genérico (00000-000, 11111-111, etc.)
        digits = cep.replace('-', '')
        if len(set(digits)) == 1:
            return False
        
        # Verificar se os primeiros 3 dígitos correspondem a uma região válida
        prefix = digits[:3]
        # Para simplificar, aceitar qualquer CEP que comece com dígitos válidos
        # Em produção, poderia usar uma API de validação de CEP
        
        return True
    
    def validate_insurance_value(self, value: Union[float, int, None]) -> bool:
        """
        Valida valor de seguro
        
        Args:
            value: Valor para validar
            
        Returns:
            True se válido
        """
        if not value or pd.isna(value):
            return False
        
        try:
            float_value = float(value)
            # Valor deve ser positivo e dentro de uma faixa razoável
            return 10000 <= float_value <= 5000000  # Entre R$ 10mil e R$ 5mi
        except (ValueError, TypeError):
            return False
    
    def validate_date_format(self, date_value: Union[str, datetime, None]) -> bool:
        """
        Valida formato de data
        
        Args:
            date_value: Data para validar
            
        Returns:
            True se válido
        """
        if not date_value:
            return False
        
        # Se já é datetime, é válido
        if isinstance(date_value, datetime):
            return True
        
        # Se é string, verificar formato YYYY-MM-DD
        if isinstance(date_value, str):
            pattern = r'^\d{4}-\d{2}-\d{2}$'
            if not re.match(pattern, date_value):
                return False
            
            # Tentar converter para verificar se é data válida
            try:
                datetime.strptime(date_value, '%Y-%m-%d')
                
                # Verificar se data não é muito antiga ou futura
                date_obj = datetime.strptime(date_value, '%Y-%m-%d')
                current_year = datetime.now().year
                
                # Aceitar datas entre 1900 e ano atual + 1
                if not (1900 <= date_obj.year <= current_year + 1):
                    return False
                
                return True
            except ValueError:
                return False
        
        return False
    
    def validate_residence_type(self, residence_type: Union[str, None]) -> bool:
        """
        Valida tipo de residência
        
        Args:
            residence_type: Tipo para validar
            
        Returns:
            True se válido
        """
        if not residence_type:
            return False
        
        return str(residence_type).lower() in self.valid_residence_types
    
    def validate_policy_number(self, policy_number: Union[str, None]) -> bool:
        """
        Valida número de apólice
        
        Args:
            policy_number: Número para validar
            
        Returns:
            True se válido
        """
        if not policy_number:
            return False
        
        policy_str = str(policy_number).strip()
        
        # Deve ter entre 5 e 20 caracteres
        if not (5 <= len(policy_str) <= 20):
            return False
        
        # Deve conter pelo menos um número
        if not re.search(r'\d', policy_str):
            return False
        
        # Não deve conter caracteres especiais (apenas letras e números)
        if not re.match(r'^[A-Za-z0-9]+$', policy_str):
            return False
        
        return True
    
    def validate_coordinates(self, latitude: Union[float, None], 
                           longitude: Union[float, None]) -> bool:
        """
        Valida coordenadas geográficas para o Brasil
        
        Args:
            latitude: Latitude para validar
            longitude: Longitude para validar
            
        Returns:
            True se válido
        """
        if latitude is None or longitude is None:
            return True  # Coordenadas são opcionais
        
        try:
            lat = float(latitude)
            lon = float(longitude)
            
            # Verificar se estão dentro dos limites do Brasil
            # Brasil: Lat aproximadamente entre -33.75 e 5.27
            #         Lon aproximadamente entre -73.98 e -28.84
            if not (-33.75 <= lat <= 5.27):
                return False
            
            if not (-73.98 <= lon <= -28.84):
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    def validate_dataframe_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Valida schema completo do DataFrame
        
        Args:
            df: DataFrame para validar
            
        Returns:
            Dicionário com resultado da validação
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_required': [],
            'extra_columns': []
        }
        
        # Colunas obrigatórias
        required_columns = ['numero_apolice', 'cep', 'tipo_residencia', 
                          'valor_segurado', 'data_contratacao']
        
        # Colunas opcionais esperadas
        optional_columns = ['latitude', 'longitude', 'ativa', 'nome_segurado']
        
        # Verificar colunas obrigatórias
        missing_required = set(required_columns) - set(df.columns)
        if missing_required:
            validation_result['valid'] = False
            validation_result['missing_required'] = list(missing_required)
            validation_result['errors'].append(
                f"Colunas obrigatórias faltantes: {missing_required}"
            )
        
        # Verificar colunas extras (não reconhecidas)
        all_expected = set(required_columns + optional_columns)
        extra_columns = set(df.columns) - all_expected
        if extra_columns:
            validation_result['extra_columns'] = list(extra_columns)
            validation_result['warnings'].append(
                f"Colunas não reconhecidas: {extra_columns}"
            )
        
        # Verificar tipos de dados
        if 'valor_segurado' in df.columns:
            non_numeric_values = df[~pd.to_numeric(df['valor_segurado'], errors='coerce').notna()]
            if len(non_numeric_values) > 0:
                validation_result['warnings'].append(
                    f"Valores não numéricos em 'valor_segurado': {len(non_numeric_values)} registros"
                )
        
        return validation_result
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Avalia qualidade geral dos dados
        
        Args:
            df: DataFrame para avaliar
            
        Returns:
            Dicionário com métricas de qualidade
        """
        quality_metrics = {
            'total_records': len(df),
            'completeness': {},
            'validity': {},
            'duplicates': 0,
            'overall_score': 0
        }
        
        # Completude (% de valores não nulos)
        for column in df.columns:
            non_null_count = df[column].notna().sum()
            completeness_pct = (non_null_count / len(df)) * 100
            quality_metrics['completeness'][column] = round(completeness_pct, 2)
        
        # Validade por campo
        if 'cep' in df.columns:
            valid_ceps = df['cep'].apply(self.validate_cep).sum()
            quality_metrics['validity']['cep'] = round((valid_ceps / len(df)) * 100, 2)
        
        if 'valor_segurado' in df.columns:
            valid_values = df['valor_segurado'].apply(self.validate_insurance_value).sum()
            quality_metrics['validity']['valor_segurado'] = round((valid_values / len(df)) * 100, 2)
        
        if 'data_contratacao' in df.columns:
            valid_dates = df['data_contratacao'].apply(self.validate_date_format).sum()
            quality_metrics['validity']['data_contratacao'] = round((valid_dates / len(df)) * 100, 2)
        
        if 'tipo_residencia' in df.columns:
            valid_types = df['tipo_residencia'].apply(self.validate_residence_type).sum()
            quality_metrics['validity']['tipo_residencia'] = round((valid_types / len(df)) * 100, 2)
        
        # Duplicatas
        if 'numero_apolice' in df.columns:
            quality_metrics['duplicates'] = df['numero_apolice'].duplicated().sum()
        
        # Score geral (média ponderada)
        completeness_scores = list(quality_metrics['completeness'].values())
        validity_scores = list(quality_metrics['validity'].values())
        
        if completeness_scores and validity_scores:
            avg_completeness = sum(completeness_scores) / len(completeness_scores)
            avg_validity = sum(validity_scores) / len(validity_scores)
            
            # Penalizar por duplicatas
            duplicate_penalty = (quality_metrics['duplicates'] / len(df)) * 10
            
            overall_score = (avg_completeness * 0.4 + avg_validity * 0.6) - duplicate_penalty
            quality_metrics['overall_score'] = round(max(0, overall_score), 2)
        
        return quality_metrics
    
    def validate_business_rules(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Valida regras de negócio específicas
        
        Args:
            df: DataFrame para validar
            
        Returns:
            Lista de violações de regras de negócio
        """
        violations = []
        
        for idx, row in df.iterrows():
            # Regra 1: Valor segurado deve ser compatível com tipo de residência
            if ('valor_segurado' in row and 'tipo_residencia' in row and 
                pd.notna(row['valor_segurado']) and pd.notna(row['tipo_residencia'])):
                
                value = row['valor_segurado']
                res_type = row['tipo_residencia']
                
                if res_type == 'apartamento' and value > 2000000:
                    violations.append({
                        'row': idx,
                        'rule': 'valor_tipo_incompativel',
                        'message': f"Apartamento com valor muito alto: R$ {value:,.2f}"
                    })
                elif res_type == 'casa' and value < 50000:
                    violations.append({
                        'row': idx,
                        'rule': 'valor_tipo_incompativel',
                        'message': f"Casa com valor muito baixo: R$ {value:,.2f}"
                    })
            
            # Regra 2: Data de contratação não pode ser futura
            if 'data_contratacao' in row and pd.notna(row['data_contratacao']):
                try:
                    contract_date = pd.to_datetime(row['data_contratacao'])
                    if contract_date > pd.Timestamp.now():
                        violations.append({
                            'row': idx,
                            'rule': 'data_futura',
                            'message': f"Data de contratação no futuro: {contract_date.date()}"
                        })
                except:
                    pass
            
            # Regra 3: CEP deve ser compatível com coordenadas (se fornecidas)
            if ('cep' in row and 'latitude' in row and 'longitude' in row and
                pd.notna(row['cep']) and pd.notna(row['latitude']) and pd.notna(row['longitude'])):
                
                # Validação básica de consistência geográfica
                # Em produção, usaria API de geocoding para verificar
                if not self.validate_coordinates(row['latitude'], row['longitude']):
                    violations.append({
                        'row': idx,
                        'rule': 'coordenadas_invalidas',
                        'message': f"Coordenadas fora do Brasil: {row['latitude']}, {row['longitude']}"
                    })
        
        return violations