"""
Análise de Risco - Sistema de Radar de Risco Climático
Interface para visualização de mapas e análise de risco geográfico
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import sys
import os
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta
import json

# Configuração da página
st.set_page_config(
    page_title="Análise de Risco - Radar Climático",
    page_icon="⚠️",
    layout="wide"
)

# Adicionar path do projeto
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

def load_risk_data():
    """Carrega dados para análise de risco"""
    try:
        from database import get_database, CRUDOperations
        
        db = get_database()
        crud = CRUDOperations(db)
        
        # Carregar apólices e sinistros com coordenadas
        apolices = crud.get_apolices_by_region()
        sinistros = crud.get_sinistros_com_coordenadas()
        
        return apolices, sinistros
        
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return [], []

def calculate_risk_score(apolice, sinistros_nearby=0, weather_risk=0.5):
    """Calcula score de risco para uma apólice"""
    
    # Score base por tipo de residência
    tipo_scores = {
        'casa': 0.6,
        'apartamento': 0.3,
        'sobrado': 0.8
    }
    
    base_score = tipo_scores.get(apolice.tipo_residencia.lower(), 0.5)
    
    # Ajuste por valor segurado (valores maiores = maior risco)
    valor_factor = min(float(apolice.valor_segurado or 0) / 1_000_000, 1.0)
    
    # Ajuste por sinistros próximos
    sinistro_factor = min(sinistros_nearby * 0.2, 1.0)
    
    # Score final (0-100)
    risk_score = (base_score + valor_factor + sinistro_factor + weather_risk) * 25
    
    return min(max(risk_score, 0), 100)

def get_risk_level(score):
    """Retorna nível de risco baseado no score - Sistema aprimorado"""
    if score < 25:
        return "Baixo", "#28a745"  # Verde mais forte
    elif score < 50:
        return "Médio", "#ffc107"  # Amarelo/laranja
    else:  # 50%+ = Alto/Crítico
        return "Alto/Crítico", "#dc3545"  # Vermelho mais forte

def create_risk_map(apolices, sinistros):
    """Cria mapa interativo de risco"""
    
    if not apolices:
        st.warning("Nenhuma apólice com coordenadas encontrada.")
        return None
    
    # Filtrar apólices com coordenadas
    apolices_geo = [a for a in apolices if a.latitude and a.longitude]
    
    if not apolices_geo:
        st.warning("Nenhuma apólice com coordenadas geográficas.")
        return None
    
    # Criar mapa centrado no Brasil
    center_lat = -15.7942
    center_lon = -47.8822
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=5,
        tiles='OpenStreetMap'
    )
    
    # Adicionar marcadores de apólices
    for apolice in apolices_geo:
        # Calcular score de risco
        risk_score = calculate_risk_score(apolice)
        risk_level, color = get_risk_level(risk_score)
        
        # Criar popup com informações
        popup_text = f"""
        <b>Apólice:</b> {apolice.numero_apolice}<br>
        <b>CEP:</b> {apolice.cep}<br>
        <b>Tipo:</b> {apolice.tipo_residencia}<br>
        <b>Valor:</b> R$ {float(apolice.valor_segurado or 0):,.2f}<br>
        <b>Risco:</b> {risk_level} ({risk_score:.1f}%)
        """
        
        # Escolher ícone baseado no risco - Sistema aprimorado
        if risk_score < 25:
            icon_color = 'green'
            icon_symbol = 'home'
        elif risk_score < 50:
            icon_color = 'orange' 
            icon_symbol = 'home'
        else:  # 50%+ = Alto/Crítico
            icon_color = 'red'
            icon_symbol = 'exclamation-sign'
        
        folium.Marker(
            location=[float(apolice.latitude), float(apolice.longitude)],
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"Apólice {apolice.numero_apolice} - Risco {risk_level}",
            icon=folium.Icon(color=icon_color, icon=icon_symbol, prefix='fa')
        ).add_to(m)
    
    # Adicionar marcadores de sinistros com melhor visualização
    for sinistro in sinistros:
        if sinistro.latitude and sinistro.longitude:
            popup_text = f"""
            <div style="color: #333; font-family: Arial, sans-serif;">
            <h4 style="color: #dc3545; margin-bottom: 10px;">🚨 Sinistro</h4>
            <b>Tipo:</b> {sinistro.tipo_sinistro}<br>
            <b>Data:</b> {sinistro.data_sinistro.strftime('%d/%m/%Y')}<br>
            <b>Prejuízo:</b> R$ {float(sinistro.valor_prejuizo or 0):,.2f}<br>
            <b>Apólice:</b> {sinistro.numero_apolice}
            </div>
            """
            
            # Usar CircleMarker para melhor visibilidade
            folium.CircleMarker(
                location=[float(sinistro.latitude), float(sinistro.longitude)],
                radius=8,
                popup=folium.Popup(popup_text, max_width=350),
                tooltip=f"⚠️ Sinistro: {sinistro.tipo_sinistro}",
                color='#dc3545',
                weight=3,
                fillColor='#dc3545',
                fillOpacity=0.8
            ).add_to(m)
    
    # Adicionar legenda com tema adaptável
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 220px; height: 160px; 
                background: linear-gradient(135deg, rgba(248,249,250,0.95) 0%, rgba(233,236,239,0.95) 100%);
                border: 2px solid #007bff; border-radius: 8px; z-index:9999; 
                font-size:14px; padding: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                color: #333; overflow: hidden;">
    <h4 style="margin-top:0; margin-bottom:10px; color: #007bff; font-size: 16px;">🎯 Níveis de Risco</h4>
    <div style="margin: 6px 0;">
        <i class="fa fa-circle" style="color:#28a745; margin-right: 8px;"></i> 
        <strong>Baixo:</strong> 0-25%
    </div>
    <div style="margin: 6px 0;">
        <i class="fa fa-circle" style="color:#ffc107; margin-right: 8px;"></i> 
        <strong>Médio:</strong> 25-50%
    </div>
    <div style="margin: 6px 0;">
        <i class="fa fa-circle" style="color:#dc3545; margin-right: 8px;"></i> 
        <strong>Alto/Crítico:</strong> 50%+
    </div>
    <div style="margin: 8px 0 2px 0; border-top: 1px solid #dee2e6; padding-top: 8px;">
        <i class="fa fa-circle" style="color:#dc3545; margin-right: 8px;"></i> 
        <strong>Sinistros Ocorridos</strong>
    </div>
    </div>
    
    <!-- Estilo para tema escuro -->
    <style>
    @media (prefers-color-scheme: dark) {
        div[style*="background: linear-gradient"] {
            background: linear-gradient(135deg, rgba(45,55,72,0.95) 0%, rgba(74,85,104,0.95) 100%) !important;
            color: #e2e8f0 !important;
        }
        div[style*="background: linear-gradient"] h4 {
            color: #63b3ed !important;
        }
        div[style*="background: linear-gradient"] strong {
            color: #cbd5e0 !important;
        }
    }
    </style>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def create_risk_heatmap(apolices):
    """Cria mapa de calor de risco por região"""
    
    if not apolices:
        return None
    
    # Agrupar por região (primeiros 5 dígitos do CEP)
    risk_by_region = {}
    
    for apolice in apolices:
        region = apolice.cep[:5] if apolice.cep else "00000"
        
        if region not in risk_by_region:
            risk_by_region[region] = {
                'count': 0,
                'total_value': 0,
                'risk_scores': []
            }
        
        risk_score = calculate_risk_score(apolice)
        risk_by_region[region]['count'] += 1
        risk_by_region[region]['total_value'] += float(apolice.valor_segurado or 0)
        risk_by_region[region]['risk_scores'].append(risk_score)
    
    # Preparar dados para gráfico
    regions = []
    avg_risks = []
    counts = []
    values = []
    
    for region, data in risk_by_region.items():
        regions.append(region)
        avg_risks.append(np.mean(data['risk_scores']))
        counts.append(data['count'])
        values.append(data['total_value'])
    
    # Criar DataFrame
    df_risk = pd.DataFrame({
        'Região (CEP)': regions,
        'Risco Médio': avg_risks,
        'Quantidade': counts,
        'Valor Total': values
    })
    
    # Criar gráfico de barras
    fig = px.bar(
        df_risk,
        x='Região (CEP)',
        y='Risco Médio',
        color='Risco Médio',
        hover_data=['Quantidade', 'Valor Total'],
        title="Risco Médio por Região",
        color_continuous_scale='RdYlGn_r',
        labels={'Risco Médio': 'Score de Risco (%)', 'Quantidade': 'Nº de Apólices'}
    )
    
    fig.update_layout(height=500)
    
    return fig

def create_risk_analysis_charts(apolices, sinistros):
    """Cria gráficos de análise de risco"""
    
    if not apolices:
        return None, None
    
    # Preparar dados
    risk_data = []
    
    for apolice in apolices:
        risk_score = calculate_risk_score(apolice)
        risk_level, _ = get_risk_level(risk_score)
        
        risk_data.append({
            'apolice': apolice.numero_apolice,
            'tipo': apolice.tipo_residencia,
            'valor': float(apolice.valor_segurado or 0),
            'risco_score': risk_score,
            'risco_nivel': risk_level
        })
    
    df_risk = pd.DataFrame(risk_data)
    
    # Gráfico 1: Distribuição de risco por tipo
    fig1 = px.box(
        df_risk,
        x='tipo',
        y='risco_score',
        color='tipo',
        title="Distribuição de Risco por Tipo de Residência",
        labels={'risco_score': 'Score de Risco (%)', 'tipo': 'Tipo de Residência'}
    )
    
    # Gráfico 2: Correlação valor x risco
    fig2 = px.scatter(
        df_risk,
        x='valor',
        y='risco_score',
        color='risco_nivel',
        size='valor',
        title="Correlação: Valor Segurado vs Score de Risco",
        labels={'valor': 'Valor Segurado (R$)', 'risco_score': 'Score de Risco (%)'},
        color_discrete_map={
            'Baixo': '#00cc66',
            'Médio': '#ffa421', 
            'Alto': '#ff7f0e',
            'Crítico': '#ff4b4b'
        }
    )
    
    return fig1, fig2

def simulate_weather_impact():
    """Simula impacto de condições climáticas no risco"""
    
    st.markdown("### 🌦️ Simulação de Impacto Climático")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        temp = st.slider("🌡️ Temperatura (°C)", -10, 50, 25)
    
    with col2:
        precipitacao = st.slider("🌧️ Precipitação (mm)", 0, 200, 10)
    
    with col3:
        vento = st.slider("💨 Velocidade do Vento (km/h)", 0, 150, 20)
    
    # Calcular fator de risco climático
    temp_risk = 0.2 if temp < 0 or temp > 40 else 0.0
    rain_risk = min(precipitacao / 100, 1.0) * 0.4
    wind_risk = min(vento / 100, 1.0) * 0.4
    
    climate_risk = (temp_risk + rain_risk + wind_risk) * 100
    
    # Mostrar resultado
    risk_level, color = get_risk_level(climate_risk)
    
    st.markdown(f"""
    <div style="background-color: {color}20; padding: 1rem; border-radius: 10px; border-left: 5px solid {color};">
        <h4>🎯 Impacto Climático Calculado</h4>
        <p><strong>Score de Risco Climático:</strong> {climate_risk:.1f}%</p>
        <p><strong>Nível de Risco:</strong> {risk_level}</p>
    </div>
    """, unsafe_allow_html=True)
    
    return climate_risk / 100

def main():
    """Função principal da página"""
    
    st.title("⚠️ Análise de Risco Climático")
    st.markdown("Visualização geográfica e análise de riscos por região")
    
    # Sidebar com filtros
    with st.sidebar:
        st.markdown("### 🎛️ Filtros de Análise")
        
        # Filtro por tipo de residência
        tipos_residencia = st.multiselect(
            "🏠 Tipo de Residência",
            options=["casa", "apartamento", "sobrado"],
            default=["casa", "apartamento", "sobrado"]
        )
        
        # Filtro por faixa de valor
        valor_min = st.number_input("💰 Valor Mínimo (R$)", min_value=0, value=0, step=10000)
        valor_max = st.number_input("💰 Valor Máximo (R$)", min_value=0, value=1000000, step=10000)
        
        # Filtro por nível de risco
        niveis_risco = st.multiselect(
            "⚠️ Níveis de Risco",
            options=["Baixo", "Médio", "Alto", "Crítico"],
            default=["Baixo", "Médio", "Alto", "Crítico"]
        )
        
        st.markdown("---")
        st.markdown("### 📊 Análises Disponíveis")
        st.markdown("- 🗺️ **Mapa de Risco** - Localização geográfica")
        st.markdown("- 📈 **Heatmap Regional** - Risco por região")
        st.markdown("- 📊 **Análise Estatística** - Gráficos de correlação")
        st.markdown("- 🌦️ **Simulação Climática** - Impacto do tempo")
    
    # Carregar dados
    with st.spinner("Carregando dados de risco..."):
        apolices, sinistros = load_risk_data()
    
    if not apolices:
        st.error("""
        ❌ **Nenhum dado encontrado para análise de risco**
        
        Para usar esta funcionalidade:
        1. Carregue dados de apólices
        2. Gere dados de exemplo
        3. Volte a esta página
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Ir para Upload", use_container_width=True):
                st.switch_page("pages/02_📤_Upload_de_Dados.py")
        
        with col2:
            if st.button("🏠 Página Principal", use_container_width=True):
                st.switch_page("app.py")
        
        return
    
    # Aplicar filtros
    apolices_filtradas = []
    
    for apolice in apolices:
        # Filtro por tipo
        if apolice.tipo_residencia not in tipos_residencia:
            continue
        
        # Filtro por valor
        valor = float(apolice.valor_segurado or 0)
        if valor < valor_min or valor > valor_max:
            continue
        
        # Filtro por nível de risco
        risk_score = calculate_risk_score(apolice)
        risk_level, _ = get_risk_level(risk_score)
        if risk_level not in niveis_risco:
            continue
        
        apolices_filtradas.append(apolice)
    
    # Métricas de risco
    st.markdown("## 📊 Resumo de Risco")
    
    if apolices_filtradas:
        # Calcular métricas
        total_apolices = len(apolices_filtradas)
        risk_scores = [calculate_risk_score(a) for a in apolices_filtradas]
        avg_risk = np.mean(risk_scores)
        
        # Contar por nível
        risk_counts = {"Baixo": 0, "Médio": 0, "Alto": 0, "Crítico": 0}
        for score in risk_scores:
            level, _ = get_risk_level(score)
            risk_counts[level] += 1
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Total de Apólices", f"{total_apolices:,}")
        
        with col2:
            risk_level, color = get_risk_level(avg_risk)
            st.metric("⚠️ Risco Médio", f"{avg_risk:.1f}%", delta=risk_level)
        
        with col3:
            high_risk_percent = (risk_counts["Alto"] + risk_counts["Crítico"]) / total_apolices * 100
            st.metric("🚨 Alto Risco", f"{high_risk_percent:.1f}%")
        
        with col4:
            valor_total = sum(float(a.valor_segurado or 0) for a in apolices_filtradas)
            st.metric("💰 Exposição Total", f"R$ {valor_total/1_000_000:.1f}M")
        
        # Distribuição por nível de risco
        st.markdown("### 📊 Distribuição por Nível de Risco")
        
        col1, col2, col3, col4 = st.columns(4)
        colors = ["#00cc66", "#ffa421", "#ff7f0e", "#ff4b4b"]
        
        for i, (nivel, count) in enumerate(risk_counts.items()):
            percent = (count / total_apolices) * 100 if total_apolices > 0 else 0
            
            with [col1, col2, col3, col4][i]:
                st.markdown(f"""
                <div style="background-color: {colors[i]}20; padding: 1rem; border-radius: 10px; text-align: center; border-left: 5px solid {colors[i]};">
                    <h3 style="color: {colors[i]}; margin: 0;">{count}</h3>
                    <p style="margin: 0;"><strong>{nivel}</strong></p>
                    <p style="margin: 0; font-size: 0.9em;">{percent:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Tabs para diferentes análises
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Mapa de Risco", "📈 Análise Regional", "📊 Correlações", "🌦️ Simulação Climática"])
    
    with tab1:
        st.markdown("## 🗺️ Mapa Interativo de Risco")
        
        if apolices_filtradas:
            # Criar mapa
            risk_map = create_risk_map(apolices_filtradas, sinistros)
            
            if risk_map:
                # Mostrar mapa
                map_data = st_folium(risk_map, width=700, height=500)
                
                # Informações sobre seleção no mapa
                if map_data['last_object_clicked_popup']:
                    st.info("💡 Clique nos marcadores do mapa para ver detalhes das apólices e sinistros.")
            else:
                st.warning("Não foi possível criar o mapa. Verifique se há apólices com coordenadas.")
        else:
            st.warning("Nenhuma apólice encontrada com os filtros aplicados.")
    
    with tab2:
        st.markdown("## 📈 Análise de Risco por Região")
        
        if apolices_filtradas:
            # Criar heatmap regional
            heatmap_fig = create_risk_heatmap(apolices_filtradas)
            
            if heatmap_fig:
                st.plotly_chart(heatmap_fig, use_container_width=True)
                
                st.markdown("### 📊 Top 10 Regiões de Maior Risco")
                
                # Calcular risco por região
                risk_by_region = {}
                
                for apolice in apolices_filtradas:
                    region = apolice.cep[:5] if apolice.cep else "00000"
                    
                    if region not in risk_by_region:
                        risk_by_region[region] = []
                    
                    risk_score = calculate_risk_score(apolice)
                    risk_by_region[region].append(risk_score)
                
                # Ordenar por risco médio
                region_avg_risk = [(region, np.mean(scores)) for region, scores in risk_by_region.items()]
                region_avg_risk.sort(key=lambda x: x[1], reverse=True)
                
                # Mostrar top 10
                for i, (region, avg_risk) in enumerate(region_avg_risk[:10], 1):
                    risk_level, color = get_risk_level(avg_risk)
                    count = len(risk_by_region[region])
                    
                    st.markdown(f"""
                    **{i}. CEP {region}xxx** - {avg_risk:.1f}% ({risk_level}) - {count} apólices
                    """)
        else:
            st.warning("Nenhuma apólice encontrada com os filtros aplicados.")
    
    with tab3:
        st.markdown("## 📊 Análise de Correlações")
        
        if apolices_filtradas:
            # Criar gráficos de análise
            fig1, fig2 = create_risk_analysis_charts(apolices_filtradas, sinistros)
            
            if fig1 and fig2:
                st.plotly_chart(fig1, use_container_width=True)
                st.plotly_chart(fig2, use_container_width=True)
                
                # Análise estatística
                st.markdown("### 📈 Estatísticas de Risco")
                
                risk_scores = [calculate_risk_score(a) for a in apolices_filtradas]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Estatísticas Gerais:**")
                    st.write(f"• **Média:** {np.mean(risk_scores):.1f}%")
                    st.write(f"• **Mediana:** {np.median(risk_scores):.1f}%")
                    st.write(f"• **Desvio padrão:** {np.std(risk_scores):.1f}%")
                    st.write(f"• **Mínimo:** {np.min(risk_scores):.1f}%")
                    st.write(f"• **Máximo:** {np.max(risk_scores):.1f}%")
                
                with col2:
                    st.markdown("**Distribuição por Tipo:**")
                    
                    for tipo in tipos_residencia:
                        tipo_scores = [calculate_risk_score(a) for a in apolices_filtradas if a.tipo_residencia == tipo]
                        if tipo_scores:
                            avg_tipo = np.mean(tipo_scores)
                            st.write(f"• **{tipo.title()}:** {avg_tipo:.1f}%")
        else:
            st.warning("Nenhuma apólice encontrada com os filtros aplicados.")
    
    with tab4:
        # Simulação de impacto climático
        weather_risk = simulate_weather_impact()
        
        if apolices_filtradas:
            st.markdown("### 📊 Impacto nas Apólices Atuais")
            
            # Recalcular riscos com fator climático
            updated_risks = []
            
            for apolice in apolices_filtradas[:10]:  # Mostrar apenas 10 para performance
                original_risk = calculate_risk_score(apolice)
                updated_risk = calculate_risk_score(apolice, weather_risk=weather_risk)
                
                updated_risks.append({
                    'Apólice': apolice.numero_apolice,
                    'Tipo': apolice.tipo_residencia,
                    'Risco Original': f"{original_risk:.1f}%",
                    'Risco Atualizado': f"{updated_risk:.1f}%",
                    'Variação': f"{updated_risk - original_risk:+.1f}%"
                })
            
            df_impact = pd.DataFrame(updated_risks)
            st.dataframe(df_impact, use_container_width=True)
            
            # Alertas baseados no clima
            high_impact_count = sum(1 for r in updated_risks if float(r['Variação'].replace('%', '').replace('+', '')) > 10)
            
            if high_impact_count > 0:
                st.warning(f"⚠️ {high_impact_count} apólices com aumento de risco > 10% devido às condições climáticas!")
            else:
                st.success("✅ Condições climáticas atuais não representam risco significativo adicional.")

if __name__ == "__main__":
    main()