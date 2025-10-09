"""
🗺️ MÓDULO COMPLETO DE MAPA DE CALOR - RADAR DE SINISTRO
Sistema de Visualização Geográfica de Riscos por CEP

Este módulo contém TODA a funcionalidade necessária para:
- Geocodificação de CEPs brasileiros
- Criação de mapas de calor interativos
- Visualização de riscos por região
- Cache inteligente para performance

Autor: Sistema Radar de Sinistro v3.0
Data: Outubro 2025
"""

import os
import json
import time
import requests
import folium
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from typing import Optional, Tuple, Dict, Any
from datetime import datetime


class OSMGeocoder:
    """
    Geocodificador usando OpenStreetMap (OSM) Nominatim
    
    Funcionalidades:
    - Conversão de CEPs brasileiros em coordenadas lat/lng
    - Cache inteligente para evitar requisições repetidas
    - Rate limiting respeitoso com API gratuita
    - Tratamento de erros robusto
    """
    
    def __init__(self, cache_dir: str = "cache"):
        """
        Inicializa o geocodificador
        
        Args:
            cache_dir: Diretório para armazenar cache de geocodificação
        """
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RadarSinistro/3.0 (sistema.radar@empresa.com)'
        })
        
        # Configuração do cache
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "geocoding_cache.json")
        self.cache = self._load_cache()
        
        # Estatísticas
        self.stats = {
            'cache_hits': 0,
            'api_calls': 0,
            'errors': 0
        }
    
    def _load_cache(self) -> Dict[str, Tuple[float, float]]:
        """Carrega cache de geocodificação do disco"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Converter listas de volta para tuplas
                    return {k: tuple(v) for k, v in data.items()}
            except Exception:
                return {}
        return {}
    
    def _save_cache(self) -> None:
        """Salva cache de geocodificação no disco"""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            # Converter tuplas para listas para JSON
            cache_data = {k: list(v) for k, v in self.cache.items()}
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Aviso: Não foi possível salvar cache: {e}")
    
    def _clean_cep(self, cep: str) -> str:
        """Remove formatação do CEP"""
        return ''.join(filter(str.isdigit, cep))
    
    def geocode_cep(self, cep: str) -> Optional[Tuple[float, float]]:
        """
        Geocodifica CEP brasileiro usando OpenStreetMap
        
        Args:
            cep: CEP no formato "12345-678" ou "12345678"
            
        Returns:
            Tupla (latitude, longitude) ou None se não encontrado
        """
        # Limpar e validar CEP
        clean_cep = self._clean_cep(cep)
        
        if len(clean_cep) != 8:
            self.stats['errors'] += 1
            return None
        
        # Verificar cache primeiro
        if clean_cep in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[clean_cep]
        
        try:
            # Formatar CEP para busca
            formatted_cep = f"{clean_cep[:5]}-{clean_cep[5:]}"
            
            # Parâmetros para API do OpenStreetMap
            params = {
                'q': f'{formatted_cep}, Brasil',
                'format': 'json',
                'countrycodes': 'br',
                'limit': 1,
                'addressdetails': 1
            }
            
            # Fazer requisição
            response = self.session.get(
                self.base_url, 
                params=params, 
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            self.stats['api_calls'] += 1
            
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                coords = (lat, lon)
                
                # Salvar no cache
                self.cache[clean_cep] = coords
                self._save_cache()
                
                return coords
            
            return None
            
        except Exception as e:
            self.stats['errors'] += 1
            return None
        
        finally:
            # Rate limiting respeitoso (1 segundo entre requisições)
            time.sleep(1)
    
    def geocode_batch(self, ceps: list) -> Dict[str, Optional[Tuple[float, float]]]:
        """
        Geocodifica múltiplos CEPs de uma vez
        
        Args:
            ceps: Lista de CEPs para geocodificar
            
        Returns:
            Dicionário {cep: (lat, lon)} ou {cep: None}
        """
        results = {}
        
        for i, cep in enumerate(ceps):
            results[cep] = self.geocode_cep(cep)
            
            # Mostrar progresso no Streamlit se disponível
            try:
                if hasattr(st, 'progress'):
                    progress = (i + 1) / len(ceps)
                    st.progress(progress, f"Geocodificando CEPs: {i+1}/{len(ceps)}")
            except:
                pass
        
        return results
    
    def get_stats(self) -> Dict[str, int]:
        """Retorna estatísticas de uso do geocodificador"""
        total_requests = self.stats['cache_hits'] + self.stats['api_calls']
        
        return {
            'total_requests': total_requests,
            'cache_hits': self.stats['cache_hits'],
            'api_calls': self.stats['api_calls'],
            'cache_hit_rate': self.stats['cache_hits'] / max(total_requests, 1) * 100,
            'errors': self.stats['errors']
        }


class MapaCalorRiscos:
    """
    Gerador de Mapas de Calor para Visualização de Riscos
    
    Funcionalidades:
    - Mapas interativos com Folium
    - Classificação visual por níveis de risco
    - Popups informativos por região
    - Legenda automática
    - Múltiplas camadas de visualização
    """
    
    def __init__(self, geocoder: OSMGeocoder = None):
        """
        Inicializa o gerador de mapas
        
        Args:
            geocoder: Instância do geocodificador (opcional)
        """
        self.geocoder = geocoder or OSMGeocoder()
        
        # Configurações de risco
        self.risk_levels = {
            'muito_baixo': {'min': 0, 'max': 25, 'color': '#388e3c', 'label': 'Muito Baixo'},
            'baixo': {'min': 25, 'max': 50, 'color': '#fbc02d', 'label': 'Baixo'},
            'medio': {'min': 50, 'max': 75, 'color': '#f57c00', 'label': 'Médio'},
            'alto': {'min': 75, 'max': 100, 'color': '#d32f2f', 'label': 'Alto'}
        }
        
        # Configurações do mapa
        self.map_config = {
            'center_brazil': [-15.7942, -47.8822],
            'default_zoom': 5,
            'tiles': ['OpenStreetMap', 'CartoDB positron'],
            'popup_width': 300,
            'min_marker_size': 8,
            'max_marker_size': 25
        }
    
    def _get_risk_config(self, score: float) -> Dict[str, Any]:
        """
        Retorna configuração de cor e label baseada no score de risco
        
        Args:
            score: Score de risco (0-100)
            
        Returns:
            Dicionário com configurações do risco
        """
        for level, config in self.risk_levels.items():
            if config['min'] <= score < config['max']:
                return config
        
        # Fallback para scores >= 100
        return self.risk_levels['alto']
    
    def _calculate_marker_size(self, count: int, max_count: int) -> int:
        """
        Calcula tamanho do marcador baseado na quantidade de apólices
        
        Args:
            count: Número de apólices no CEP
            max_count: Máximo de apólices em qualquer CEP
            
        Returns:
            Tamanho do marcador em pixels
        """
        min_size = self.map_config['min_marker_size']
        max_size = self.map_config['max_marker_size']
        
        if max_count <= 1:
            return min_size
        
        normalized = (count - 1) / (max_count - 1)
        return int(min_size + (max_size - min_size) * normalized)
    
    def _create_popup_html(self, cep: str, data: Dict[str, Any]) -> str:
        """
        Cria HTML personalizado para popup do marcador
        
        Args:
            cep: CEP da região
            data: Dados agregados do CEP
            
        Returns:
            HTML formatado para popup
        """
        risk_config = self._get_risk_config(data['risk_score'])
        
        html = f"""
        <div style='min-width: 250px; font-family: Arial, sans-serif;'>
            <h4 style='margin: 0 0 10px 0; color: #1e3c72; border-bottom: 2px solid #1e3c72; padding-bottom: 5px;'>
                📍 CEP: {cep}
            </h4>
            
            <div style='margin: 8px 0;'>
                <span style='font-weight: bold; color: {risk_config["color"]};'>🎯 Nível de Risco:</span><br>
                <span style='color: {risk_config["color"]}; font-size: 16px; font-weight: bold;'>
                    {data['risk_score']:.1f} - {risk_config["label"]}
                </span>
            </div>
            
            <div style='margin: 8px 0;'>
                <span style='font-weight: bold; color: #424242;'>📋 Apólices:</span><br>
                <span style='font-size: 16px;'>{data['policy_count']} apólices cadastradas</span>
            </div>
            
            <div style='margin: 8px 0;'>
                <span style='font-weight: bold; color: #424242;'>💰 Valor Total:</span><br>
                <span style='font-size: 16px; color: #2e7d32;'>R$ {data['total_value']:,.0f}</span>
            </div>
            
            <div style='margin: 8px 0;'>
                <span style='font-weight: bold; color: #424242;'>📊 Valor Médio:</span><br>
                <span style='font-size: 14px;'>R$ {data['avg_value']:,.0f} por apólice</span>
            </div>
        </div>
        """
        
        return html
    
    def _create_legend_html(self) -> str:
        """
        Cria HTML da legenda do mapa
        
        Returns:
            HTML formatado para legenda
        """
        legend_items = []
        
        for level, config in self.risk_levels.items():
            legend_items.append(
                f"<p style='margin: 3px 0;'>"
                f"<span style='color:{config['color']}; font-size: 16px; font-weight: bold;'>●</span> "
                f"{config['label']} ({config['min']}-{config['max']})"
                f"</p>"
            )
        
        html = f"""
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 220px; height: 140px; 
                    background-color: white; border: 2px solid grey; z-index: 9999; 
                    font-size: 14px; padding: 10px; box-shadow: 0 0 15px rgba(0,0,0,0.2);
                    border-radius: 5px;">
            <h4 style='margin: 0 0 10px 0; color: #1e3c72; text-align: center;'>
                🎯 Classificação de Risco
            </h4>
            {''.join(legend_items)}
        </div>
        """
        
        return html
    
    def criar_mapa_calor(self, policies_df: pd.DataFrame) -> str:
        """
        Cria mapa de calor interativo baseado nos dados das apólices
        
        Args:
            policies_df: DataFrame com colunas: cep, risk_score, insured_value
            
        Returns:
            HTML do mapa para renderização no Streamlit
        """
        if policies_df.empty:
            return self._create_empty_map_html()
        
        # Validar colunas necessárias
        required_columns = ['cep', 'risk_score', 'insured_value']
        missing_columns = [col for col in required_columns if col not in policies_df.columns]
        
        if missing_columns:
            st.error(f"Colunas obrigatórias faltando: {missing_columns}")
            return self._create_empty_map_html()
        
        # Agregar dados por CEP
        cep_data = self._aggregate_data_by_cep(policies_df)
        
        if cep_data.empty:
            return self._create_empty_map_html()
        
        # Criar mapa base
        mapa = self._create_base_map()
        
        # Adicionar marcadores
        success_count = self._add_markers_to_map(mapa, cep_data)
        
        # Adicionar legenda
        legend_html = self._create_legend_html()
        mapa.get_root().html.add_child(folium.Element(legend_html))
        
        # Adicionar controle de camadas
        folium.LayerControl().add_to(mapa)
        
        # Exibir estatísticas no Streamlit
        self._show_geocoding_stats(len(cep_data), success_count)
        
        return mapa._repr_html_()
    
    def _aggregate_data_by_cep(self, policies_df: pd.DataFrame) -> pd.DataFrame:
        """Agrega dados das apólices por CEP"""
        try:
            # Limpar dados
            df_clean = policies_df.dropna(subset=['cep', 'risk_score', 'insured_value'])
            df_clean = df_clean[df_clean['cep'] != '']
            
            # Converter tipos
            df_clean['risk_score'] = pd.to_numeric(df_clean['risk_score'], errors='coerce')
            df_clean['insured_value'] = pd.to_numeric(df_clean['insured_value'], errors='coerce')
            
            # Remover valores inválidos
            df_clean = df_clean.dropna(subset=['risk_score', 'insured_value'])
            
            # Agregar por CEP
            cep_aggregated = df_clean.groupby('cep').agg({
                'risk_score': 'mean',
                'insured_value': ['sum', 'mean', 'count']
            }).round(2)
            
            # Flatten colunas
            cep_aggregated.columns = ['risk_score', 'total_value', 'avg_value', 'policy_count']
            cep_aggregated = cep_aggregated.reset_index()
            
            return cep_aggregated
            
        except Exception as e:
            st.error(f"Erro ao agregar dados: {e}")
            return pd.DataFrame()
    
    def _create_base_map(self) -> folium.Map:
        """Cria mapa base do Brasil"""
        mapa = folium.Map(
            location=self.map_config['center_brazil'],
            zoom_start=self.map_config['default_zoom'],
            tiles=self.map_config['tiles'][0]
        )
        
        # Adicionar tiles alternativos
        for tile_name in self.map_config['tiles'][1:]:
            folium.TileLayer(tile_name, name=tile_name).add_to(mapa)
        
        return mapa
    
    def _add_markers_to_map(self, mapa: folium.Map, cep_data: pd.DataFrame) -> int:
        """Adiciona marcadores ao mapa e retorna número de sucessos"""
        success_count = 0
        max_policies = cep_data['policy_count'].max()
        
        for _, row in cep_data.iterrows():
            coords = self.geocoder.geocode_cep(row['cep'])
            
            if coords:
                success_count += 1
                risk_config = self._get_risk_config(row['risk_score'])
                marker_size = self._calculate_marker_size(row['policy_count'], max_policies)
                
                popup_html = self._create_popup_html(row['cep'], row)
                
                folium.CircleMarker(
                    location=coords,
                    radius=marker_size,
                    popup=folium.Popup(popup_html, max_width=self.map_config['popup_width']),
                    tooltip=f"CEP {row['cep']} - Risco: {row['risk_score']:.1f}",
                    color=risk_config['color'],
                    fillColor=risk_config['color'],
                    fillOpacity=0.7,
                    weight=2
                ).add_to(mapa)
        
        return success_count
    
    def _create_empty_map_html(self) -> str:
        """Retorna HTML para mapa vazio"""
        return """
        <div style='text-align: center; padding: 50px; background: #f5f5f5; border-radius: 10px;'>
            <h3 style='color: #666;'>🗺️ Mapa não disponível</h3>
            <p style='color: #888;'>
                Nenhuma apólice com CEP válido encontrada.<br>
                Adicione apólices em 'Gerenciar Apólices' para visualizar o mapa.
            </p>
        </div>
        """
    
    def _show_geocoding_stats(self, total_ceps: int, geocoded_ceps: int) -> None:
        """Exibe estatísticas de geocodificação no Streamlit"""
        failed_ceps = total_ceps - geocoded_ceps
        
        if failed_ceps > 0:
            st.info(
                f"📊 **Geocodificação:** {geocoded_ceps} sucessos, {failed_ceps} falhas "
                f"({geocoded_ceps/total_ceps*100:.1f}% de sucesso)"
            )
        
        # Mostrar estatísticas do geocodificador
        stats = self.geocoder.get_stats()
        if stats['total_requests'] > 0:
            st.caption(
                f"📈 Cache: {stats['cache_hit_rate']:.1f}% de acertos "
                f"({stats['cache_hits']}/{stats['total_requests']} requisições)"
            )


def criar_interface_streamlit(policies_df: pd.DataFrame = None) -> None:
    """
    Cria interface completa do mapa no Streamlit
    
    Args:
        policies_df: DataFrame com dados das apólices (opcional)
    """
    st.header("🗺️ Mapa de Calor - Distribuição de Riscos por CEP")
    st.markdown(
        "Visualização geográfica interativa dos riscos de sinistros "
        "baseada nos CEPs das apólices cadastradas."
    )
    
    # Informações e controles
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("🎯 **Mapa Interativo:** Clique nos círculos para ver detalhes de cada região")
    
    with col2:
        if st.button("🔄 Atualizar Mapa", use_container_width=True):
            st.rerun()
    
    # Gerar dados de exemplo se não fornecidos
    if policies_df is None:
        policies_df = _gerar_dados_exemplo()
        st.warning("📊 Usando dados de exemplo. Integre com seu sistema para dados reais.")
    
    if policies_df.empty:
        st.warning("📭 Nenhuma apólice cadastrada encontrada no sistema")
        
        # Sugestão de ação
        st.markdown("### 💡 Como adicionar dados:")
        st.markdown("""
        1. **Cadastre apólices** com CEPs válidos
        2. **Certifique-se** que as colunas necessárias existem:
           - `cep`: CEP da propriedade
           - `risk_score`: Score de risco (0-100)
           - `insured_value`: Valor segurado
        3. **Recarregue** esta página
        """)
        return
    
    # Métricas resumidas
    _exibir_metricas_resumo(policies_df)
    
    # Gerar e exibir mapa
    st.markdown("---")
    
    with st.spinner("🔄 Gerando mapa de calor... (Pode levar alguns segundos para geocodificar CEPs)"):
        try:
            # Criar instâncias
            geocoder = OSMGeocoder()
            mapa_generator = MapaCalorRiscos(geocoder)
            
            # Gerar mapa
            mapa_html = mapa_generator.criar_mapa_calor(policies_df)
            
            # Renderizar mapa
            components.html(mapa_html, height=650, scrolling=False)
            
            st.success(f"✅ Mapa gerado com sucesso para {len(policies_df)} apólices")
            
        except Exception as e:
            st.error(f"❌ Erro ao gerar mapa: {e}")
            
            # Fallback: mostrar dados em tabela
            _exibir_fallback_tabela(policies_df)


def _gerar_dados_exemplo() -> pd.DataFrame:
    """Gera dados de exemplo para demonstração"""
    import numpy as np
    
    # Configurar seed para dados consistentes
    np.random.seed(42)
    
    # CEPs de exemplo (regiões conhecidas do Brasil)
    ceps_exemplo = [
        '01310-100',  # São Paulo - SP
        '04038-001',  # São Paulo - SP
        '20040-020',  # Rio de Janeiro - RJ
        '22071-900',  # Rio de Janeiro - RJ
        '30112-000',  # Belo Horizonte - MG
        '31270-901',  # Belo Horizonte - MG
        '80010-000',  # Curitiba - PR
        '80230-130',  # Curitiba - PR
        '90010-150',  # Porto Alegre - RS
        '91040-001',  # Porto Alegre - RS
        '40070-110',  # Salvador - BA
        '41770-395',  # Salvador - BA
        '60160-230',  # Fortaleza - CE
        '60811-905',  # Fortaleza - CE
        '50030-230',  # Recife - PE
        '52061-160',  # Recife - PE
        '70040-010',  # Brasília - DF
        '72405-610',  # Brasília - DF
        '69020-160',  # Manaus - AM
        '69083-000',  # Manaus - AM
    ]
    
    # Gerar dados aleatórios
    dados = []
    for i, cep in enumerate(ceps_exemplo * 3):  # Triplicar para ter mais dados
        dados.append({
            'cep': cep,
            'risk_score': np.random.uniform(10, 90),
            'insured_value': np.random.uniform(100000, 800000),
            'policy_id': f'EX-{i+1:04d}'
        })
    
    return pd.DataFrame(dados)


def _exibir_metricas_resumo(policies_df: pd.DataFrame) -> None:
    """Exibe métricas resumidas dos dados"""
    st.markdown("### 📊 Resumo dos Dados")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_policies = len(policies_df)
    unique_ceps = policies_df['cep'].nunique()
    avg_risk = policies_df['risk_score'].mean()
    high_risk_ceps = len(policies_df[policies_df['risk_score'] >= 75]['cep'].unique())
    
    with col1:
        st.metric("📋 Total de Apólices", f"{total_policies:,}")
    
    with col2:
        st.metric("📍 CEPs Únicos", f"{unique_ceps:,}")
    
    with col3:
        st.metric("🎯 Risco Médio", f"{avg_risk:.1f}")
    
    with col4:
        st.metric("🔴 CEPs Alto Risco", f"{high_risk_ceps:,}")


def _exibir_fallback_tabela(policies_df: pd.DataFrame) -> None:
    """Exibe dados em tabela como alternativa ao mapa"""
    st.markdown("### 📊 Dados das Apólices (Visualização Alternativa)")
    
    # Agregar dados por CEP
    summary_df = policies_df.groupby('cep').agg({
        'risk_score': 'mean',
        'insured_value': ['sum', 'count']
    }).round(2)
    
    # Flatten colunas
    summary_df.columns = ['risk_medio', 'valor_total', 'num_apolices']
    summary_df = summary_df.reset_index()
    
    # Adicionar classificação de risco
    def classify_risk(score):
        if score >= 75: return '🔴 Alto'
        elif score >= 50: return '🟡 Médio'
        elif score >= 25: return '🔵 Baixo'
        else: return '🟢 Muito Baixo'
    
    summary_df['nivel_risco'] = summary_df['risk_medio'].apply(classify_risk)
    
    # Ordenar por risco
    summary_df = summary_df.sort_values('risk_medio', ascending=False)
    
    # Exibir tabela
    st.dataframe(
        summary_df[['cep', 'nivel_risco', 'risk_medio', 'num_apolices', 'valor_total']],
        column_config={
            'cep': 'CEP',
            'nivel_risco': 'Nível de Risco',
            'risk_medio': 'Score Médio',
            'num_apolices': 'Nº Apólices',
            'valor_total': 'Valor Total (R$)'
        },
        use_container_width=True
    )


# Função principal para teste standalone
def main():
    """Função principal para executar o módulo como aplicação standalone"""
    st.set_page_config(
        page_title="Mapa de Calor - Radar de Sinistro",
        page_icon="🗺️",
        layout="wide"
    )
    
    st.title("🗺️ Módulo de Mapa de Calor - Radar de Sinistro")
    st.markdown("---")
    
    # Interface principal
    criar_interface_streamlit()
    
    # Informações técnicas
    with st.expander("ℹ️ Informações Técnicas"):
        st.markdown("""
        ### 🔧 Funcionalidades:
        - **Geocodificação**: Conversão automática de CEPs em coordenadas
        - **Cache Inteligente**: Armazena resultados para melhor performance
        - **Mapas Interativos**: Visualização com Folium e OpenStreetMap
        - **Classificação Visual**: Cores representam níveis de risco
        - **Popups Informativos**: Detalhes completos por região
        
        ### 📋 Dados Necessários:
        - `cep`: CEP da propriedade (formato: "12345-678")
        - `risk_score`: Score de risco (0-100)
        - `insured_value`: Valor segurado (numérico)
        
        ### 🎯 Classificação de Riscos:
        - **🟢 Muito Baixo**: 0-25
        - **🔵 Baixo**: 25-50  
        - **🟡 Médio**: 50-75
        - **🔴 Alto**: 75-100
        """)


if __name__ == "__main__":
    main()