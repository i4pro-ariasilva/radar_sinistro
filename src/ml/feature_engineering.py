"""
Feature Engineering para Sistema de Radar de Sinistro
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from typing import Tuple, List, Dict, Any
import logging
import joblib
import os

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Classe responsável pela criação automática de features para o modelo ML"""
    
    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.target_column = 'houve_sinistro'
        
    def create_features(self, df_apolices: pd.DataFrame, 
                       df_sinistros: pd.DataFrame = None,
                       df_clima: pd.DataFrame = None) -> pd.DataFrame:
        """
        Cria features automáticas a partir dos dados disponíveis
        
        Args:
            df_apolices: DataFrame com dados das apólices
            df_sinistros: DataFrame com histórico de sinistros (opcional)
            df_clima: DataFrame com dados climáticos (opcional)
            
        Returns:
            DataFrame com features criadas e target
        """
        logger.info("Iniciando criação de features...")
        
        # Começar com dados das apólices
        features_df = df_apolices.copy()
        
        # 1. Features básicas das apólices
        features_df = self._create_policy_features(features_df)
        
        # 2. Features geográficas do CEP
        features_df = self._create_geographic_features(features_df)
        
        # 3. Features climáticas se disponíveis
        if df_clima is not None:
            features_df = self._add_climate_features(features_df, df_clima)
        else:
            # Features climáticas simuladas para funcionar sem dados reais
            features_df = self._create_simulated_climate_features(features_df)
        
        # 4. Target (sinistro ou não) baseado no histórico
        if df_sinistros is not None:
            features_df = self._create_target_variable(features_df, df_sinistros)
        else:
            # Target simulado para funcionar sem dados históricos
            features_df = self._create_simulated_target(features_df)
        
        # 5. Limpeza final
        features_df = self._clean_features(features_df)
        
        logger.info(f"Features criadas: {len(features_df)} registros, {len(features_df.columns)} colunas")
        return features_df
    
    def _clean_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove colunas não numéricas e prepara dados para ML"""
        # Colunas a remover (identificadores e strings)
        cols_to_remove = [
            'numero_apolice', 'cep', 'tipo_residencia', 'data_contratacao',
            'cep_clean', 'cep_regiao', 'cep_subregiao', 'cep_setor', 'regiao_brasil'
        ]
        
        # Remover colunas que existem
        for col in cols_to_remove:
            if col in df.columns:
                df = df.drop(columns=[col])
        
        # Converter categóricos para numérico
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = pd.Categorical(df[col]).codes
            elif df[col].dtype == 'category':
                df[col] = df[col].cat.codes
        
        # Converter datetime para timestamp numérico
        for col in df.columns:
            if df[col].dtype == 'datetime64[ns]':
                df[col] = df[col].astype('int64') // 10**9  # segundos desde epoch
        
        # Garantir que todas as colunas são numéricas
        for col in df.columns:
            if df[col].dtype not in ['int64', 'float64', 'int32', 'float32']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remover NaN
        df = df.fillna(0)
        
        return df
    
    def _create_policy_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cria features básicas das apólices"""
        df = df.copy()
        
        # Valor segurado normalizado (log para reduzir skewness)
        df['valor_segurado_log'] = np.log1p(df['valor_segurado'])
        
        # Faixas de valor
        df['faixa_valor'] = pd.cut(df['valor_segurado'], 
                                  bins=[0, 200000, 400000, 600000, np.inf],
                                  labels=['baixo', 'medio', 'alto', 'premium'])
        
        # Idade da apólice (se tiver data_contratacao)
        if 'data_contratacao' in df.columns:
            df['data_contratacao'] = pd.to_datetime(df['data_contratacao'])
            df['idade_apolice_dias'] = (pd.Timestamp.now() - df['data_contratacao']).dt.days
            df['idade_apolice_anos'] = df['idade_apolice_dias'] / 365.25
        else:
            # Simular idade da apólice
            df['idade_apolice_dias'] = np.random.randint(30, 1095, len(df))  # 1 mês a 3 anos
            df['idade_apolice_anos'] = df['idade_apolice_dias'] / 365.25
        
        return df
    
    def _create_geographic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cria features baseadas na localização (CEP)"""
        df = df.copy()
        
        # Extrair informações do CEP
        df['cep_clean'] = df['cep'].str.replace('-', '')
        df['cep_regiao'] = df['cep_clean'].str[:1]  # Primeiro dígito = região
        df['cep_subregiao'] = df['cep_clean'].str[:2]  # Dois primeiros = sub-região
        df['cep_setor'] = df['cep_clean'].str[:3]  # Três primeiros = setor
        
        # Mapeamento de regiões brasileiras por CEP
        regiao_mapping = {
            '0': 'SP_Grande_SP',
            '1': 'SP_Interior', 
            '2': 'RJ_ES',
            '3': 'MG',
            '4': 'BA_SE',
            '5': 'PR_SC_RS',
            '6': 'PE_PB_RN_AL',
            '7': 'DF_GO_TO_MT_MS',
            '8': 'AC_AM_AP_PA_RO_RR',
            '9': 'MA_PI_CE'
        }
        
        df['regiao_brasil'] = df['cep_regiao'].map(regiao_mapping)
        
        # Features de risco por região (baseado em conhecimento geral)
        risco_regiao = {
            'SP_Grande_SP': 0.7,  # Alto risco urbano
            'SP_Interior': 0.4,
            'RJ_ES': 0.8,  # Alto risco (chuvas, encostas)
            'MG': 0.3,
            'BA_SE': 0.5,
            'PR_SC_RS': 0.6,  # Região de temporais
            'PE_PB_RN_AL': 0.6,
            'DF_GO_TO_MT_MS': 0.3,
            'AC_AM_AP_PA_RO_RR': 0.4,
            'MA_PI_CE': 0.5
        }
        
        df['risco_base_regiao'] = df['regiao_brasil'].map(risco_regiao).fillna(0.4)
        
        # Proximidade ao mar (baseado no CEP)
        ceps_costeiros = ['2', '4', '5', '6', '8', '9']  # Regiões com costa
        df['proximidade_mar'] = df['cep_regiao'].isin(ceps_costeiros).astype(int)
        
        return df
    
    def _add_climate_features(self, df: pd.DataFrame, df_clima: pd.DataFrame) -> pd.DataFrame:
        """Adiciona features climáticas reais se disponíveis"""
        # Por enquanto, usar features simuladas
        # Em produção, faria join com dados climáticos por lat/lon e data
        return self._create_simulated_climate_features(df)
    
    def _create_simulated_climate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cria features climáticas simuladas para o protótipo"""
        df = df.copy()
        np.random.seed(42)  # Para reprodutibilidade
        
        # Simular condições climáticas baseadas na região
        for idx, row in df.iterrows():
            regiao = row.get('regiao_brasil', 'MG')
            
            # Parâmetros por região
            if 'RJ' in regiao or 'SP' in regiao:
                temp_base, chuva_base, vento_base = 25, 100, 15
            elif 'BA' in regiao or 'PE' in regiao:
                temp_base, chuva_base, vento_base = 28, 60, 12
            elif 'RS' in regiao or 'SC' in regiao:
                temp_base, chuva_base, vento_base = 20, 120, 20
            else:
                temp_base, chuva_base, vento_base = 26, 80, 15
            
            # Adicionar variação aleatória
            df.loc[idx, 'temperatura_media'] = np.random.normal(temp_base, 3)
            df.loc[idx, 'precipitacao_30d'] = np.random.gamma(2, chuva_base/2)
            df.loc[idx, 'vento_max'] = np.random.gamma(2, vento_base/2)
            df.loc[idx, 'umidade_media'] = np.random.normal(70, 10)
        
        # Features derivadas do clima
        df['indice_tempestade'] = (df['precipitacao_30d'] * df['vento_max']) / 1000
        df['temp_extrema'] = ((df['temperatura_media'] > 35) | (df['temperatura_media'] < 10)).astype(int)
        df['chuva_intensa'] = (df['precipitacao_30d'] > 150).astype(int)
        df['vento_forte'] = (df['vento_max'] > 30).astype(int)
        
        return df
    
    def _create_target_variable(self, df: pd.DataFrame, df_sinistros: pd.DataFrame) -> pd.DataFrame:
        """Cria variável target baseada no histórico real de sinistros"""
        df = df.copy()
        
        # Marcar apólices que tiveram sinistro
        apolices_com_sinistro = df_sinistros['numero_apolice'].unique()
        df[self.target_column] = df['numero_apolice'].isin(apolices_com_sinistro).astype(int)
        
        return df
    
    def _create_simulated_target(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cria target simulado baseado nas features para o protótipo"""
        df = df.copy()
        np.random.seed(42)
        
        # Score de risco baseado nas features
        risk_score = (
            df['risco_base_regiao'] * 0.3 +
            df['indice_tempestade'] * 0.01 +
            df['temp_extrema'] * 0.2 +
            df['chuva_intensa'] * 0.3 +
            df['vento_forte'] * 0.2 +
            df['proximidade_mar'] * 0.1 +
            (df['faixa_valor'] == 'premium').astype(int) * 0.1
        )
        
        # Adicionar ruído e converter para probabilidade
        risk_score += np.random.normal(0, 0.1, len(df))
        risk_score = np.clip(risk_score, 0, 1)
        
        # Gerar target baseado na probabilidade (aprox 10% de sinistros)
        df[self.target_column] = (np.random.random(len(df)) < risk_score * 0.15).astype(int)
        
        return df
    
    def _clean_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpeza final e seleção de features"""
        df = df.copy()
        
        # Features finais para o modelo
        self.feature_columns = [
            'valor_segurado_log', 'idade_apolice_anos', 'risco_base_regiao',
            'proximidade_mar', 'temperatura_media', 'precipitacao_30d', 
            'vento_max', 'umidade_media', 'indice_tempestade',
            'temp_extrema', 'chuva_intensa', 'vento_forte'
        ]
        
        # Encoding de variáveis categóricas
        categorical_features = ['tipo_residencia', 'faixa_valor', 'regiao_brasil']
        
        for feature in categorical_features:
            if feature in df.columns:
                if feature not in self.label_encoders:
                    self.label_encoders[feature] = LabelEncoder()
                    df[f'{feature}_encoded'] = self.label_encoders[feature].fit_transform(df[feature])
                else:
                    df[f'{feature}_encoded'] = self.label_encoders[feature].transform(df[feature])
                
                self.feature_columns.append(f'{feature}_encoded')
        
        # Remover valores nulos
        df = df.dropna(subset=self.feature_columns + [self.target_column])
        
        return df
    
    def prepare_model_data(self, df: pd.DataFrame, test_size: float = 0.3) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Prepara dados para treinamento do modelo
        
        Returns:
            X_train, X_test, y_train, y_test
        """
        X = df[self.feature_columns]
        y = df[self.target_column]
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Normalizar features numéricas
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Converter de volta para DataFrame
        X_train = pd.DataFrame(X_train_scaled, columns=self.feature_columns, index=X_train.index)
        X_test = pd.DataFrame(X_test_scaled, columns=self.feature_columns, index=X_test.index)
        
        logger.info(f"Dados preparados: Train={len(X_train)}, Test={len(X_test)}")
        logger.info(f"Distribuição target train: {y_train.value_counts().to_dict()}")
        
        return X_train, X_test, y_train, y_test
    
    def save_preprocessors(self, model_dir: str):
        """Salva encoders e scaler para uso em produção"""
        os.makedirs(model_dir, exist_ok=True)
        
        # Salvar scaler
        joblib.dump(self.scaler, os.path.join(model_dir, 'scaler.pkl'))
        
        # Salvar label encoders
        joblib.dump(self.label_encoders, os.path.join(model_dir, 'label_encoders.pkl'))
        
        # Salvar lista de features
        joblib.dump(self.feature_columns, os.path.join(model_dir, 'feature_columns.pkl'))
        
        logger.info(f"Preprocessors salvos em {model_dir}")
    
    def load_preprocessors(self, model_dir: str):
        """Carrega encoders e scaler salvos"""
        self.scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
        self.label_encoders = joblib.load(os.path.join(model_dir, 'label_encoders.pkl'))
        self.feature_columns = joblib.load(os.path.join(model_dir, 'feature_columns.pkl'))
        
        logger.info(f"Preprocessors carregados de {model_dir}")
    
    def transform_new_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transforma novos dados usando preprocessors treinados"""
        # Aplicar mesmas transformações do treinamento
        df = self._create_policy_features(df)
        df = self._create_geographic_features(df)
        df = self._create_simulated_climate_features(df)
        df = self._clean_features(df)
        
        # Aplicar scaling
        X = df[self.feature_columns]
        X_scaled = self.scaler.transform(X)
        
        return pd.DataFrame(X_scaled, columns=self.feature_columns, index=df.index)


# Exemplo de uso para testes
if __name__ == "__main__":
    # Testar com dados simulados
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    from database import get_database, CRUDOperations
    
    try:
        # Carregar dados do banco
        db = get_database()
        crud = CRUDOperations(db)
        
        # Simular dados se banco vazio
        from database import SampleDataGenerator
        generator = SampleDataGenerator()
        policies = generator.generate_sample_policies(100)
        claims = generator.generate_sample_claims(policies, 20)
        
        df_policies = pd.DataFrame(policies)
        df_claims = pd.DataFrame(claims)
        
        # Testar feature engineering
        fe = FeatureEngineer()
        features_df = fe.create_features(df_policies, df_claims)
        
        print("Feature Engineering - Teste:")
        print(f"Shape: {features_df.shape}")
        print(f"Features: {fe.feature_columns}")
        print(f"Target distribution: {features_df['houve_sinistro'].value_counts()}")
        
    except Exception as e:
        print(f"Erro no teste: {e}")
        print("Execute o sistema completo primeiro para inicializar o banco.")