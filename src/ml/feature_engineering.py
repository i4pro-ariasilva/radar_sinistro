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
import sys
from pathlib import Path

# Adicionar path para módulo weather
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# Import do sistema de weather
try:
    from weather.weather_service import WeatherService
    from weather.weather_models import WeatherData
    WEATHER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Sistema de weather não disponível: {e}")
    WEATHER_AVAILABLE = False

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Classe responsável pela criação automática de features para o modelo ML"""
    
    def __init__(self, use_real_weather: bool = True, weather_cache_hours: int = 1):
        """
        Inicializa o Feature Engineer
        
        Args:
            use_real_weather: Se deve usar dados climáticos reais da API
            weather_cache_hours: TTL do cache climático em horas
        """
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.target_column = 'houve_sinistro'
        
        # Sistema de weather
        self.use_real_weather = use_real_weather and WEATHER_AVAILABLE
        self.weather_service = None
        
        if self.use_real_weather:
            try:
                self.weather_service = WeatherService(
                    cache_ttl_hours=weather_cache_hours,
                    cache_db_path="weather_cache.db"
                )
                # Reduzir log verboso - só logar na primeira inicialização
                if not hasattr(WeatherService, '_first_init_logged'):
                    logger.info("✅ WeatherService inicializado - Usando dados climáticos reais")
                    WeatherService._first_init_logged = True
            except Exception as e:
                logger.warning(f"❌ Falha ao inicializar WeatherService: {e}")
                self.use_real_weather = False
        
        if not self.use_real_weather:
            logger.info("⚠️  Usando dados climáticos simulados (fallback)")
        
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
        
        # 3. Features climáticas (reais da API ou simuladas)
        if df_clima is not None:
            features_df = self._add_climate_features(features_df, df_clima)
        else:
            # Usar dados climáticos reais da API se disponível, senão simular
            features_df = self._create_climate_features(features_df)
        
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
    
    def _create_climate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cria features climáticas usando dados reais da API ou simulados
        
        Args:
            df: DataFrame com dados das apólices (deve ter latitude/longitude)
            
        Returns:
            DataFrame com features climáticas adicionadas
        """
        if self.use_real_weather and self.weather_service:
            return self._create_real_climate_features(df)
        else:
            return self._create_simulated_climate_features(df)
    
    def _create_real_climate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cria features climáticas usando dados reais da API OpenMeteo"""
        df = df.copy()
        logger.info(f"🌤️  Buscando dados climáticos reais para {len(df)} localizações")
        
        # Contador de sucessos/falhas para estatísticas
        api_success_count = 0
        fallback_count = 0
        
        # Buscar dados climáticos para cada localização
        for idx, row in df.iterrows():
            try:
                # Obter coordenadas (devem estar disponíveis do _create_geographic_features)
                latitude = row.get('latitude')
                longitude = row.get('longitude')
                
                if pd.isna(latitude) or pd.isna(longitude):
                    logger.warning(f"Coordenadas faltantes para índice {idx}, usando fallback")
                    self._add_fallback_climate_data(df, idx, row)
                    fallback_count += 1
                    continue
                
                # Buscar dados climáticos reais
                weather_data = self.weather_service.get_weather_for_prediction(latitude, longitude)
                
                if weather_data and weather_data.source != "minimal_fallback":
                    # Usar dados reais da API
                    self._add_real_climate_data(df, idx, weather_data)
                    api_success_count += 1
                else:
                    # Fallback para dados simulados
                    self._add_fallback_climate_data(df, idx, row)
                    fallback_count += 1
                    
            except Exception as e:
                logger.warning(f"Erro ao buscar clima para índice {idx}: {e}")
                self._add_fallback_climate_data(df, idx, row)
                fallback_count += 1
        
        # Log de estatísticas
        total_requests = api_success_count + fallback_count
        if total_requests > 0:
            api_rate = (api_success_count / total_requests) * 100
            logger.info(f"📊 Dados climáticos: {api_success_count} API ({api_rate:.1f}%), {fallback_count} fallback")
        
        # Criar features derivadas dos dados climáticos
        df = self._create_derived_climate_features(df)
        
        return df
    
    def _add_real_climate_data(self, df: pd.DataFrame, idx: int, weather_data: WeatherData):
        """Adiciona dados climáticos reais ao DataFrame"""
        
        # Features básicas de temperatura
        df.loc[idx, 'temperatura_atual'] = weather_data.temperature_current or 22.0
        df.loc[idx, 'temperatura_max'] = weather_data.temperature_max or weather_data.temperature_current or 25.0
        df.loc[idx, 'temperatura_min'] = weather_data.temperature_min or weather_data.temperature_current or 18.0
        df.loc[idx, 'temperatura_sensacao'] = weather_data.temperature_apparent or weather_data.temperature_current or 22.0
        
        # Features de precipitação
        df.loc[idx, 'precipitacao_atual'] = weather_data.precipitation or 0.0
        df.loc[idx, 'chuva_atual'] = weather_data.rain or 0.0
        df.loc[idx, 'neve_atual'] = weather_data.snowfall or 0.0
        
        # Features atmosféricas
        df.loc[idx, 'umidade_atual'] = weather_data.humidity or 60.0
        df.loc[idx, 'pressao_atmosferica'] = weather_data.pressure_msl or 1013.0
        df.loc[idx, 'cobertura_nuvens'] = weather_data.cloud_cover or 50.0
        
        # Features de vento
        df.loc[idx, 'vento_velocidade'] = weather_data.wind_speed or 10.0
        df.loc[idx, 'vento_direcao'] = weather_data.wind_direction or 180.0
        df.loc[idx, 'vento_rajadas'] = weather_data.wind_gusts or weather_data.wind_speed or 10.0
        
        # Features históricas (últimos 7 dias)
        df.loc[idx, 'temp_max_7d'] = weather_data.temperature_max_7d or weather_data.temperature_max or 25.0
        df.loc[idx, 'temp_min_7d'] = weather_data.temperature_min_7d or weather_data.temperature_min or 18.0
        df.loc[idx, 'precipitacao_7d'] = weather_data.precipitation_sum_7d or 0.0
        
        # Features categóricas
        df.loc[idx, 'condicoes_tempo'] = weather_data.conditions.value if weather_data.conditions else 'partly_cloudy'
        df.loc[idx, 'codigo_tempo'] = weather_data.weather_code or 1
        
        # Metadados
        df.loc[idx, 'fonte_clima'] = weather_data.source
        df.loc[idx, 'clima_cache'] = weather_data.is_cached
    
    def _add_fallback_climate_data(self, df: pd.DataFrame, idx: int, row: pd.Series):
        """Adiciona dados climáticos simulados como fallback"""
        
        # Usar região para simular dados mais realísticos
        regiao = row.get('regiao_brasil', 'MG')
        latitude = row.get('latitude', -15.0)
        
        # Parâmetros regionais baseados na latitude
        if latitude < -25:  # Sul
            temp_base, chuva_base, umidade_base = 20, 120, 75
        elif latitude < -20:  # Sudeste
            temp_base, chuva_base, umidade_base = 24, 100, 65
        elif latitude < -10:  # Centro-Oeste
            temp_base, chuva_base, umidade_base = 27, 80, 60
        else:  # Norte/Nordeste
            temp_base, chuva_base, umidade_base = 29, 60, 70
        
        # Adicionar variação sazonal (simplificada)
        import datetime
        month = datetime.datetime.now().month
        if month in [12, 1, 2]:  # Verão
            temp_adj, chuva_mult = 3, 1.5
        elif month in [6, 7, 8]:  # Inverno
            temp_adj, chuva_mult = -3, 0.5
        else:
            temp_adj, chuva_mult = 0, 1.0
        
        # Features básicas com variação aleatória
        np.random.seed(42 + idx)  # Seed determinística por linha
        
        temp_atual = temp_base + temp_adj + np.random.normal(0, 2)
        df.loc[idx, 'temperatura_atual'] = temp_atual
        df.loc[idx, 'temperatura_max'] = temp_atual + np.random.uniform(2, 6)
        df.loc[idx, 'temperatura_min'] = temp_atual - np.random.uniform(2, 5)
        df.loc[idx, 'temperatura_sensacao'] = temp_atual + np.random.uniform(-2, 3)
        
        precipitacao = np.random.gamma(2, chuva_base * chuva_mult / 30)  # Para escala diária
        df.loc[idx, 'precipitacao_atual'] = precipitacao
        df.loc[idx, 'chuva_atual'] = precipitacao
        df.loc[idx, 'neve_atual'] = 0.0  # Raramente neve no Brasil
        
        df.loc[idx, 'umidade_atual'] = max(20, min(95, umidade_base + np.random.normal(0, 10)))
        df.loc[idx, 'pressao_atmosferica'] = np.random.normal(1013, 8)
        df.loc[idx, 'cobertura_nuvens'] = np.random.uniform(10, 90)
        
        vento_base = 15 if latitude < -20 else 12  # Sul tem mais vento
        df.loc[idx, 'vento_velocidade'] = np.random.gamma(2, vento_base/2)
        df.loc[idx, 'vento_direcao'] = np.random.uniform(0, 360)
        df.loc[idx, 'vento_rajadas'] = df.loc[idx, 'vento_velocidade'] * np.random.uniform(1.2, 2.0)
        
        # Histórico simulado
        df.loc[idx, 'temp_max_7d'] = temp_atual + np.random.uniform(3, 8)
        df.loc[idx, 'temp_min_7d'] = temp_atual - np.random.uniform(3, 6)
        df.loc[idx, 'precipitacao_7d'] = precipitacao * np.random.uniform(5, 15)
        
        # Categóricas simuladas
        if precipitacao > 5:
            condicoes = 'rain'
            codigo = 61
        elif df.loc[idx, 'cobertura_nuvens'] > 80:
            condicoes = 'overcast'
            codigo = 3
        else:
            condicoes = 'partly_cloudy'
            codigo = 1
            
        df.loc[idx, 'condicoes_tempo'] = condicoes
        df.loc[idx, 'codigo_tempo'] = codigo
        df.loc[idx, 'fonte_clima'] = 'simulated_fallback'
        df.loc[idx, 'clima_cache'] = False
    
    def _create_derived_climate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cria features derivadas dos dados climáticos básicos"""
        
        # Índices de risco climático
        df['indice_tempestade'] = (df['precipitacao_atual'] * df['vento_velocidade']) / 100
        df['indice_calor'] = df['temperatura_atual'] + (df['umidade_atual'] / 100) * 5
        df['amplitude_termica'] = df['temperatura_max'] - df['temperatura_min']
        df['amplitude_7d'] = df['temp_max_7d'] - df['temp_min_7d']
        
        # Features binárias de risco
        df['temp_extrema'] = ((df['temperatura_atual'] > 35) | (df['temperatura_atual'] < 5)).astype(int)
        df['chuva_intensa'] = (df['precipitacao_atual'] > 20).astype(int)
        df['vento_forte'] = (df['vento_velocidade'] > 40).astype(int)
        df['umidade_extrema'] = ((df['umidade_atual'] > 90) | (df['umidade_atual'] < 30)).astype(int)
        df['pressao_anormal'] = ((df['pressao_atmosferica'] > 1025) | (df['pressao_atmosferica'] < 1000)).astype(int)
        
        # Features de tendência histórica
        df['tendencia_temperatura'] = df['temperatura_atual'] - ((df['temp_max_7d'] + df['temp_min_7d']) / 2)
        df['precipitacao_concentrada'] = (df['precipitacao_atual'] / df['precipitacao_7d']).fillna(0)
        
        # Score de risco climático geral (0-1)
        risk_components = [
            (df['indice_tempestade'] / 100).clip(0, 1),
            (df['chuva_intensa']).astype(float),
            (df['vento_forte']).astype(float),
            (df['temp_extrema']).astype(float),
            (df['pressao_anormal']).astype(float) * 0.5
        ]
        df['risco_climatico_geral'] = sum(risk_components) / len(risk_components)
        
        return df
    
    def _create_simulated_climate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cria features climáticas simuladas compatíveis com as novas features reais"""
        df = df.copy()
        np.random.seed(42)  # Para reprodutibilidade
        
        # Mapear campos antigos para novos (compatibilidade)
        for idx, row in df.iterrows():
            regiao = row.get('regiao_brasil', 'MG')
            
            # Parâmetros por região
            if 'RJ' in regiao or 'SP' in regiao:
                temp_base, chuva_base, vento_base, umidade_base = 25, 100, 15, 65
            elif 'BA' in regiao or 'PE' in regiao:
                temp_base, chuva_base, vento_base, umidade_base = 28, 60, 12, 70
            elif 'RS' in regiao or 'SC' in regiao:
                temp_base, chuva_base, vento_base, umidade_base = 20, 120, 20, 75
            else:
                temp_base, chuva_base, vento_base, umidade_base = 26, 80, 15, 65
            
            # Features básicas compatíveis com versão real
            temp_atual = np.random.normal(temp_base, 3)
            df.loc[idx, 'temperatura_atual'] = temp_atual
            df.loc[idx, 'temperatura_max'] = temp_atual + np.random.uniform(2, 6)
            df.loc[idx, 'temperatura_min'] = temp_atual - np.random.uniform(2, 5)
            df.loc[idx, 'temperatura_sensacao'] = temp_atual + np.random.uniform(-2, 3)
            
            precipitacao = np.random.gamma(2, chuva_base/20)  # Escala para mm/dia
            df.loc[idx, 'precipitacao_atual'] = precipitacao
            df.loc[idx, 'chuva_atual'] = precipitacao
            df.loc[idx, 'neve_atual'] = 0.0
            
            df.loc[idx, 'umidade_atual'] = np.random.normal(umidade_base, 10)
            df.loc[idx, 'pressao_atmosferica'] = np.random.normal(1013, 8)
            df.loc[idx, 'cobertura_nuvens'] = np.random.uniform(20, 80)
            
            vento = np.random.gamma(2, vento_base/2)
            df.loc[idx, 'vento_velocidade'] = vento
            df.loc[idx, 'vento_direcao'] = np.random.uniform(0, 360)
            df.loc[idx, 'vento_rajadas'] = vento * np.random.uniform(1.2, 2.0)
            
            # Histórico simulado
            df.loc[idx, 'temp_max_7d'] = temp_atual + np.random.uniform(3, 8)
            df.loc[idx, 'temp_min_7d'] = temp_atual - np.random.uniform(3, 6)
            df.loc[idx, 'precipitacao_7d'] = precipitacao * np.random.uniform(5, 15)
            
            # Categóricas
            df.loc[idx, 'condicoes_tempo'] = 'rain' if precipitacao > 5 else 'partly_cloudy'
            df.loc[idx, 'codigo_tempo'] = 61 if precipitacao > 5 else 1
            df.loc[idx, 'fonte_clima'] = 'simulated_legacy'
            df.loc[idx, 'clima_cache'] = False
        
        # Criar features derivadas usando a mesma função
        df = self._create_derived_climate_features(df)
        
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
        
        # Remover valores nulos apenas das colunas que existem
        existing_features = [col for col in self.feature_columns if col in df.columns]
        required_columns = existing_features + [self.target_column] if self.target_column in df.columns else existing_features
        
        if required_columns:
            df = df.dropna(subset=required_columns)
        
        # Atualizar feature_columns apenas com colunas que existem
        self.feature_columns = existing_features
        
        return df
    
    def prepare_model_data(self, df: pd.DataFrame, test_size: float = 0.3) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Prepara dados para treinamento do modelo
        
        Returns:
            X_train, X_test, y_train, y_test
        """
        X = df[self.feature_columns]
        y = df[self.target_column]

        # Split train/test - verificar se podemos estratificar
        # Para estratificar, cada classe precisa ter pelo menos 2 exemplos
        value_counts = y.value_counts()
        min_class_count = value_counts.min()
        
        # Só estratificar se todas as classes têm pelo menos 2 exemplos
        stratify_param = y if len(y.unique()) > 1 and min_class_count >= 2 else None
        
        if stratify_param is None:
            logger.warning("Não é possível estratificar: classes insuficientes ou com poucos exemplos")
            logger.info(f"Distribuição das classes: {value_counts.to_dict()}")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=stratify_param
        )        # Normalizar features numéricas
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
        """Transforma novos dados para predição (SEM coluna target)"""
        logger.info("Transformando dados para predição...")
        
        # Fazer cópia para não alterar original
        df_pred = df.copy()
        
        # Aplicar mesmas transformações do treinamento (sem target)
        df_pred = self._create_policy_features(df_pred)
        df_pred = self._create_geographic_features(df_pred)
        df_pred = self._create_climate_features(df_pred)  # Usar nova função que escolhe real ou simulado
        
        # Limpeza especial para predição (sem tentar acessar target)
        df_pred = self._clean_features_for_prediction(df_pred)
        
        # Selecionar apenas as features do modelo
        if hasattr(self, 'feature_columns') and self.feature_columns:
            # Garantir que todas as features necessárias existem
            missing_features = []
            for col in self.feature_columns:
                if col not in df_pred.columns:
                    missing_features.append(col)
                    df_pred[col] = 0  # Adicionar com valor padrão
            
            if missing_features:
                logger.warning(f"Features faltantes preenchidas com 0: {missing_features}")
            
            # Selecionar apenas as features do modelo
            df_pred = df_pred[self.feature_columns]
        else:
            # Se não tem feature_columns, usar colunas numéricas
            numeric_cols = df_pred.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns
            df_pred = df_pred[numeric_cols]
        
        # Aplicar scaling se disponível
        if hasattr(self, 'scaler') and self.scaler:
            df_pred_scaled = self.scaler.transform(df_pred)
            df_pred = pd.DataFrame(df_pred_scaled, columns=df_pred.columns, index=df_pred.index)
        
        logger.info(f"Dados transformados para predição: {df_pred.shape}")
        return df_pred
    
    def _clean_features_for_prediction(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa features para predição (sem tentar acessar target)"""
        # Colunas a remover (identificadores e strings)
        cols_to_remove = [
            'numero_apolice', 'cep', 'tipo_residencia', 'data_contratacao',
            'cep_clean', 'cep_regiao', 'cep_subregiao', 'cep_setor', 'regiao_brasil',
            # NÃO incluir 'houve_sinistro' pois não existe em predições
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
                df[col] = df[col].astype('int64') // 10**9
        
        # Garantir que todas as colunas são numéricas
        for col in df.columns:
            if df[col].dtype not in ['int64', 'float64', 'int32', 'float32']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remover NaN
        df = df.fillna(0)
        
        return df
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
