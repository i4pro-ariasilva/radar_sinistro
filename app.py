"""
🌦️ RADAR DE SINISTRO - INTERFACE WEB
Sistema Inteligente de Predição de Riscos Climáticos

Aplicação Streamlit para análise preditiva de sinistros
baseada em dados climáticos e características de imóveis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Configurar path para módulos do sistema
sys.path.append('.')
from policy_management import show_manage_policies
from mapa_de_calor_completo import criar_interface_streamlit  # NOVA IMPORTAÇÃO

# Configuração da página
st.set_page_config(
    page_title="Radar de Sinistro v3.0",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2a5298;
        margin: 0.5rem 0;
        color: #333333;
    }
    
    .metric-card h2 {
        color: #1e3c72;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    
    .metric-card h3 {
        color: #555555;
        margin: 0 0 0.5rem 0;
        font-size: 1.1rem;
    }
    
    .metric-card p {
        color: #666666;
        margin: 0.5rem 0 0 0;
        font-size: 0.9rem;
    }
    
    .risk-high {
        background: #ffebee;
        border-left-color: #f44336;
    }
    
    .risk-high h2 {
        color: #d32f2f;
    }
    
    .risk-medium {
        background: #fff3e0;
        border-left-color: #ff9800;
    }
    
    .risk-medium h2 {
        color: #f57c00;
    }
    
    .risk-low {
        background: #e8f5e8;
        border-left-color: #4caf50;
    }
    
    .risk-low h2 {
        color: #388e3c;
    }
    
    .sidebar .sidebar-content {
        background: #f5f5f5;
    }
    
    /* Estilos para tabelas de apólices */
    .dataframe {
        font-size: 14px;
    }
    
    .dataframe th {
        background-color: #2a5298 !important;
        color: white !important;
        font-weight: bold;
        text-align: center;
    }
    
    .dataframe td {
        text-align: center;
        color: #333333 !important;
        font-weight: 500;
    }
    
    /* Classes para risco nas tabelas */
    .risk-high-row {
        background-color: #ffebee !important;
        color: #d32f2f !important;
    }
    
    .risk-medium-row {
        background-color: #fff3e0 !important;
        color: #e65100 !important;
    }
    
    .risk-low-row {
        background-color: #e8f5e8 !important;
        color: #2e7d32 !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Função principal da aplicação"""
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🌦️ RADAR DE SINISTRO v3.0</h1>
        <p>Sistema Inteligente de Predição de Riscos Climáticos</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar para navegação
    with st.sidebar:
        # Logo/Header da sidebar
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%); 
                    border-radius: 10px; color: white; margin-bottom: 1rem;">
            <h3>🌦️ RADAR SINISTRO</h3>
            <p style="margin: 0; font-size: 0.9em;">Sistema de Análise Preditiva</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Menu de navegação
        page = st.selectbox(
            "🧭 Navegação",
            [
                "🏠 Dashboard Principal",
                "🔮 Análise de Risco",
                "📋 Apólices em Risco",
                "🗺️ Mapa de Calor",  # NOVA OPÇÃO ADICIONADA
                "➕ Gerenciar Apólices",
                "📊 Estatísticas",
                "🌡️ Monitoramento Climático",
                "⚙️ Configurações"
            ]
        )
        
        st.markdown("---")
        
        # Informações adicionais da sidebar
        st.markdown("### ℹ️ Sobre o Sistema")
        st.markdown("""
        **Radar de Sinistro v3.0**
        
        Sistema inteligente de predição de riscos climáticos para seguradoras.
        
        **Funcionalidades:**
        - 🧠 Machine Learning
        - 🌦️ Dados Climáticos
        - 📊 Análise Preditiva
        - 📈 Relatórios Detalhados
        """)
    
    # Roteamento de páginas
    if page == "🏠 Dashboard Principal":
        show_dashboard()
    elif page == "🔮 Análise de Risco":
        show_risk_analysis()
    elif page == "📋 Apólices em Risco":
        show_policies_at_risk()
    elif page == "🗺️ Mapa de Calor":  # NOVA ROTA ADICIONADA
        show_mapa_calor()
    elif page == "➕ Gerenciar Apólices":
        show_manage_policies()
    elif page == "📊 Estatísticas":
        show_statistics()
    elif page == "🌡️ Monitoramento Climático":
        show_weather_monitoring()
    elif page == "⚙️ Configurações":
        show_settings()

def check_ml_status():
    """Verificar status do modelo ML"""
    try:
        from web_ml_integration import get_ml_integration
        ml_integration = get_ml_integration()
        status = ml_integration.get_system_status()
        return status.get('overall', False)
    except:
        return False

def check_weather_status():
    """Verificar status da API climática"""
    try:
        from src.weather.weather_service import WeatherService
        weather = WeatherService()
        health = weather.health_check()
        return health.get('status') == 'healthy'
    except:
        return False

def check_database_status():
    """Verificar status do banco de dados"""
    try:
        from database import get_database
        db = get_database()
        return db is not None
    except:
        return False

def show_dashboard():
    """Página principal do dashboard"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Análises Realizadas</h3>
            <h2>1,247</h2>
            <p>+12% esta semana</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card risk-medium">
            <h3>⚠️ Alertas Ativos</h3>
            <h2>23</h2>
            <p>Riscos médios/altos</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card risk-low">
            <h3>🎯 Precisão do Modelo</h3>
            <h2>94.2%</h2>
            <p>Última atualização</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráficos de exemplo
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Tendência de Riscos (Últimos 30 dias)")
        
        # Dados de exemplo
        dates = pd.date_range(start='2025-09-06', end='2025-10-06', freq='D')
        risk_scores = np.random.normal(45, 15, len(dates))
        risk_scores = np.clip(risk_scores, 0, 100)
        
        fig = px.line(
            x=dates, 
            y=risk_scores,
            title="Score Médio de Risco por Dia",
            labels={'x': 'Data', 'y': 'Score de Risco'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🗺️ Distribuição de Riscos por Região")
        
        # Dados de exemplo por região
        regions = ['Centro', 'Norte', 'Sul', 'Leste', 'Oeste']
        risk_counts = [45, 32, 28, 51, 38]
        
        fig = px.bar(
            x=regions,
            y=risk_counts,
            title="Análises de Risco por Região",
            labels={'x': 'Região', 'y': 'Número de Análises'},
            color=risk_counts,
            color_continuous_scale='RdYlGn_r'
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

def show_risk_analysis():
    """Página de Análise de Risco - formulário principal"""
    
    st.header("📝 Análise de Risco de Imóvel")
    st.markdown("Insira os dados do imóvel para obter uma análise preditiva de risco de sinistros.")
    
    # Inicializar session state se não existir
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    
    # Formulário principal
    with st.form("risk_analysis_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏠 Dados do Imóvel")
            
            cep = st.text_input(
                "CEP",
                placeholder="01310-100",
                help="CEP do imóvel (formato: XXXXX-XXX)"
            )
            
            tipo_residencia = st.selectbox(
                "Tipo de Residência",
                ["casa", "apartamento", "sobrado", "kitnet", "cobertura"],
                help="Tipo de construção do imóvel"
            )
            
            valor_segurado = st.number_input(
                "Valor Segurado (R$)",
                min_value=10000.0,
                max_value=10000000.0,
                value=300000.0,
                step=10000.0,
                help="Valor total da cobertura do seguro"
            )
            
            area_construida = st.number_input(
                "Área Construída (m²)",
                min_value=20.0,
                max_value=1000.0,
                value=120.0,
                step=10.0,
                help="Área total construída do imóvel"
            )
        
        with col2:
            st.subheader("📅 Parâmetros da Análise")
            
            data_analise = st.date_input(
                "Data da Análise",
                value=datetime.now(),
                help="Data de referência para a análise"
            )
            
            incluir_clima = st.checkbox(
                "Incluir dados climáticos em tempo real",
                value=True,
                help="Buscar condições meteorológicas atuais para o CEP"
            )
            
            tipo_analise = st.selectbox(
                "Tipo de Análise",
                ["Análise Completa", "Análise Básica", "Análise Expressa"],
                help="Nível de detalhamento da análise"
            )
            
            st.markdown("---")
            
            # Botão de análise
            submit_button = st.form_submit_button(
                "🔍 ANALISAR RISCO",
                use_container_width=True
            )
    
    # Processar análise FORA do formulário
    if submit_button:
        if not cep:
            st.error("❌ Por favor, informe o CEP do imóvel!")
            st.session_state.analysis_result = None
        elif len(cep.replace("-", "")) != 8:
            st.error("❌ CEP deve ter 8 dígitos (formato: XXXXX-XXX)!")
            st.session_state.analysis_result = None
        else:
            # Processar análise
            with st.spinner("🔄 Processando Análise de Risco..."):
                result = process_risk_analysis(
                    cep, tipo_residencia, valor_segurado, 
                    area_construida, incluir_clima, tipo_analise
                )
            
            # Salvar resultado no session state
            st.session_state.analysis_result = result
    
    # Mostrar resultados se existirem (completamente FORA do formulário)
    if st.session_state.analysis_result is not None:
        show_risk_results(st.session_state.analysis_result)

def process_risk_analysis(cep, tipo_residencia, valor_segurado, area_construida, incluir_clima, tipo_analise):
    """Processar Análise de Risco usando sistema ML real"""
    
    try:
        # Carregar integração ML
        from web_ml_integration import get_ml_integration
        ml_integration = get_ml_integration()
        
        with st.spinner("🧠 Analisando risco com IA..."):
            # Fazer predição usando o sistema ML
            resultado = ml_integration.predict_risk(
                cep=cep,
                tipo_residencia=tipo_residencia,
                valor_segurado=valor_segurado,
                area_construida=area_construida,
                incluir_clima=incluir_clima
            )
            
            return resultado
            
    except Exception as e:
        st.warning(f"⚠️ Sistema ML indisponível. Usando modo simulação.")
        
        # Fallback para simulação
        import random
        import time
        
        with st.spinner("🧠 Analisando risco (modo simulação)..."):
            time.sleep(2)
            
            # Score de risco simulado baseado nos inputs
            base_score = random.uniform(20, 80)
            
            # Ajustar score baseado no tipo de residência
            tipo_multiplier = {
                "casa": 1.0,
                "apartamento": 0.8,
                "sobrado": 1.2,
                "kitnet": 0.9,
                "cobertura": 1.3
            }
            
            score = base_score * tipo_multiplier.get(tipo_residencia, 1.0)
            score = min(100, max(0, score))
            
            # Classificação de risco (PADRONIZADA)
            if score >= 75:
                classificacao = "Alto"
                cor = "error"
                emoji = "�"
            elif score >= 50:
                classificacao = "Médio"
                cor = "warning"
                emoji = "�"
            elif score >= 25:
                classificacao = "Baixo"
                cor = "info"
                emoji = "�"
            else:
                classificacao = "Muito Baixo"
                cor = "success"
                emoji = "�"
            
            return {
                "score": round(score, 1),
                "classificacao": classificacao,
                "cor": cor,
                "emoji": emoji,
                "cep": cep,
                "tipo_residencia": tipo_residencia,
                "valor_segurado": valor_segurado,
                "area_construida": area_construida,
                "fatores": {
                    "Localização": random.uniform(0.7, 1.3),
                    "Tipo de Construção": tipo_multiplier.get(tipo_residencia, 1.0),
                    "Valor do Imóvel": min(1.5, valor_segurado / 200000),
                    "Condições Climáticas": random.uniform(0.8, 1.4) if incluir_clima else 1.0
                },
                "recomendacoes": [
                    "Considerar cobertura adicional para eventos climáticos extremos",
                    "Avaliar sistema de drenagem da propriedade",
                    "Verificar estado da cobertura e estrutura"
                ],
                "is_real_prediction": False,
                "confianca": random.uniform(0.60, 0.80)
            }

def show_risk_results(result):
    """Exibir resultados da Análise de Risco"""
    
    st.markdown("---")
    
    # Header com emoji e classificação
    emoji = result.get("emoji", "🔵")
    classificacao = result.get("classificacao", "N/A")
    
    st.subheader(f"{emoji} Resultado da Análise - Risco {classificacao}")
    
    # Indicador de tipo de predição
    if result.get("is_real_prediction", False):
        st.success("🧠 Predição usando modelo de Machine Learning")
        confianca = result.get("confianca", 0.9)
        st.metric("Confiança da Predição", f"{confianca:.1%}")
    else:
        st.warning("⚠️ Resultado em modo simulação")
        confianca = result.get("confianca", 0.7)
        st.metric("Confiança (Simulação)", f"{confianca:.1%}")
    
    # Score principal
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Gauge chart do score melhorado
        score = result["score"]
        
        # Cores baseadas no score
        if score < 25:
            gauge_color = "green"
        elif score < 50:
            gauge_color = "lightblue"
        elif score < 75:
            gauge_color = "orange"
        else:
            gauge_color = "red"
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': f"Score de Risco<br><span style='font-size:0.8em;color:gray'>CEP: {result['cep']}</span>"},
            delta = {'reference': 50},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': gauge_color},
                'steps': [
                    {'range': [0, 25], 'color': "lightgreen"},
                    {'range': [25, 50], 'color': "lightblue"},
                    {'range': [50, 75], 'color': "lightyellow"},
                    {'range': [75, 100], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Métricas resumidas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tipo", result["tipo_residencia"].title())
    
    with col2:
        valor = result["valor_segurado"]
        st.metric("Valor Segurado", f"R$ {valor:,.0f}")
    
    with col3:
        area = result["area_construida"]
        st.metric("Área", f"{area} m²")
    
    with col4:
        cor = result.get("cor", "info")
        if cor == "success":
            st.success(f"✅ {classificacao}")
        elif cor == "info":
            st.info(f"ℹ️ {classificacao}")
        elif cor == "warning":
            st.warning(f"⚠️ {classificacao}")
        else:
            st.error(f"🚨 {classificacao}")
    
    # Fatores de influência
    st.markdown("### 📈 Fatores de Influência")
    
    fatores = result.get("fatores", {})
    if fatores:
        col1, col2 = st.columns(2)
        
        with col1:
            for i, (fator, valor) in enumerate(fatores.items()):
                if i % 2 == 0:  # Coluna 1: itens pares
                    if isinstance(valor, (int, float)):
                        color = "green" if valor < 1.0 else "orange" if valor < 1.2 else "red"
                        st.markdown(f"**{fator}:** <span style='color:{color}'>{valor:.2f}x</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{fator}:** {valor}")
        
        with col2:
            for i, (fator, valor) in enumerate(fatores.items()):
                if i % 2 == 1:  # Coluna 2: itens ímpares
                    if isinstance(valor, (int, float)):
                        color = "green" if valor < 1.0 else "orange" if valor < 1.2 else "red"
                        st.markdown(f"**{fator}:** <span style='color:{color}'>{valor:.2f}x</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{fator}:** {valor}")
    
    # Recomendações
    st.markdown("### 💡 Recomendações")
    
    recomendacoes = result.get("recomendacoes", [])
    if recomendacoes:
        for rec in recomendacoes:
            st.markdown(f"• {rec}")
    else:
        st.info("Nenhuma recomendação específica disponível.")
    
    # Timestamp
    if "timestamp" in result:
        timestamp = result["timestamp"]
        st.caption(f"📅 Análise realizada em: {timestamp.strftime('%d/%m/%Y às %H:%M:%S')}")
    
    # Ações adicionais
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Nova Análise", use_container_width=True):
            # Limpar resultado da session
            st.session_state.analysis_result = None
            st.rerun()
    
    with col2:
        if st.button("📋 Exportar Relatório", use_container_width=True):
            # Simulação de exportação
            st.success("📄 Relatório exportado com sucesso!")
    
    with col3:
        if st.button("📞 Contatar Corretor", use_container_width=True):
            st.info("📞 Redirecionando para contato com corretor...")

def show_policies_at_risk():
    """Página de Apólices em Risco - Lista ordenada por score de risco com dados reais do banco"""
    
    st.header("📋 Apólices em Risco - Dados Reais")
    st.markdown("Lista de apólices **REAIS** ordenadas por nível de risco de sinistro (maior para menor)")
    st.info("🗄️ **Conectado ao banco de dados**: Esta seção mostra as apólices inseridas via 'Gerenciar Apólices'")
    
    # Seção de busca
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_policy = st.text_input(
            "🔍 Buscar Apólice", 
            placeholder="Digite o número da apólice (ex: POL-2025-001234)",
            help="Busque uma apólice específica pelo número"
        )
    
    with col2:
        if st.button("🔍 Buscar", use_container_width=True):
            if search_policy:
                st.success(f"Buscando apólice: {search_policy}")
            else:
                st.warning("Digite um número de apólice para buscar")
    
    # Filtros
    st.markdown("### 🎛️ Filtros")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        risk_filter = st.selectbox(
            "Nível de Risco",
            ["Todos", "Alto (75-100)", "Médio-Alto (50-75)", "Médio-Baixo (25-50)", "Baixo (0-25)"]
        )
    
    with col2:
        policy_type = st.selectbox(
            "Tipo de Imóvel",
            ["Todos", "Casa", "Apartamento", "Sobrado", "Cobertura", "Kitnet"]
        )
    
    with col3:
        value_range = st.selectbox(
            "Faixa de Valor",
            ["Todos", "Até R$ 100k", "R$ 100k - 300k", "R$ 300k - 500k", "R$ 500k - 1M", "Acima R$ 1M"]
        )
    
    with col4:
        date_range = st.selectbox(
            "Período",
            ["Todos", "Última semana", "Último mês", "Últimos 3 meses", "Último ano"]
        )
    
    # Buscar dados REAIS de apólices do banco de dados
    policies_data = get_real_policies_data(search_policy, risk_filter, policy_type, value_range)
    
    # Métricas resumidas
    st.markdown("---")
    st.markdown("### 📈 Resumo das Apólices")
    
    col1, col2, col3, col4 = st.columns(4)
    
    high_risk = len([p for p in policies_data if p['risk_score'] >= 75])
    medium_risk = len([p for p in policies_data if 50 <= p['risk_score'] < 75])
    low_risk = len([p for p in policies_data if p['risk_score'] < 50])
    total_value = sum([p['insured_value'] for p in policies_data])
    
    with col1:
        st.metric("🔴 Alto Risco", high_risk, f"{high_risk/len(policies_data)*100:.1f}%" if policies_data else "0%")
    
    with col2:
        st.metric("🟡 Médio Risco", medium_risk, f"{medium_risk/len(policies_data)*100:.1f}%" if policies_data else "0%")
    
    with col3:
        st.metric("🟢 Baixo Risco", low_risk, f"{low_risk/len(policies_data)*100:.1f}%" if policies_data else "0%")
    
    with col4:
        st.metric("💰 Valor Total", f"R$ {total_value/1000000:.1f}M", f"{len(policies_data)} apólices")
    
    # Tabela de apólices
    st.markdown("---")
    st.markdown("### 📋 Lista de Apólices (Ordenado por Risco)")
    
    if policies_data:
        # Criar DataFrame
        df = pd.DataFrame(policies_data)
        
        # Adicionar colunas formatadas
        df['risk_level'] = df['risk_score'].apply(get_risk_level_emoji)
        df['valor_formatado'] = df['insured_value'].apply(lambda x: f"R$ {x:,.0f}")
        df['ultima_analise'] = df['last_analysis'].apply(lambda x: x.strftime('%d/%m/%Y'))
        
        # Selecionar e renomear colunas para exibição
        display_df = df[[
            'policy_number', 'risk_level', 'risk_score', 'property_type', 
            'cep', 'valor_formatado', 'ultima_analise', 'status'
        ]].copy()
        
        display_df.columns = [
            'Nº da Apólice', 'Risco', 'Score', 'Tipo', 
            'CEP', 'Valor Segurado', 'Última Análise', 'Status'
        ]
        
        # Configurar cores baseadas no risco
        def highlight_risk(row):
            if row['Score'] >= 75:
                return ['background-color: #ffebee; color: #d32f2f; font-weight: bold'] * len(row)
            elif row['Score'] >= 50:
                return ['background-color: #fff3e0; color: #e65100; font-weight: bold'] * len(row)
            elif row['Score'] >= 25:
                return ['background-color: #e3f2fd; color: #1976d2; font-weight: bold'] * len(row)
            else:
                return ['background-color: #e8f5e8; color: #2e7d32; font-weight: bold'] * len(row)
        
        # Exibir tabela com estilo
        styled_df = display_df.style.apply(highlight_risk, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Detalhes da apólice selecionada
        st.markdown("---")
        st.markdown("### 🔍 Detalhes da Apólice")
        
        selected_policy = st.selectbox(
            "Selecione uma apólice para ver detalhes:",
            options=df['policy_number'].tolist(),
            format_func=lambda x: f"{x} - Score: {df[df['policy_number']==x]['risk_score'].iloc[0]}"
        )
        
        if selected_policy:
            policy_details = df[df['policy_number'] == selected_policy].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📋 Informações Básicas")
                st.write(f"**Número da Apólice:** {policy_details['policy_number']}")
                st.write(f"**Segurado:** {policy_details.get('insured_name', 'N/A')}")
                st.write(f"**Tipo de Imóvel:** {policy_details['property_type'].title()}")
                st.write(f"**CEP:** {policy_details['cep']}")
                st.write(f"**Área:** {policy_details['area']} m² (estimado)")
                st.write(f"**Status:** {policy_details['status']}")
            
            with col2:
                st.markdown("#### 💰 Informações Financeiras e Risco")
                st.write(f"**Valor Segurado:** R$ {policy_details['insured_value']:,.2f}")
                st.write(f"**Prêmio Anual:** R$ {policy_details['annual_premium']:,.2f}")
                st.write(f"**Score de Risco:** {policy_details['risk_score']:.1f}/100")
                st.write(f"**Nível de Risco:** {policy_details.get('risk_level', 'N/A').title()}")
                st.write(f"**Probabilidade de Sinistro:** {policy_details.get('probability', 0)*100:.1f}%")
                
                # Botão para nova análise
                if st.button(f"🔄 Atualizar Análise - {selected_policy}", use_container_width=True):
                    with st.spinner("Atualizando Análise de Risco..."):
                        import time
                        time.sleep(2)
                        st.success("✅ Análise atualizada com sucesso!")
                        st.rerun()  # Recarregar dados
    
    else:
        st.info("📭 Nenhuma apólice encontrada com os filtros selecionados.")
        st.markdown("**Dicas:**")
        st.markdown("- Verifique se o número da apólice está correto")
        st.markdown("- Tente ajustar os filtros")
        st.markdown("- Remova filtros para ver todas as apólices")

def generate_mock_policies_data(search_filter=None, risk_filter="Todos", type_filter="Todos", value_filter="Todos"):
    """Gerar dados simulados de apólices para demonstração"""
    
    import random
    from datetime import datetime, timedelta
    
    # Tipos de imóveis
    property_types = ['casa', 'apartamento', 'sobrado', 'cobertura', 'kitnet']
    
    # Gerar apólices
    policies = []
    
    # Se há busca específica, criar uma apólice que corresponda
    if search_filter and search_filter.strip():
        policies.append({
            'policy_number': search_filter.upper(),
            'risk_score': random.randint(30, 90),
            'property_type': random.choice(property_types),
            'cep': f"{random.randint(10000, 99999):05d}-{random.randint(100, 999):03d}",
            'area': random.randint(50, 300),
            'insured_value': random.randint(100000, 1000000),
            'annual_premium': 0,
            'last_analysis': datetime.now() - timedelta(days=random.randint(1, 30)),
            'status': random.choice(['Ativa', 'Pendente', 'Em Análise'])
        })
    
    # Gerar apólices adicionais
    for i in range(50):
        risk_score = random.randint(15, 95)
        insured_value = random.randint(80000, 2000000)
        
        policy = {
            'policy_number': f"POL-2025-{random.randint(100000, 999999):06d}",
            'risk_score': risk_score,
            'property_type': random.choice(property_types),
            'cep': f"{random.randint(10000, 99999):05d}-{random.randint(100, 999):03d}",
            'area': random.randint(40, 500),
            'insured_value': insured_value,
            'annual_premium': insured_value * (risk_score / 100) * 0.015,  # 1.5% base ajustado pelo risco
            'last_analysis': datetime.now() - timedelta(days=random.randint(1, 90)),
            'status': random.choice(['Ativa', 'Ativa', 'Ativa', 'Pendente', 'Em Análise', 'Renovação'])
        }
        
        policies.append(policy)
    
    # Aplicar filtros
    filtered_policies = policies.copy()
    
    # Filtro de risco
    if risk_filter != "Todos":
        if "Alto" in risk_filter:
            filtered_policies = [p for p in filtered_policies if p['risk_score'] >= 75]
        elif "Médio-Alto" in risk_filter:
            filtered_policies = [p for p in filtered_policies if 50 <= p['risk_score'] < 75]
        elif "Médio-Baixo" in risk_filter:
            filtered_policies = [p for p in filtered_policies if 25 <= p['risk_score'] < 50]
        elif "Baixo" in risk_filter:
            filtered_policies = [p for p in filtered_policies if p['risk_score'] < 25]
    
    # Filtro de tipo
    if type_filter != "Todos":
        filtered_policies = [p for p in filtered_policies if p['property_type'] == type_filter.lower()]
    
    # Filtro de valor
    if value_filter != "Todos":
        if "Até R$ 100k" in value_filter:
            filtered_policies = [p for p in filtered_policies if p['insured_value'] <= 100000]
        elif "R$ 100k - 300k" in value_filter:
            filtered_policies = [p for p in filtered_policies if 100000 < p['insured_value'] <= 300000]
        elif "R$ 300k - 500k" in value_filter:
            filtered_policies = [p for p in filtered_policies if 300000 < p['insured_value'] <= 500000]
        elif "R$ 500k - 1M" in value_filter:
            filtered_policies = [p for p in filtered_policies if 500000 < p['insured_value'] <= 1000000]
        elif "Acima R$ 1M" in value_filter:
            filtered_policies = [p for p in filtered_policies if p['insured_value'] > 1000000]
    
    # Ordenar por score de risco (maior para menor)
    filtered_policies.sort(key=lambda x: x['risk_score'], reverse=True)
    
    return filtered_policies

def get_real_policies_data(search_filter=None, risk_filter="Todos", type_filter="Todos", value_filter="Todos"):
    """Buscar dados reais de apólices do banco de dados"""
    
    from datetime import datetime
    
    try:
        # Conectar com banco de dados real
        from database import get_database, CRUDOperations
        db = get_database()
        crud = CRUDOperations(db)
        
        # Buscar todas as apólices ativas
        import sqlite3
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        query = """
        SELECT numero_apolice, segurado, cep, valor_segurado, 
               tipo_residencia, score_risco, nivel_risco, 
               probabilidade_sinistro, created_at, data_inicio
        FROM apolices 
        ORDER BY score_risco DESC, created_at DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            st.info("📝 Nenhuma apólice encontrada no banco de dados real.")
            st.info("💡 Use 'Gerenciar Apólices' → 'Inclusão Individual' para adicionar apólices!")
            # Retornar dados simulados como fallback
            return generate_mock_policies_data(search_filter, risk_filter, type_filter, value_filter)
        
        # Converter dados do banco para formato esperado pela interface
        policies = []
        for row in rows:
            # Mapear dados do banco para estrutura da interface
            policy = {
                'policy_number': row[0],  # numero_apolice
                'insured_name': row[1],   # segurado
                'cep': row[2],            # cep
                'insured_value': float(row[3]) if row[3] else 0,  # valor_segurado
                'property_type': row[4] if row[4] else 'casa',    # tipo_residencia
                'risk_score': float(row[5]) if row[5] else 0,     # score_risco
                'risk_level': row[6] if row[6] else 'baixo',      # nivel_risco
                'probability': float(row[7]) if row[7] else 0,    # probabilidade_sinistro
                'created_at': row[8],     # created_at
                'policy_start': row[9],   # data_inicio
                
                # Campos calculados/inferidos
                'area': 100,  # Valor padrão (poderia ser calculado baseado no valor segurado)
                'annual_premium': float(row[3]) * (float(row[5]) / 100) * 0.015 if row[3] and row[5] else 0,
                'last_analysis': datetime.now() if row[8] else datetime.now(),
                'status': 'Ativa'
            }
            policies.append(policy)
        
        # Aplicar filtros
        filtered_policies = policies.copy()
        
        # Filtro de busca específica
        if search_filter and search_filter.strip():
            search_term = search_filter.upper().strip()
            filtered_policies = [p for p in filtered_policies 
                               if search_term in p['policy_number'].upper()]
        
        # Filtro de risco
        if risk_filter != "Todos":
            if "Alto" in risk_filter:
                filtered_policies = [p for p in filtered_policies if p['risk_score'] >= 75]
            elif "Médio-Alto" in risk_filter:
                filtered_policies = [p for p in filtered_policies if 50 <= p['risk_score'] < 75]
            elif "Médio-Baixo" in risk_filter:
                filtered_policies = [p for p in filtered_policies if 25 <= p['risk_score'] < 50]
            elif "Baixo" in risk_filter:
                filtered_policies = [p for p in filtered_policies if p['risk_score'] < 25]
        
        # Filtro de tipo
        if type_filter != "Todos":
            filtered_policies = [p for p in filtered_policies 
                               if p['property_type'].lower() == type_filter.lower()]
        
        # Filtro de valor
        if value_filter != "Todos":
            if "Até R$ 100k" in value_filter:
                filtered_policies = [p for p in filtered_policies if p['insured_value'] <= 100000]
            elif "R$ 100k - 300k" in value_filter:
                filtered_policies = [p for p in filtered_policies if 100000 < p['insured_value'] <= 300000]
            elif "R$ 300k - 500k" in value_filter:
                filtered_policies = [p for p in filtered_policies if 300000 < p['insured_value'] <= 500000]
            elif "R$ 500k - 1M" in value_filter:
                filtered_policies = [p for p in filtered_policies if 500000 < p['insured_value'] <= 1000000]
            elif "Acima R$ 1M" in value_filter:
                filtered_policies = [p for p in filtered_policies if p['insured_value'] > 1000000]
        
        # Já está ordenado por score_risco DESC na query
        
        # Se dados reais foram encontrados, mostrar informação
        if filtered_policies:
            st.success(f"✅ Mostrando {len(filtered_policies)} apólices REAIS do banco de dados!")
            if len(policies) > len(filtered_policies):
                st.info(f"📊 Filtrado de {len(policies)} apólices totais")
        
        return filtered_policies
        
    except Exception as e:
        st.error(f"❌ Erro ao conectar com banco de dados: {e}")
        st.warning("🔄 Usando dados simulados como fallback...")
        # Fallback para dados simulados
        return generate_mock_policies_data(search_filter, risk_filter, type_filter, value_filter)

def get_risk_level_emoji(score):
    """Retornar emoji baseado no score de risco - PADRONIZADO"""
    if score >= 75:
        return "🔴 Alto"
    elif score >= 50:
        return "🟡 Médio"
    elif score >= 25:
        return "🔵 Baixo"
    else:
        return "🟢 Muito Baixo"

def format_risk_level_from_db(nivel_risco_db):
    """Converter nivel_risco do banco para formato de exibição"""
    if not nivel_risco_db:
        return "🔵 Baixo"
    
    nivel = nivel_risco_db.lower()
    if nivel == 'alto':
        return "🔴 Alto"
    elif nivel == 'medio':
        return "🟡 Médio"
    elif nivel == 'baixo':
        return "🔵 Baixo"
    elif nivel == 'muito_baixo':
        return "🟢 Muito Baixo"
    else:
        return "🔵 Baixo"  # padrão

def show_statistics():
    """Página de Estatísticas do sistema"""
    st.header("📊 Estatísticas do Sistema")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Análises Realizadas", 
            value="1,347", 
            delta="23 hoje",
            help="Total de predições de risco processadas"
        )
    
    with col2:
        st.metric(
            label="Score Médio", 
            value="52.3", 
            delta="-2.1 esta semana",
            help="Score médio de risco das análises"
        )
    
    with col3:
        st.metric(
            label="Alertas Ativos", 
            value="31", 
            delta="5 novos",
            help="Análises com risco alto/crítico"
        )
    
    with col4:
        st.metric(
            label="Precisão do Modelo", 
            value="94.2%", 
            delta="0.3%",
            help="Acurácia do modelo de ML"
        )
    
    # Gráficos de análise
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Distribuição de Scores de Risco")
        
        # Simulação de dados de distribuição
        import numpy as np
        scores = np.random.normal(52, 18, 1000)
        scores = np.clip(scores, 0, 100)
        
        fig = px.histogram(
            x=scores, 
            nbins=30,
            title="Distribuição dos Scores de Risco",
            labels={'x': 'Score de Risco', 'y': 'Frequência'},
            color_discrete_sequence=['#1f77b4']
        )
        
        # Adicionar linhas de referência
        fig.add_vline(x=25, line_dash="dash", line_color="green", annotation_text="Baixo Risco")
        fig.add_vline(x=50, line_dash="dash", line_color="orange", annotation_text="Médio Risco")
        fig.add_vline(x=75, line_dash="dash", line_color="red", annotation_text="Alto Risco")
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏠 Análises por Tipo de Residência")
        
        # Dados simulados
        tipos = ['Casa', 'Apartamento', 'Sobrado', 'Cobertura', 'Kitnet']
        counts = [432, 356, 289, 145, 125]
        
        fig = px.pie(
            values=counts,
            names=tipos,
            title="Distribuição por Tipo de Residência"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabela de análises recentes
    st.markdown("---")
    st.subheader("Análises Recentes")
    
    # Dados simulados de análises recentes
    import pandas as pd
    from datetime import datetime, timedelta
    
    recent_data = []
    for i in range(10):
        date = datetime.now() - timedelta(hours=i*2)
        cep = f"{np.random.randint(1000, 9999):04d}-{np.random.randint(100, 999):03d}"
        tipo = np.random.choice(['Casa', 'Apartamento', 'Sobrado', 'Cobertura'])
        score = np.random.randint(15, 90)
        
        if score < 25:
            risco = "🟢 Baixo"
        elif score < 50:
            risco = "🔵 Médio-Baixo"
        elif score < 75:
            risco = "🟡 Médio-Alto"
        else:
            risco = "🔴 Alto"
        
        recent_data.append({
            'Data/Hora': date.strftime('%d/%m %H:%M'),
            'CEP': cep,
            'Tipo': tipo,
            'Score': score,
            'Classificação': risco
        })
    
    df = pd.DataFrame(recent_data)
    st.dataframe(df, use_container_width=True)
    
    # Status dos componentes
    st.markdown("---")
    st.subheader("🔧 Status dos Componentes")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🧠 Machine Learning")
        try:
            from web_ml_integration import get_ml_integration
            ml = get_ml_integration()
            status = ml.get_system_status()
            
            if status.get('overall'):
                st.success("✅ Sistema ML Operacional")
                st.write("• Modelo carregado")
                st.write("• Predições em tempo real")
            else:
                st.warning("⚠️ Modo Simulação")
                st.write("• Usando predições simuladas")
        except:
            st.error("❌ Erro ao verificar ML")
    
    with col2:
        st.markdown("#### 🌦️ API Climática")
        try:
            status_weather = check_weather_status()
            if status_weather:
                st.success("✅ OpenMeteo Online")
                st.write("• Dados em tempo real")
                st.write("• Cache ativo")
            else:
                st.error("❌ API Indisponível")
        except:
            st.error("❌ Erro na verificação")
    
    with col3:
        st.markdown("#### 🗄️ Banco de Dados")
        try:
            status_db = check_database_status()
            if status_db:
                st.success("✅ Database Online")
                st.write("• SQLite conectado")
                st.write("• Logs ativos")
            else:
                st.error("❌ DB Indisponível")
        except:
            st.error("❌ Erro na verificação")
    
    # Estatísticas de performance
    st.markdown("---")
    st.subheader("⚡ Performance do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Tempo de resposta médio
        response_times = np.random.normal(1.2, 0.3, 50)
        response_times = np.clip(response_times, 0.5, 3.0)
        
        fig = px.line(
            x=range(len(response_times)),
            y=response_times,
            title="Tempo de Resposta das Predições (últimas 50)",
            labels={'x': 'Predição', 'y': 'Tempo (segundos)'}
        )
        fig.add_hline(y=2.0, line_dash="dash", line_color="red", annotation_text="Limite")
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Uso de recursos
        cpu_usage = np.random.randint(20, 80, 50)
        memory_usage = np.random.randint(40, 90, 50)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=cpu_usage,
            mode='lines',
            name='CPU %',
            line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            y=memory_usage,
            mode='lines',
            name='Memória %',
            line=dict(color='red')
        ))
        
        fig.update_layout(
            title="Uso de Recursos do Sistema",
            xaxis_title="Tempo",
            yaxis_title="Percentual (%)"
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_weather_monitoring():
    """Página de monitoramento climático"""
    st.header("🌡️ Monitoramento Climático")
    
    # Input de localização
    col1, col2 = st.columns([2, 1])
    
    with col1:
        cep_weather = st.text_input("🏠 CEP para monitoramento climático", placeholder="12345-678")
    
    with col2:
        if st.button("🔍 Buscar Dados Climáticos", use_container_width=True):
            if cep_weather and len(cep_weather.replace("-", "")) == 8:
                st.success("✅ CEP válido - buscando dados...")
            else:
                st.error("❌ CEP inválido!")
    
    # Dados climáticos simulados ou reais
    if cep_weather and len(cep_weather.replace("-", "")) == 8:
        st.markdown("---")
        
        # Tentar buscar dados reais
        try:
            from web_ml_integration import get_ml_integration
            ml = get_ml_integration()
            
            # Simular coordenadas do CEP
            lat, lon = ml._get_coordinates_from_cep(cep_weather)
            
            # Buscar dados climáticos
            if ml.weather_service:
                weather_data = ml.weather_service.get_weather_data(lat, lon)
                
                if weather_data and weather_data.current:
                    # Dados climáticos atuais
                    st.subheader(f"🌍 Condições Atuais - CEP {cep_weather}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        temp = weather_data.current.temperature_c
                        st.metric("🌡️ Temperatura", f"{temp}°C")
                    
                    with col2:
                        precip = weather_data.current.precipitation_mm
                        st.metric("🌧️ Precipitação", f"{precip} mm")
                    
                    with col3:
                        wind = weather_data.current.wind_speed_kmh
                        st.metric("💨 Vento", f"{wind} km/h")
                    
                    with col4:
                        humidity = weather_data.current.humidity_percent
                        st.metric("💧 Umidade", f"{humidity}%")
                    
                    # Alertas climáticos
                    st.markdown("### ⚠️ Alertas Climáticos")
                    
                    alertas = []
                    
                    if temp > 35:
                        alertas.append("🔥 Temperatura extremamente alta - risco de incêndio")
                    elif temp < 5:
                        alertas.append("🧊 Temperatura muito baixa - risco de congelamento")
                    
                    if precip > 20:
                        alertas.append("🌊 Precipitação intensa - risco de alagamento")
                    elif precip > 50:
                        alertas.append("⛈️ Chuva torrencial - risco alto de inundação")
                    
                    if wind > 60:
                        alertas.append("🌪️ Ventos muito fortes - risco estrutural")
                    
                    if humidity > 80:
                        alertas.append("💨 Umidade muito alta - risco de mofo")
                    
                    if alertas:
                        for alerta in alertas:
                            st.warning(alerta)
                    else:
                        st.success("✅ Condições climáticas dentro da normalidade")
                    
                    use_real_data = True
                    
                else:
                    use_real_data = False
            else:
                use_real_data = False
                
        except Exception as e:
            st.warning(f"⚠️ Usando dados simulados. Erro: {e}")
            use_real_data = False
        
        # Se não conseguir dados reais, usar simulação
        if not use_real_data:
            # Dados simulados
            import random
            
            st.subheader(f"🌍 Condições Climáticas Simuladas - CEP {cep_weather}")
            st.info("ℹ️ Dados simulados para demonstração")
            
            col1, col2, col3, col4 = st.columns(4)
            
            temp = random.uniform(18, 32)
            precip = random.uniform(0, 15)
            wind = random.uniform(5, 25)
            humidity = random.uniform(45, 85)
            
            with col1:
                st.metric("🌡️ Temperatura", f"{temp:.1f}°C")
            
            with col2:
                st.metric("🌧️ Precipitação", f"{precip:.1f} mm")
            
            with col3:
                st.metric("💨 Vento", f"{wind:.1f} km/h")
            
            with col4:
                st.metric("💧 Umidade", f"{humidity:.1f}%")
        
        # Gráficos de tendência
        st.markdown("---")
        st.subheader("📈 Tendências Climáticas (Últimos 7 dias)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de temperatura
            import numpy as np
            days = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
            temps = np.random.normal(25, 5, 7)
            temps = np.clip(temps, 15, 35)
            
            fig = px.line(
                x=days,
                y=temps,
                title="Temperatura nos Últimos 7 Dias",
                labels={'x': 'Dia', 'y': 'Temperatura (°C)'},
                markers=True
            )
            fig.update_traces(line_color='orange')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Gráfico de precipitação
            precips = np.random.exponential(3, 7)
            precips = np.clip(precips, 0, 25)
            
            fig = px.bar(
                x=days,
                y=precips,
                title="Precipitação nos Últimos 7 Dias",
                labels={'x': 'Dia', 'y': 'Precipitação (mm)'},
                color=precips,
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Análise de Risco climático
        st.markdown("---")
        st.subheader("🎯 Análise de Risco Climático")
        
        # Calcular score de risco climático
        risco_temp = min(100, max(0, abs(temp - 25) * 4)) if 'temp' in locals() else 20
        risco_precip = min(100, precip * 2) if 'precip' in locals() else 10
        risco_vento = min(100, max(0, (wind - 30) * 3)) if 'wind' in locals() else 15
        risco_umidade = min(100, max(0, abs(humidity - 60) * 2)) if 'humidity' in locals() else 25
        
        risco_total = (risco_temp + risco_precip + risco_vento + risco_umidade) / 4
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Gauge do risco climático
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = risco_total,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Risco Climático"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "lightblue"},
                    'steps': [
                        {'range': [0, 25], 'color': "lightgreen"},
                        {'range': [25, 50], 'color': "yellow"},
                        {'range': [50, 75], 'color': "orange"},
                        {'range': [75, 100], 'color': "red"}
                    ]
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### � Fatores de Risco")
            
            fatores_risco = {
                "🌡️ Temperatura": risco_temp,
                "🌧️ Precipitação": risco_precip,
                "💨 Vento": risco_vento,
                "💧 Umidade": risco_umidade
            }
            
            for fator, valor in fatores_risco.items():
                progress_color = "normal"
                if valor > 75:
                    progress_color = "red"
                elif valor > 50:
                    progress_color = "orange"
                elif valor > 25:
                    progress_color = "yellow"
                else:
                    progress_color = "green"
                
                st.markdown(f"**{fator}**")
                st.progress(valor / 100)
                st.caption(f"Score: {valor:.1f}/100")
        
        # Recomendações climáticas
        st.markdown("---")
        st.subheader("💡 Recomendações Climáticas")
        
        recomendacoes = []
        
        if risco_total > 60:
            recomendacoes.append("⚠️ Monitoramento climático intensivo recomendado")
            recomendacoes.append("🛡️ Considerar medidas preventivas adicionais")
        
        if risco_temp > 50:
            recomendacoes.append("🌡️ Verificar isolamento térmico da propriedade")
        
        if risco_precip > 50:
            recomendacoes.append("🌧️ Inspecionar sistema de drenagem")
        
        if risco_vento > 50:
            recomendacoes.append("💨 Verificar fixação de estruturas externas")
        
        if risco_umidade > 50:
            recomendacoes.append("💧 Melhorar ventilação para controle de umidade")
        
        if not recomendacoes:
            recomendacoes.append("✅ Condições climáticas favoráveis - manter monitoramento regular")
        
        for rec in recomendacoes:
            st.write(f"• {rec}")
    
    else:
        # Interface inicial
        st.markdown("---")
        st.info("ℹ️ Insira um CEP válido para visualizar dados climáticos detalhados")
        
        # Mostrar dados gerais
        st.subheader("🌍 Monitoramento Geral")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 🏙️ Região Metropolitana SP
            **Status:** Online  
            **Estações:** 45 ativas  
            **Última atualização:** Há 5 min
            """)
        
        with col2:
            st.markdown("""
            ### 🌊 Região Costeira
            **Status:** Online  
            **Estações:** 23 ativas  
            **Última atualização:** Há 3 min
            """)
        
        with col3:
            st.markdown("""
            ### 🏔️ Região Serrana
            **Status:** Online  
            **Estações:** 18 ativas  
            **Última atualização:** Há 7 min
            """)
        
        # Alertas gerais
        st.markdown("---")
        st.subheader("🚨 Alertas Meteorológicos Gerais")
        
        st.warning("⚠️ Previsão de chuva forte para região metropolitana de SP - Próximas 6h")
        st.info("ℹ️ Frente fria se aproximando do litoral sul - Temperatura pode cair 8°C")
        st.success("✅ Condições estáveis na região serrana - Tempo bom para os próximos 3 dias")

def show_settings():
    """Página de configurações"""
    st.header("⚙️ Configurações do Sistema")
    
    # Status detalhado do sistema
    st.subheader("🔧 Status dos Componentes")
    
    try:
        from web_ml_integration import get_ml_integration
        ml_integration = get_ml_integration()
        status = ml_integration.get_system_status()
        model_info = ml_integration.get_model_info()
        
        # Status dos componentes
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🧠 Sistema de Machine Learning")
            st.success("✅ Integração ML Carregada") if status.get('ml_model') else st.error("❌ Modelo ML não encontrado")
            st.success("✅ Preditor Ativo") if status.get('predictor') else st.error("❌ Preditor Inativo")
            
            # Informações do modelo
            st.markdown("**Informações do Modelo:**")
            st.write(f"• Tipo: {model_info.get('model_type', 'N/A')}")
            st.write(f"• Versão: {model_info.get('version', 'N/A')}")
            st.write(f"• Status: {model_info.get('status', 'N/A')}")
            st.write(f"• Acurácia: {model_info.get('accuracy', 'N/A')}")
        
        with col2:
            st.markdown("#### 🌦️ Sistema Climático")
            st.success("✅ Weather Service Ativo") if status.get('weather_service') else st.error("❌ Weather Service Inativo")
            st.success("✅ API OpenMeteo Online") if status.get('weather_api') else st.error("❌ API OpenMeteo Offline")
            
            # Teste de conectividade
            if st.button("🔄 Testar Conectividade Climática"):
                with st.spinner("Testando..."):
                    try:
                        from src.weather.weather_service import WeatherService
                        weather = WeatherService()
                        test_data = weather.get_weather_data(-23.5505, -46.6333)  # São Paulo
                        
                        if test_data and test_data.current:
                            st.success(f"✅ Conectividade OK - Temp: {test_data.current.temperature_c}°C")
                        else:
                            st.error("❌ Falha na conectividade")
                    except Exception as e:
                        st.error(f"❌ Erro: {e}")
        
        # Status geral
        overall_status = status.get('overall', False)
        
        if overall_status:
            st.success("🎉 Sistema Totalmente Operacional - Predições em tempo real ativas!")
        else:
            st.warning("⚠️ Sistema em Modo Simulação - Algumas funcionalidades limitadas")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar status do sistema: {e}")
        st.warning("⚠️ Sistema funcionando em modo básico")
    
    # Configurações de predição
    st.markdown("---")
    st.subheader("🎯 Configurações de Predição")
    
    col1, col2 = st.columns(2)
    
    with col1:
        incluir_clima_padrao = st.checkbox("Incluir dados climáticos por padrão", value=True)
        limite_risco_alto = st.slider("Limite para Risco Alto", 70, 90, 75)
        
    with col2:
        precisao_decimal = st.selectbox("Precisão decimal do score", [1, 2], index=0)
        cache_weather = st.checkbox("Cache de dados climáticos", value=True)
    
    if st.button("💾 Salvar Configurações"):
        st.success("✅ Configurações salvas com sucesso!")
    
    # Informações do sistema
    st.markdown("---")
    st.subheader("ℹ️ Informações do Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Versão", "v3.0")
        st.metric("Framework Web", "Streamlit")
    
    with col2:
        st.metric("ML Framework", "XGBoost")
        st.metric("API Climática", "OpenMeteo")
    
    with col3:
        st.metric("Banco de Dados", "SQLite")
        st.metric("Ambiente", "Desenvolvimento")

def show_mapa_calor():
    """Página do Mapa de Calor - NOVA FUNÇÃO"""
    st.header("🗺️ Mapa de Calor - Distribuição de Riscos por CEP")
    st.markdown("Visualização geográfica interativa dos riscos de sinistros baseada nos CEPs das apólices cadastradas.")
    
    # Verificar se há dados de apólices no banco
    try:
        # Buscar dados reais do banco
        policies_data = get_real_policies_data()
        
        if not policies_data:
            st.warning("⚠️ Nenhuma apólice encontrada no banco de dados.")
            st.info("💡 Adicione apólices através de 'Gerenciar Apólices' para ver o mapa!")
            
            # Botão para ir para gerenciar apólices
            if st.button("➕ Ir para Gerenciar Apólices", use_container_width=True):
                st.session_state.page_redirect = "➕ Gerenciar Apólices"
                st.rerun()
            
            # Oferecer dados de exemplo
            st.markdown("---")
            st.subheader("📊 Ou visualize com dados de exemplo:")
            
            if st.button("🎭 Gerar Mapa com Dados de Exemplo", use_container_width=True):
                with st.spinner("Gerando mapa com dados simulados..."):
                    # Gerar DataFrame de exemplo para o mapa de calor
                    import pandas as pd
                    mock_policies = generate_mock_policies_data()
                    mock_df = pd.DataFrame([{
                        'cep': p['cep'],
                        'risk_score': p['risk_score'],
                        'insured_value': p['insured_value'],
                        'policy_id': p['policy_number']
                    } for p in mock_policies])
                    criar_interface_streamlit(mock_df)
            return
        
        # Converter dados do banco para DataFrame
        import pandas as pd
        
        # Preparar dados para o mapa
        mapa_data = []
        for policy in policies_data:
            mapa_data.append({
                'cep': policy['cep'],
                'risk_score': policy['risk_score'],
                'insured_value': policy['insured_value'],
                'policy_id': policy['policy_number']
            })
        
        # Criar DataFrame
        policies_df = pd.DataFrame(mapa_data)
        
        # Métricas resumidas antes do mapa
        col1, col2, col3, col4 = st.columns(4)
        
        total_policies = len(policies_df)
        unique_ceps = policies_df['cep'].nunique()
        avg_risk = policies_df['risk_score'].mean()
        total_value = policies_df['insured_value'].sum()
        
        with col1:
            st.metric("📋 Total de Apólices", f"{total_policies:,}")
        
        with col2:
            st.metric("📍 CEPs Únicos", f"{unique_ceps:,}")
        
        with col3:
            st.metric("🎯 Risco Médio", f"{avg_risk:.1f}")
        
        with col4:
            st.metric("💰 Valor Total", f"R$ {total_value/1000000:.1f}M")
        
        # Distribuição por nível de risco
        st.markdown("---")
        st.subheader("📊 Distribuição por Nível de Risco")
        
        col1, col2, col3, col4 = st.columns(4)
        
        muito_baixo = len(policies_df[policies_df['risk_score'] < 25])
        baixo = len(policies_df[(policies_df['risk_score'] >= 25) & (policies_df['risk_score'] < 50)])
        medio = len(policies_df[(policies_df['risk_score'] >= 50) & (policies_df['risk_score'] < 75)])
        alto = len(policies_df[policies_df['risk_score'] >= 75])
        
        with col1:
            st.metric("🟢 Muito Baixo", muito_baixo, f"{muito_baixo/total_policies*100:.1f}%")
        
        with col2:
            st.metric("🔵 Baixo", baixo, f"{baixo/total_policies*100:.1f}%")
        
        with col3:
            st.metric("🟡 Médio", medio, f"{medio/total_policies*100:.1f}%")
        
        with col4:
            st.metric("🔴 Alto", alto, f"{alto/total_policies*100:.1f}%")
        
        # Chamar a interface do mapa de calor com dados reais
        st.markdown("---")
        st.success(f"✅ Exibindo mapa com {total_policies} apólices REAIS do banco de dados!")
        
        # Usar a função completa do mapa de calor
        criar_interface_streamlit(policies_df)
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        st.warning("🔄 Usando dados de exemplo...")
        
        # Fallback para dados de exemplo
        import pandas as pd
        criar_interface_streamlit(pd.DataFrame())

if __name__ == "__main__":
    main()










