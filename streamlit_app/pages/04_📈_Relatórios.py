"""
Relatórios e Estatísticas - Sistema de Radar de Risco Climático
Interface para geração de relatórios detalhados e análises estatísticas
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta
import io
import base64
import time

# Configuração da página
st.set_page_config(
    page_title="Relatórios - Radar Climático",
    page_icon="📈",
    layout="wide"
)

# Adicionar path do projeto
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

def load_complete_data():
    """Carrega todos os dados disponíveis no sistema"""
    try:
        from database import get_database, CRUDOperations
        
        db = get_database()
        crud = CRUDOperations(db)
        
        # Carregar todas as tabelas
        apolices = crud.get_all_apolices()
        sinistros = crud.get_all_sinistros()
        
        return apolices, sinistros
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return [], []

def load_weather_cache_data():
    """Carrega dados climáticos do cache para relatórios"""
    try:
        from src.weather.weather_cache import WeatherCache
        
        # Inicializar cache
        cache = WeatherCache()
        
        # Obter dados em DataFrame
        weather_df = cache.export_to_dataframe(include_expired=False)
        
        if weather_df is not None and not weather_df.empty:
            # Converter timestamps para datetime
            if 'timestamp' in weather_df.columns:
                weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'])
            if 'file_time' in weather_df.columns:
                weather_df['file_time'] = pd.to_datetime(weather_df['file_time'])
        
        # Obter estatísticas
        weather_stats = cache.get_summary_statistics()
        
        return weather_df, weather_stats
        
    except Exception as e:
        st.error(f"Erro ao carregar dados climáticos: {str(e)}")
        return pd.DataFrame(), {}

def create_comprehensive_report(apolices, sinistros):
    """Gera relatório abrangente do sistema"""
    
    if not apolices:
        return None
    
    # Converter para DataFrames
    df_apolices = pd.DataFrame([{
        'numero_apolice': a.numero_apolice,
        'cep': a.cep,
        'tipo_residencia': a.tipo_residencia,
        'valor_segurado': float(a.valor_segurado or 0),
        'data_contratacao': a.data_contratacao,
        'latitude': a.latitude,
        'longitude': a.longitude
    } for a in apolices])
    
    df_sinistros = pd.DataFrame()
    if sinistros:
        # Criar mapeamento de apolice_id para numero_apolice
        apolice_map = {a.id: a.numero_apolice for a in apolices}
        
        df_sinistros = pd.DataFrame([{
            'numero_apolice': apolice_map.get(s.apolice_id, f'ID_{s.apolice_id}'),
            'data_sinistro': s.data_sinistro,
            'tipo_sinistro': s.tipo_sinistro,
            'valor_prejuizo': float(s.valor_prejuizo or 0),
            'condicoes_climaticas': s.condicoes_climaticas
        } for s in sinistros])
    
    # Análises estatísticas
    report = {
        'data_geracao': datetime.now(),
        'total_apolices': len(df_apolices),
        'total_sinistros': len(df_sinistros),
        'valor_total_segurado': df_apolices['valor_segurado'].sum(),
        'valor_medio_apolice': df_apolices['valor_segurado'].mean(),
        'distribuicao_tipos': df_apolices['tipo_residencia'].value_counts().to_dict(),
        'taxa_sinistralidade': (len(df_sinistros) / len(df_apolices)) * 100 if len(df_apolices) > 0 else 0
    }
    
    if not df_sinistros.empty:
        report.update({
            'valor_total_sinistros': df_sinistros['valor_prejuizo'].sum(),
            'valor_medio_sinistro': df_sinistros['valor_prejuizo'].mean(),
            'tipos_sinistros': df_sinistros['tipo_sinistro'].value_counts().to_dict()
        })
    
    return report, df_apolices, df_sinistros

def create_weather_report(weather_df, weather_stats):
    """Cria relatório específico de dados climáticos"""
    
    if weather_df.empty:
        return None, "Nenhum dado climático disponível no cache"
    
    # Métricas básicas
    report = {
        'total_consultas': len(weather_df),
        'localizacoes_unicas': weather_df['location'].nunique() if 'location' in weather_df else 0,
        'periodo_analise': {
            'inicio': weather_df['timestamp'].min() if 'timestamp' in weather_df else None,
            'fim': weather_df['timestamp'].max() if 'timestamp' in weather_df else None
        },
        'estatisticas': weather_stats.get('weather_stats', {})
    }
    
    # Criar visualizações
    visualizations = {}
    
    # 1. Distribuição de temperaturas
    if 'temperature_c' in weather_df.columns and weather_df['temperature_c'].notna().any():
        fig_temp = px.histogram(
            weather_df,
            x='temperature_c',
            nbins=20,
            title="Distribuição de Temperaturas Registradas",
            labels={'temperature_c': 'Temperatura (°C)', 'count': 'Frequência'}
        )
        fig_temp.update_layout(height=400)
        visualizations['temperature_dist'] = fig_temp
    
    # 2. Níveis de risco ao longo do tempo
    if 'risk_score' in weather_df.columns and 'timestamp' in weather_df.columns:
        weather_df_sorted = weather_df.sort_values('timestamp')
        fig_risk = px.line(
            weather_df_sorted,
            x='timestamp',
            y='risk_score',
            color='location',
            title="Evolução do Risco Climático por Localização",
            labels={'risk_score': 'Score de Risco', 'timestamp': 'Data/Hora'}
        )
        fig_risk.update_layout(height=400)
        visualizations['risk_timeline'] = fig_risk
    
    # 3. Mapa de calor de condições climáticas
    if 'condition' in weather_df.columns:
        condition_counts = weather_df['condition'].value_counts()
        fig_conditions = px.pie(
            values=condition_counts.values,
            names=condition_counts.index,
            title="Distribuição de Condições Climáticas"
        )
        visualizations['conditions_pie'] = fig_conditions
    
    # 4. Análise de umidade vs temperatura
    if 'temperature_c' in weather_df.columns and 'humidity_percent' in weather_df.columns:
        fig_scatter = px.scatter(
            weather_df,
            x='temperature_c',
            y='humidity_percent',
            color='risk_level' if 'risk_level' in weather_df.columns else None,
            title="Relação Temperatura vs Umidade",
            labels={'temperature_c': 'Temperatura (°C)', 'humidity_percent': 'Umidade (%)'}
        )
        visualizations['temp_humidity'] = fig_scatter
    
    # 5. Análise por localização
    if 'location' in weather_df.columns:
        location_stats = weather_df.groupby('location').agg({
            'temperature_c': ['mean', 'min', 'max'] if 'temperature_c' in weather_df else [],
            'humidity_percent': 'mean' if 'humidity_percent' in weather_df else [],
            'risk_score': 'mean' if 'risk_score' in weather_df else []
        }).reset_index()
        
        # Flatten column names
        location_stats.columns = ['_'.join(col).strip() if col[1] else col[0] for col in location_stats.columns]
        
        if 'temperature_c_mean' in location_stats.columns:
            fig_locations = px.bar(
                location_stats,
                x='location',
                y='temperature_c_mean',
                title="Temperatura Média por Localização",
                labels={'temperature_c_mean': 'Temperatura Média (°C)', 'location': 'Localização'}
            )
            fig_locations.update_layout(height=400)
            visualizations['locations_temp'] = fig_locations
    
    return report, visualizations

def create_financial_analysis(df_apolices, df_sinistros):
    """Cria análise financeira detalhada"""
    
    if df_apolices.empty:
        return None, None
    
    # Análise por valor segurado
    fig1 = px.histogram(
        df_apolices,
        x='valor_segurado',
        nbins=20,
        title="Distribuição de Valores Segurados",
        labels={'valor_segurado': 'Valor Segurado (R$)', 'count': 'Quantidade'}
    )
    
    fig1.update_layout(height=400)
    
    # Análise por tipo e valor
    valor_por_tipo = df_apolices.groupby('tipo_residencia')['valor_segurado'].agg([
        'count', 'sum', 'mean', 'median'
    ]).reset_index()
    
    fig2 = px.bar(
        valor_por_tipo,
        x='tipo_residencia',
        y='sum',
        title="Valor Total Segurado por Tipo de Residência",
        labels={'sum': 'Valor Total (R$)', 'tipo_residencia': 'Tipo de Residência'}
    )
    
    fig2.update_layout(height=400)
    
    # Se há dados de sinistros, analisar impacto financeiro
    if not df_sinistros.empty:
        # Análise de sinistralidade por tipo
        merged_df = df_sinistros.merge(
            df_apolices[['numero_apolice', 'tipo_residencia', 'valor_segurado']], 
            on='numero_apolice', 
            how='left'
        )
        
        sinistro_por_tipo = merged_df.groupby('tipo_residencia')['valor_prejuizo'].agg([
            'count', 'sum', 'mean'
        ]).reset_index()
        
        fig3 = px.bar(
            sinistro_por_tipo,
            x='tipo_residencia',
            y='sum',
            title="Valor Total de Sinistros por Tipo de Residência",
            labels={'sum': 'Valor Total Sinistros (R$)', 'tipo_residencia': 'Tipo de Residência'},
            color='sum',
            color_continuous_scale='Reds'
        )
        
        fig3.update_layout(height=400)
        
        return fig1, fig2, fig3
    
    return fig1, fig2, None

def create_temporal_analysis(df_apolices, df_sinistros):
    """Cria análise temporal detalhada"""
    
    if df_apolices.empty:
        return None
    
    # Converter datas
    df_apolices['data_contratacao'] = pd.to_datetime(df_apolices['data_contratacao'])
    
    # Análise mensal de contratações
    df_apolices['mes_ano'] = df_apolices['data_contratacao'].dt.to_period('M')
    
    contratos_mes = df_apolices.groupby('mes_ano').agg({
        'numero_apolice': 'count',
        'valor_segurado': 'sum'
    }).reset_index()
    
    contratos_mes['mes_ano_str'] = contratos_mes['mes_ano'].astype(str)
    
    # Criar gráfico combinado
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=['Contratos por Mês', 'Valor Segurado por Mês'],
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
    )
    
    # Linha de contratos
    fig.add_trace(
        go.Scatter(
            x=contratos_mes['mes_ano_str'],
            y=contratos_mes['numero_apolice'],
            mode='lines+markers',
            name='Contratos',
            line=dict(color='#1f77b4', width=3)
        ),
        row=1, col=1
    )
    
    # Linha de valor
    fig.add_trace(
        go.Scatter(
            x=contratos_mes['mes_ano_str'],
            y=contratos_mes['valor_segurado'],
            mode='lines+markers',
            name='Valor Total',
            line=dict(color='#ff7f0e', width=3)
        ),
        row=2, col=1
    )
    
    # Se há sinistros, adicionar análise temporal
    if not df_sinistros.empty:
        df_sinistros['data_sinistro'] = pd.to_datetime(df_sinistros['data_sinistro'])
        df_sinistros['mes_ano'] = df_sinistros['data_sinistro'].dt.to_period('M')
        
        sinistros_mes = df_sinistros.groupby('mes_ano').agg({
            'valor_prejuizo': ['count', 'sum']
        }).reset_index()
        
        sinistros_mes.columns = ['mes_ano', 'count', 'sum']
        sinistros_mes['mes_ano_str'] = sinistros_mes['mes_ano'].astype(str)
        
        # Adicionar subplot para sinistros
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=['Contratos por Mês', 'Valor Segurado por Mês', 'Sinistros por Mês'],
            vertical_spacing=0.08
        )
        
        # Re-adicionar traces anteriores
        fig.add_trace(
            go.Scatter(
                x=contratos_mes['mes_ano_str'],
                y=contratos_mes['numero_apolice'],
                mode='lines+markers',
                name='Contratos',
                line=dict(color='#1f77b4', width=3)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=contratos_mes['mes_ano_str'],
                y=contratos_mes['valor_segurado'],
                mode='lines+markers',
                name='Valor Total',
                line=dict(color='#ff7f0e', width=3)
            ),
            row=2, col=1
        )
        
        # Adicionar sinistros
        fig.add_trace(
            go.Scatter(
                x=sinistros_mes['mes_ano_str'],
                y=sinistros_mes['count'],
                mode='lines+markers',
                name='Sinistros',
                line=dict(color='#d62728', width=3)
            ),
            row=3, col=1
        )
    
    fig.update_layout(height=600, title_text="Análise Temporal Completa")
    fig.update_xaxes(title_text="Período")
    
    return fig

def create_geographic_analysis(df_apolices):
    """Cria análise geográfica por CEP"""
    
    if df_apolices.empty:
        return None
    
    # Análise por região (primeiros 5 dígitos do CEP)
    df_apolices['regiao_cep'] = df_apolices['cep'].str[:5]
    
    analise_geografica = df_apolices.groupby('regiao_cep').agg({
        'numero_apolice': 'count',
        'valor_segurado': ['sum', 'mean'],
        'tipo_residencia': lambda x: x.mode().iloc[0] if not x.empty else 'N/A'
    }).reset_index()
    
    analise_geografica.columns = ['regiao_cep', 'total_apolices', 'valor_total', 'valor_medio', 'tipo_predominante']
    
    # Top 10 regiões por valor total
    top_regioes = analise_geografica.nlargest(10, 'valor_total')
    
    fig = px.bar(
        top_regioes,
        x='regiao_cep',
        y='valor_total',
        color='total_apolices',
        title="Top 10 Regiões por Valor Total Segurado",
        labels={
            'valor_total': 'Valor Total (R$)',
            'regiao_cep': 'Região (CEP)',
            'total_apolices': 'Nº Apólices'
        }
    )
    
    fig.update_layout(height=500)
    
    return fig, analise_geografica

def generate_pdf_report(report_data):
    """Gera relatório em PDF (simulado como texto)"""
    
    report_text = f"""
RELATÓRIO COMPLETO DO SISTEMA DE RADAR CLIMÁTICO
===============================================

Data de Geração: {report_data['data_geracao'].strftime('%d/%m/%Y %H:%M')}

RESUMO EXECUTIVO
================
• Total de Apólices: {report_data['total_apolices']:,}
• Total de Sinistros: {report_data['total_sinistros']:,}
• Valor Total Segurado: R$ {report_data['valor_total_segurado']:,.2f}
• Valor Médio por Apólice: R$ {report_data['valor_medio_apolice']:,.2f}
• Taxa de Sinistralidade: {report_data['taxa_sinistralidade']:.2f}%

DISTRIBUIÇÃO POR TIPO DE RESIDÊNCIA
===================================
"""
    
    for tipo, quantidade in report_data['distribuicao_tipos'].items():
        percentual = (quantidade / report_data['total_apolices']) * 100
        report_text += f"• {tipo.title()}: {quantidade:,} ({percentual:.1f}%)\n"
    
    if 'tipos_sinistros' in report_data:
        report_text += f"""

ANÁLISE DE SINISTROS
===================
• Valor Total de Sinistros: R$ {report_data['valor_total_sinistros']:,.2f}
• Valor Médio por Sinistro: R$ {report_data['valor_medio_sinistro']:,.2f}

Tipos de Sinistros:
"""
        for tipo, quantidade in report_data['tipos_sinistros'].items():
            report_text += f"• {tipo}: {quantidade:,}\n"
    
    report_text += f"""

CONCLUSÕES E RECOMENDAÇÕES
==========================
1. O sistema possui {report_data['total_apolices']:,} apólices ativas
2. Taxa de sinistralidade atual: {report_data['taxa_sinistralidade']:.1f}%
3. Exposição total do portfólio: R$ {report_data['valor_total_segurado']/1_000_000:.1f} milhões

Recomendações:
• Monitorar regiões com alta concentração de apólices
• Implementar alertas para condições climáticas adversas
• Revisar precificação com base nos dados históricos
• Expandir cobertura geográfica em regiões de baixo risco

---
Relatório gerado automaticamente pelo Sistema de Radar Climático
"""
    
    return report_text

def main():
    """Função principal da página"""
    
    st.title("📈 Relatórios e Estatísticas")
    st.markdown("Análises completas e relatórios detalhados do sistema")
    
    # Sidebar com opções de relatório
    with st.sidebar:
        st.markdown("### 📋 Tipos de Relatório")
        
        tipo_relatorio = st.selectbox(
            "Escolha o tipo de análise:",
            [
                "Relatório Completo",
                "Análise Financeira", 
                "Análise Temporal",
                "Análise Geográfica",
                "Análise Climática",
                "Estatísticas Detalhadas"
            ]
        )
        
        st.markdown("---")
        st.markdown("### 📊 Opções de Exportação")
        
        formato_export = st.selectbox(
            "Formato de exportação:",
            ["Visualização Web", "Texto/PDF", "CSV", "Excel"]
        )
        
        st.markdown("---")
        st.markdown("### 🔧 Configurações")
        
        incluir_graficos = st.checkbox("Incluir gráficos", value=True)
        incluir_tabelas = st.checkbox("Incluir tabelas detalhadas", value=True)
        incluir_recomendacoes = st.checkbox("Incluir recomendações", value=True)
    
    # Carregar dados
    with st.spinner("Carregando dados para análise..."):
        apolices, sinistros = load_complete_data()
    
    if not apolices:
        st.error("""
        ❌ **Nenhum dado encontrado para gerar relatórios**
        
        Para acessar os relatórios:
        1. Carregue dados de apólices
        2. Gere dados de exemplo
        3. Volte a esta página
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Carregar Dados", use_container_width=True):
                st.switch_page("pages/02_📤_Upload_de_Dados.py")
        
        with col2:
            if st.button("🏠 Página Principal", use_container_width=True):
                st.switch_page("app.py")
        
        return
    
    # Gerar relatório completo
    with st.spinner("Gerando análises..."):
        report_data, df_apolices, df_sinistros = create_comprehensive_report(apolices, sinistros)
    
    if not report_data:
        st.error("Erro ao gerar relatório. Verifique os dados.")
        return
    
    # Mostrar métricas principais
    st.markdown("## 📊 Resumo Executivo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📋 Total de Apólices",
            f"{report_data['total_apolices']:,}",
            delta=f"+{report_data['total_apolices']//10}"
        )
    
    with col2:
        st.metric(
            "⚠️ Total de Sinistros",
            f"{report_data['total_sinistros']:,}",
            delta=f"{report_data['taxa_sinistralidade']:.1f}%"
        )
    
    with col3:
        st.metric(
            "💰 Valor Total Segurado",
            f"R$ {report_data['valor_total_segurado']/1_000_000:.1f}M",
            delta=f"Média: R$ {report_data['valor_medio_apolice']/1000:.0f}K"
        )
    
    with col4:
        if 'valor_total_sinistros' in report_data:
            st.metric(
                "💸 Total de Sinistros",
                f"R$ {report_data['valor_total_sinistros']/1_000_000:.1f}M",
                delta=f"Média: R$ {report_data['valor_medio_sinistro']/1000:.0f}K"
            )
        else:
            st.metric("💸 Total de Sinistros", "R$ 0")
    
    # Conteúdo baseado no tipo de relatório selecionado
    if tipo_relatorio == "Relatório Completo":
        
        st.markdown("---")
        st.markdown("## 📊 Distribuição por Tipo de Residência")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de pizza
            tipos = list(report_data['distribuicao_tipos'].keys())
            valores = list(report_data['distribuicao_tipos'].values())
            
            fig_pie = px.pie(
                values=valores,
                names=tipos,
                title="Distribuição de Apólices por Tipo"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Tabela detalhada
            st.markdown("### 📋 Detalhamento")
            
            for tipo, quantidade in report_data['distribuicao_tipos'].items():
                percentual = (quantidade / report_data['total_apolices']) * 100
                st.markdown(f"**{tipo.title()}:** {quantidade:,} ({percentual:.1f}%)")
            
            st.markdown("---")
            st.markdown(f"**Taxa de Sinistralidade:** {report_data['taxa_sinistralidade']:.2f}%")
            
            if report_data['taxa_sinistralidade'] > 10:
                st.warning("⚠️ Taxa de sinistralidade elevada")
            else:
                st.success("✅ Taxa de sinistralidade adequada")
        
        # Análises adicionais
        if incluir_graficos:
            st.markdown("---")
            st.markdown("## 💰 Análise Financeira")
            
            fig1, fig2, fig3 = create_financial_analysis(df_apolices, df_sinistros)
            
            if fig1:
                st.plotly_chart(fig1, use_container_width=True)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)
            if fig3:
                st.plotly_chart(fig3, use_container_width=True)
        
        if incluir_graficos:
            st.markdown("---")
            st.markdown("## 📅 Análise Temporal")
            
            fig_temporal = create_temporal_analysis(df_apolices, df_sinistros)
            if fig_temporal:
                st.plotly_chart(fig_temporal, use_container_width=True)
        
        if incluir_graficos:
            st.markdown("---")
            st.markdown("## 🗺️ Análise Geográfica")
            
            fig_geo, tabela_geo = create_geographic_analysis(df_apolices)
            
            if fig_geo:
                st.plotly_chart(fig_geo, use_container_width=True)
                
                if incluir_tabelas:
                    st.markdown("### 📊 Detalhamento por Região")
                    st.dataframe(tabela_geo.head(10), use_container_width=True)
        
        if incluir_recomendacoes:
            st.markdown("---")
            st.markdown("## 💡 Recomendações")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ✅ Pontos Positivos")
                st.success("• Sistema operacional e coletando dados")
                st.success(f"• {report_data['total_apolices']:,} apólices ativas no portfólio")
                st.success("• Dados estruturados e organizados")
                
                if report_data['taxa_sinistralidade'] < 10:
                    st.success("• Taxa de sinistralidade dentro da meta")
            
            with col2:
                st.markdown("### ⚠️ Pontos de Atenção")
                
                if report_data['taxa_sinistralidade'] > 10:
                    st.warning("• Taxa de sinistralidade acima do recomendado")
                
                if report_data['total_sinistros'] == 0:
                    st.info("• Sem histórico de sinistros para análise preditiva")
                
                st.info("• Implementar integração com APIs climáticas")
                st.info("• Expandir coleta de dados geográficos")
    
    elif tipo_relatorio == "Análise Financeira":
        fig1, fig2, fig3 = create_financial_analysis(df_apolices, df_sinistros)
        
        if fig1:
            st.plotly_chart(fig1, use_container_width=True)
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)
        if fig3:
            st.plotly_chart(fig3, use_container_width=True)
    
    elif tipo_relatorio == "Análise Temporal":
        fig_temporal = create_temporal_analysis(df_apolices, df_sinistros)
        if fig_temporal:
            st.plotly_chart(fig_temporal, use_container_width=True)
    
    elif tipo_relatorio == "Análise Geográfica":
        fig_geo, tabela_geo = create_geographic_analysis(df_apolices)
        
        if fig_geo:
            st.plotly_chart(fig_geo, use_container_width=True)
            st.dataframe(tabela_geo, use_container_width=True)
    
    elif tipo_relatorio == "Análise Climática":
        st.markdown("## 🌤️ Análise de Dados Climáticos")
        
        with st.spinner("Carregando dados climáticos do cache..."):
            weather_df, weather_stats = load_weather_cache_data()
        
        if weather_df.empty:
            st.warning("""
            ⚠️ **Nenhum dado climático encontrado no cache**
            
            Para gerar análises climáticas:
            1. Acesse a página **🌤️ API Climática**
            2. Configure sua chave da API
            3. Faça consultas de dados climáticos
            4. Os dados ficam automaticamente em cache para análise
            """)
        else:
            weather_report, weather_visualizations = create_weather_report(weather_df, weather_stats)
            
            # Métricas de resumo
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total de Consultas",
                    weather_report.get('total_consultas', 0)
                )
            
            with col2:
                st.metric(
                    "Localizações Únicas",
                    weather_report.get('localizacoes_unicas', 0)
                )
            
            with col3:
                temp_stats = weather_report.get('estatisticas', {}).get('temperature_c', {})
                if temp_stats:
                    st.metric(
                        "Temp. Média",
                        f"{temp_stats.get('mean', 0):.1f}°C",
                        f"Min: {temp_stats.get('min', 0):.1f}°C | Max: {temp_stats.get('max', 0):.1f}°C"
                    )
                else:
                    st.metric("Temp. Média", "N/A")
            
            with col4:
                risk_stats = weather_report.get('estatisticas', {}).get('risk_score', {})
                if risk_stats:
                    st.metric(
                        "Risco Médio",
                        f"{risk_stats.get('mean', 0):.1f}",
                        f"Faixa: {risk_stats.get('min', 0):.1f} - {risk_stats.get('max', 0):.1f}"
                    )
                else:
                    st.metric("Risco Médio", "N/A")
            
            # Período de análise
            if weather_report.get('periodo_analise', {}).get('inicio'):
                inicio = weather_report['periodo_analise']['inicio']
                fim = weather_report['periodo_analise']['fim']
                st.info(f"📅 **Período analisado:** {inicio} até {fim}")
            
            # Visualizações
            if weather_visualizations:
                st.markdown("### 📊 Visualizações Climáticas")
                
                # Distribuição de temperaturas
                if 'temperature_dist' in weather_visualizations:
                    st.plotly_chart(weather_visualizations['temperature_dist'], use_container_width=True)
                
                # Timeline de risco
                if 'risk_timeline' in weather_visualizations:
                    st.plotly_chart(weather_visualizations['risk_timeline'], use_container_width=True)
                
                # Duas colunas para gráficos menores
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'conditions_pie' in weather_visualizations:
                        st.plotly_chart(weather_visualizations['conditions_pie'], use_container_width=True)
                
                with col2:
                    if 'temp_humidity' in weather_visualizations:
                        st.plotly_chart(weather_visualizations['temp_humidity'], use_container_width=True)
                
                # Análise por localização
                if 'locations_temp' in weather_visualizations:
                    st.plotly_chart(weather_visualizations['locations_temp'], use_container_width=True)
            
            # Tabela de dados detalhados
            with st.expander("📋 Dados Detalhados do Cache Climático"):
                st.dataframe(
                    weather_df.drop(columns=['cache_key', 'file_time'], errors='ignore'),
                    use_container_width=True
                )
            
            # Estatísticas por condição climática
            if 'condition' in weather_df.columns:
                st.markdown("### 🌦️ Análise por Condição Climática")
                
                condition_analysis = weather_df.groupby('condition').agg({
                    'temperature_c': ['mean', 'std'] if 'temperature_c' in weather_df else [],
                    'humidity_percent': 'mean' if 'humidity_percent' in weather_df else [],
                    'risk_score': ['mean', 'max'] if 'risk_score' in weather_df else [],
                    'location': 'count'
                }).round(2)
                
                condition_analysis.columns = ['_'.join(col).strip() if col[1] else col[0] 
                                             for col in condition_analysis.columns]
                condition_analysis = condition_analysis.rename(columns={'location_count': 'frequencia'})
                
                st.dataframe(condition_analysis, use_container_width=True)
            
            # Correlação com sinistros (se possível)
            if not df_sinistros.empty and 'location' in weather_df.columns:
                st.markdown("### 🔗 Correlação Clima x Sinistros")
                
                # Tentar correlacionar por cidade/região
                weather_locations = set(weather_df['location'].str.lower())
                sinistro_locations = set()
                
                # Extrair cidades dos dados de sinistros (se tiver campo de localização)
                if 'cidade' in df_sinistros.columns:
                    sinistro_locations = set(df_sinistros['cidade'].str.lower())
                elif 'endereco' in df_sinistros.columns:
                    # Tentar extrair cidade do endereço
                    sinistro_locations = set([addr.split(',')[-1].strip().lower() 
                                            for addr in df_sinistros['endereco'] if ',' in addr])
                
                common_locations = weather_locations.intersection(sinistro_locations)
                
                if common_locations:
                    st.success(f"📍 Encontradas {len(common_locations)} localizações em comum para análise de correlação")
                    
                    # Análise básica de correlação
                    correlation_data = []
                    
                    for location in common_locations:
                        weather_subset = weather_df[weather_df['location'].str.lower() == location]
                        sinistro_subset = df_sinistros[
                            (df_sinistros.get('cidade', '').str.lower() == location) |
                            (df_sinistros.get('endereco', '').str.contains(location, case=False, na=False))
                        ]
                        
                        if not weather_subset.empty and not sinistro_subset.empty:
                            avg_risk = weather_subset['risk_score'].mean() if 'risk_score' in weather_subset else 0
                            num_sinistros = len(sinistro_subset)
                            avg_value = sinistro_subset['valor_prejuizo'].mean() if 'valor_prejuizo' in sinistro_subset else 0
                            
                            correlation_data.append({
                                'Localização': location.title(),
                                'Risco Climático Médio': round(avg_risk, 2),
                                'Número de Sinistros': num_sinistros,
                                'Valor Médio Sinistro': f"R$ {avg_value:,.2f}" if avg_value > 0 else "N/A"
                            })
                    
                    if correlation_data:
                        correlation_df = pd.DataFrame(correlation_data)
                        st.dataframe(correlation_df, use_container_width=True)
                        
                        # Gráfico de correlação
                        if len(correlation_data) > 1:
                            fig_corr = px.scatter(
                                correlation_df,
                                x='Risco Climático Médio',
                                y='Número de Sinistros',
                                hover_data=['Localização'],
                                title="Correlação: Risco Climático vs Número de Sinistros",
                                labels={
                                    'Risco Climático Médio': 'Score de Risco Climático',
                                    'Número de Sinistros': 'Quantidade de Sinistros'
                                }
                            )
                            st.plotly_chart(fig_corr, use_container_width=True)
                    else:
                        st.info("📊 Dados insuficientes para análise de correlação detalhada")
                else:
                    st.info("📍 Nenhuma localização em comum encontrada entre dados climáticos e sinistros")
    
    elif tipo_relatorio == "Estatísticas Detalhadas":
        st.markdown("## 📊 Estatísticas Completas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 Estatísticas de Apólices")
            st.dataframe(df_apolices.describe(), use_container_width=True)
        
        with col2:
            if not df_sinistros.empty:
                st.markdown("### ⚠️ Estatísticas de Sinistros")
                st.dataframe(df_sinistros.describe(), use_container_width=True)
            else:
                st.info("Nenhum sinistro registrado para análise estatística.")
    
    # Exportação
    st.markdown("---")
    st.markdown("## 📤 Exportar Relatório")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Baixar Relatório PDF", use_container_width=True):
            if formato_export == "Texto/PDF":
                pdf_content = generate_pdf_report(report_data)
                
                st.download_button(
                    label="💾 Download PDF",
                    data=pdf_content,
                    file_name=f"relatorio_radar_climatico_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )
            else:
                st.info("Selecione 'Texto/PDF' no formato de exportação")
    
    with col2:
        if st.button("📊 Exportar Dados CSV", use_container_width=True):
            if formato_export == "CSV":
                # Combinar dados principais
                csv_data = df_apolices.to_csv(index=False)
                
                # Se tem dados climáticos, incluir
                if tipo_relatorio == "Análise Climática" and not weather_df.empty:
                    weather_csv = weather_df.to_csv(index=False)
                    csv_data += "\n\n# DADOS CLIMATICOS\n" + weather_csv
                
                st.download_button(
                    label="💾 Download CSV",
                    data=csv_data,
                    file_name=f"dados_radar_climatico_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("Selecione 'CSV' no formato de exportação")
    
    with col3:
        if st.button("🔄 Atualizar Cache Climático", use_container_width=True):
            with st.spinner("Atualizando cache climático..."):
                try:
                    from src.reports import cleanup_expired_cache, get_weather_cache_summary
                    
                    # Limpar cache expirado
                    cleanup_result = cleanup_expired_cache()
                    
                    # Obter estatísticas atuais
                    summary_result = get_weather_cache_summary()
                    
                    if cleanup_result['success']:
                        st.success(f"✅ Cache atualizado! {cleanup_result['removed_files']} arquivos expirados removidos")
                    
                    if summary_result['success']:
                        st.info(f"📊 Total de registros ativos: {summary_result['total_records']}")
                    
                    # Recarregar página para mostrar dados atualizados
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro ao atualizar cache: {e}")

# Executar função principal diretamente no Streamlit
main()