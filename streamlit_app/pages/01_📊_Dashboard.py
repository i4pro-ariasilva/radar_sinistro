"""
Dashboard Principal - Sistema de Radar de Risco Climático
Página com visão geral, métricas e status do sistema
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Radar Climático",
    page_icon="📊",
    layout="wide"
)

# Adicionar path do projeto
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

def load_data():
    """Carrega dados do banco de dados"""
    try:
        from database import get_database, CRUDOperations
        
        db = get_database()
        crud = CRUDOperations(db)
        
        # Buscar dados das apólices
        apolices = crud.get_all_apolices()
        
        # Buscar dados de sinistros
        sinistros = crud.get_all_sinistros()
        
        return apolices, sinistros
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return [], []

def create_metrics_cards(apolices, sinistros):
    """Cria cards com métricas principais"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Total de apólices
    with col1:
        total_apolices = len(apolices)
        st.metric(
            label="📋 Total de Apólices",
            value=f"{total_apolices:,}",
            delta=f"+{total_apolices//10}" if total_apolices > 0 else None
        )
    
    # Total de sinistros
    with col2:
        total_sinistros = len(sinistros)
        st.metric(
            label="⚠️ Total de Sinistros",
            value=f"{total_sinistros:,}",
            delta=f"-{total_sinistros//20}" if total_sinistros > 0 else None,
            delta_color="inverse"
        )
    
    # Valor total segurado
    with col3:
        if apolices:
            valor_total = sum(float(apolice.valor_segurado or 0) for apolice in apolices)
            st.metric(
                label="💰 Valor Total Segurado",
                value=f"R$ {valor_total/1_000_000:.1f}M",
                delta=f"+R$ {valor_total/10_000_000:.1f}M"
            )
        else:
            st.metric(label="💰 Valor Total Segurado", value="R$ 0")
    
    # Taxa de sinistralidade
    with col4:
        if total_apolices > 0:
            taxa_sinistro = (total_sinistros / total_apolices) * 100
            st.metric(
                label="📈 Taxa de Sinistralidade",
                value=f"{taxa_sinistro:.1f}%",
                delta=f"{taxa_sinistro-5:.1f}%" if taxa_sinistro > 5 else f"+{5-taxa_sinistro:.1f}%",
                delta_color="inverse" if taxa_sinistro > 5 else "normal"
            )
        else:
            st.metric(label="📈 Taxa de Sinistralidade", value="0%")

def create_apolices_charts(apolices):
    """Cria gráficos relacionados às apólices"""
    
    if not apolices:
        st.warning("Nenhuma apólice encontrada. Gere dados de exemplo primeiro.")
        return
    
    # Converter para DataFrame
    df_apolices = pd.DataFrame([{
        'numero_apolice': a.numero_apolice,
        'cep': a.cep,
        'tipo_residencia': a.tipo_residencia,
        'valor_segurado': float(a.valor_segurado or 0),
        'data_contratacao': a.data_contratacao,
        'latitude': a.latitude,
        'longitude': a.longitude
    } for a in apolices])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribuição por Tipo de Residência")
        
        # Gráfico de pizza
        tipo_counts = df_apolices['tipo_residencia'].value_counts()
        
        fig_pie = px.pie(
            values=tipo_counts.values,
            names=tipo_counts.index,
            title="Distribuição de Apólices por Tipo",
            color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        )
        
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("📈 Valor Segurado por Tipo")
        
        # Gráfico de barras
        valor_por_tipo = df_apolices.groupby('tipo_residencia')['valor_segurado'].sum().reset_index()
        valor_por_tipo['valor_milhoes'] = valor_por_tipo['valor_segurado'] / 1_000_000
        
        fig_bar = px.bar(
            valor_por_tipo,
            x='tipo_residencia',
            y='valor_milhoes',
            title="Valor Total Segurado por Tipo (R$ Milhões)",
            color='valor_milhoes',
            color_continuous_scale='blues'
        )
        
        fig_bar.update_layout(
            xaxis_title="Tipo de Residência",
            yaxis_title="Valor (R$ Milhões)",
            showlegend=False
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)

def create_temporal_analysis(apolices, sinistros):
    """Cria análise temporal dos dados"""
    
    if not apolices and not sinistros:
        return
    
    st.subheader("📅 Análise Temporal")
    
    # Gráfico de linha temporal
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=['Apólices Contratadas por Mês', 'Sinistros por Mês'],
        vertical_spacing=0.1
    )
    
    if apolices:
        # Processar dados de apólices
        df_apolices = pd.DataFrame([{
            'data': a.data_contratacao,
            'valor': float(a.valor_segurado or 0)
        } for a in apolices if a.data_contratacao])
        
        if not df_apolices.empty:
            df_apolices['data'] = pd.to_datetime(df_apolices['data'])
            df_apolices['mes'] = df_apolices['data'].dt.to_period('M')
            
            apolices_mes = df_apolices.groupby('mes').size().reset_index(name='count')
            apolices_mes['mes_str'] = apolices_mes['mes'].astype(str)
            
            fig.add_trace(
                go.Scatter(
                    x=apolices_mes['mes_str'],
                    y=apolices_mes['count'],
                    mode='lines+markers',
                    name='Apólices',
                    line=dict(color='#1f77b4', width=3)
                ),
                row=1, col=1
            )
    
    if sinistros:
        # Processar dados de sinistros
        df_sinistros = pd.DataFrame([{
            'data': s.data_sinistro,
            'valor': float(s.valor_prejuizo or 0)
        } for s in sinistros if s.data_sinistro])
        
        if not df_sinistros.empty:
            df_sinistros['data'] = pd.to_datetime(df_sinistros['data'])
            df_sinistros['mes'] = df_sinistros['data'].dt.to_period('M')
            
            sinistros_mes = df_sinistros.groupby('mes').size().reset_index(name='count')
            sinistros_mes['mes_str'] = sinistros_mes['mes'].astype(str)
            
            fig.add_trace(
                go.Scatter(
                    x=sinistros_mes['mes_str'],
                    y=sinistros_mes['count'],
                    mode='lines+markers',
                    name='Sinistros',
                    line=dict(color='#ff7f0e', width=3)
                ),
                row=2, col=1
            )
    
    fig.update_layout(
        height=600,
        title_text="Evolução Temporal dos Dados",
        showlegend=False
    )
    
    fig.update_xaxes(title_text="Período", row=2, col=1)
    fig.update_yaxes(title_text="Quantidade", row=1, col=1)
    fig.update_yaxes(title_text="Quantidade", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)

def create_geographic_overview(apolices):
    """Cria visão geográfica das apólices"""
    
    if not apolices:
        return
    
    st.subheader("🗺️ Distribuição Geográfica")
    
    # Filtrar apólices com coordenadas
    apolices_geo = [a for a in apolices if a.latitude and a.longitude]
    
    if not apolices_geo:
        st.warning("Nenhuma apólice com coordenadas geográficas encontrada.")
        return
    
    # Criar DataFrame
    df_geo = pd.DataFrame([{
        'numero_apolice': a.numero_apolice,
        'latitude': float(a.latitude),
        'longitude': float(a.longitude),
        'valor_segurado': float(a.valor_segurado or 0),
        'tipo_residencia': a.tipo_residencia,
        'cep': a.cep
    } for a in apolices_geo])
    
    # Mapa de dispersão
    fig_map = px.scatter_mapbox(
        df_geo,
        lat='latitude',
        lon='longitude',
        size='valor_segurado',
        color='tipo_residencia',
        hover_data=['numero_apolice', 'cep', 'valor_segurado'],
        title="Localização das Apólices",
        mapbox_style='open-street-map',
        height=500,
        zoom=5
    )
    
    fig_map.update_layout(
        mapbox=dict(
            center=dict(lat=-15.7942, lon=-47.8822),  # Centro do Brasil
            zoom=4
        )
    )
    
    st.plotly_chart(fig_map, use_container_width=True)

def main():
    """Função principal da página"""
    
    st.title("📊 Dashboard Principal")
    st.markdown("Visão geral do Sistema de Radar de Risco Climático")
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        apolices, sinistros = load_data()
    
    if not apolices and not sinistros:
        st.error("""
        ❌ **Nenhum dado encontrado no sistema**
        
        Para começar, você precisa:
        1. Inicializar o sistema (se ainda não fez)
        2. Gerar dados de exemplo ou carregar dados reais
        3. Voltar a esta página para ver o dashboard
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔧 Voltar à Página Principal", use_container_width=True):
                st.switch_page("app.py")
        
        with col2:
            if st.button("📤 Ir para Upload de Dados", use_container_width=True):
                st.switch_page("pages/02_📤_Upload_de_Dados.py")
        
        return
    
    # Métricas principais
    st.markdown("## 📋 Métricas Principais")
    create_metrics_cards(apolices, sinistros)
    
    st.markdown("---")
    
    # Gráficos de apólices
    st.markdown("## 📊 Análise de Apólices")
    create_apolices_charts(apolices)
    
    st.markdown("---")
    
    # Análise temporal
    create_temporal_analysis(apolices, sinistros)
    
    st.markdown("---")
    
    # Visão geográfica
    create_geographic_overview(apolices)
    
    st.markdown("---")
    
    # Status do sistema
    with st.expander("🔧 Status do Sistema"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Estatísticas do Banco")
            try:
                from database import get_database
                db = get_database()
                
                st.write(f"**Banco de dados:** {os.path.basename(db.db_path)}")
                st.write(f"**Apólices:** {len(apolices)}")
                st.write(f"**Sinistros:** {len(sinistros)}")
                st.write(f"**Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                
            except Exception as e:
                st.error(f"Erro ao verificar status: {str(e)}")
        
        with col2:
            st.markdown("### 🎯 Próximas Ações")
            st.markdown("""
            - 📤 **Upload de novos dados** - Carregar mais apólices
            - ⚠️ **Análise de risco** - Identificar regiões críticas  
            - 📈 **Relatórios detalhados** - Gerar análises específicas
            - 🌦️ **Integração climática** - Conectar APIs meteorológicas
            """)

if __name__ == "__main__":
    main()