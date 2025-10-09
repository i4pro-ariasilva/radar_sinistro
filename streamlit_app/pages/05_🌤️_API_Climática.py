"""
Análise Climática - Sistema de Radar de Risco Climático
Interface para demonstração e configuração da API climática
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import time

# Configuração da página
st.set_page_config(
    page_title="API Climática - Radar Climático",
    page_icon="🌤️",
    layout="wide"
)

# Adicionar path do projeto
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

def configure_api_key():
    """Interface para configurar chave da API"""
    
    st.markdown("## 🔑 Configuração da API")
    
    with st.expander("📋 Como obter sua chave da API", expanded=False):
        st.markdown("""
        **Passos para obter chave gratuita:**
        
        1. 🌐 Acesse: https://www.weatherapi.com
        2. 📝 Crie uma conta gratuita
        3. ✅ Confirme seu email
        4. 🔑 Acesse o painel e copie sua API Key
        5. 📋 Cole a chave abaixo
        
        **Limites da conta gratuita:**
        - 1.000.000 calls/mês
        - Dados atuais + previsão 3 dias
        - Histórico últimos 7 dias
        """)
    
    # Input para chave da API
    api_key = st.text_input(
        "🔑 Cole sua chave da WeatherAPI aqui:",
        type="password",
        help="Sua chave será salva no arquivo .env"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Salvar Chave", use_container_width=True, type="primary"):
            if api_key and api_key.strip():
                try:
                    # Usar função segura para atualizar .env
                    from src.utils import update_env_variable, create_env_template
                    
                    env_file = ROOT_DIR / '.env'
                    
                    # Criar template se arquivo não existir
                    if not env_file.exists():
                        create_env_template(env_file)
                    
                    # Atualizar chave usando função segura
                    if update_env_variable(env_file, 'WEATHERAPI_KEY', api_key.strip()):
                        st.success("✅ Chave salva com sucesso!")
                        st.info("🔄 Reinicie a aplicação para carregar a nova chave")
                        
                        # Limpar cache do Streamlit para forçar reload
                        if hasattr(st, 'cache_data'):
                            st.cache_data.clear()
                        
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar chave no arquivo .env")
                    
                except Exception as e:
                    st.error(f"❌ Erro ao salvar chave: {str(e)}")
                    
                    # Oferecer método manual como fallback
                    with st.expander("🔧 Configuração Manual (Fallback)"):
                        st.markdown("**Se o erro persistir, configure manualmente:**")
                        st.code(f"WEATHERAPI_KEY={api_key.strip()}", language="bash")
                        st.markdown("1. Abra o arquivo `.env` na raiz do projeto")
                        st.markdown("2. Adicione ou atualize a linha acima")
                        st.markdown("3. Salve o arquivo")
                        st.markdown("4. Reinicie a aplicação")
            else:
                st.warning("⚠️ Por favor, insira uma chave válida")
    
    with col2:
        if st.button("🧪 Testar Conexão", use_container_width=True):
            if api_key and api_key.strip():
                with st.spinner("Testando conexão..."):
                    try:
                        from src.weather import WeatherClient
                        
                        client = WeatherClient(api_key.strip())
                        
                        if client.test_connection():
                            st.success("✅ Conexão funcionando!")
                            
                            # Teste rápido
                            weather = client.get_current_weather("São Paulo, Brazil")
                            if weather:
                                st.info(f"🌡️ Teste: São Paulo está com {weather.temperature_c}°C")
                        else:
                            st.error("❌ Erro na conexão. Verifique a chave.")
                            
                    except Exception as e:
                        st.error(f"❌ Erro: {str(e)}")
            else:
                st.warning("⚠️ Por favor, insira uma chave para testar")

def check_api_status():
    """Verificar status da API configurada"""
    
    try:
        from config.settings import API_CONFIG
        from src.weather import WeatherClient
        
        api_key = API_CONFIG['weather']['weatherapi_key']
        
        if not api_key or api_key == 'your_weatherapi_key_here':
            return False, "Chave não configurada"
        
        client = WeatherClient(api_key)
        
        if client.test_connection():
            return True, "API funcionando"
        else:
            return False, "Erro na conexão"
            
    except Exception as e:
        return False, f"Erro: {str(e)}"

def demo_weather_data():
    """Demonstração de dados climáticos"""
    
    st.markdown("## 🌦️ Demonstração de Dados Climáticos")
    
    # Verificar se API está configurada
    api_working, status_msg = check_api_status()
    
    if not api_working:
        st.error(f"❌ API não configurada: {status_msg}")
        st.info("💡 Configure sua chave da API na seção acima primeiro.")
        return
    
    st.success(f"✅ API funcionando: {status_msg}")
    
    # Interface para busca
    col1, col2 = st.columns([2, 1])
    
    with col1:
        location_type = st.selectbox(
            "🔍 Tipo de busca:",
            ["Cidade", "CEP", "Coordenadas"]
        )
    
    with col2:
        if st.button("🎲 Exemplo Aleatório", use_container_width=True):
            import random
            examples = {
                "Cidade": ["São Paulo, Brazil", "Rio de Janeiro, Brazil", "Belo Horizonte, Brazil"],
                "CEP": ["01310-100", "04038-001", "22071-900"],
                "Coordenadas": ["-23.5505,-46.6333", "-22.9068,-43.1729", "-19.9208,-43.9378"]
            }
            st.session_state.example_location = random.choice(examples[location_type])
    
    # Input baseado no tipo
    if location_type == "Cidade":
        location = st.text_input(
            "🏙️ Digite o nome da cidade:",
            value=st.session_state.get('example_location', ''),
            placeholder="Ex: São Paulo, Brazil"
        )
    elif location_type == "CEP":
        location = st.text_input(
            "📮 Digite o CEP:",
            value=st.session_state.get('example_location', ''),
            placeholder="Ex: 01310-100"
        )
    else:  # Coordenadas
        location = st.text_input(
            "🗺️ Digite as coordenadas (lat,lon):",
            value=st.session_state.get('example_location', ''),
            placeholder="Ex: -23.5505,-46.6333"
        )
    
    if st.button("🔍 Buscar Dados Climáticos", type="primary", use_container_width=True):
        if location:
            with st.spinner(f"Obtendo dados para {location}..."):
                try:
                    from src.weather import WeatherClient
                    from config.settings import API_CONFIG
                    
                    api_key = API_CONFIG['weather']['weatherapi_key']
                    client = WeatherClient(api_key)
                    
                    # Buscar dados baseado no tipo
                    if location_type == "CEP":
                        weather = client.get_weather_by_cep(location)
                    elif location_type == "Coordenadas":
                        lat, lon = map(float, location.split(','))
                        weather = client.get_weather_by_coordinates(lat, lon)
                    else:
                        weather = client.get_current_weather(location)
                    
                    if weather:
                        # Mostrar dados em cards
                        st.markdown("### 📊 Dados Climáticos Obtidos")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            risk_level = weather.get_risk_level()
                            risk_color = {
                                "Baixo": "🟢",
                                "Médio": "🟡", 
                                "Alto": "🟠",
                                "Crítico": "🔴"
                            }.get(risk_level, "⚪")
                            
                            st.metric(
                                f"{weather.get_condition_emoji()} Condição",
                                weather.condition,
                                delta=f"{risk_color} Risco {risk_level}"
                            )
                        
                        with col2:
                            st.metric(
                                "🌡️ Temperatura",
                                f"{weather.temperature_c}°C",
                                delta=f"Sensação: {weather.feels_like_c}°C"
                            )
                        
                        with col3:
                            st.metric(
                                "💧 Umidade",
                                f"{weather.humidity_percent}%",
                                delta=f"Pressão: {weather.pressure_mb} mb"
                            )
                        
                        with col4:
                            st.metric(
                                "💨 Vento",
                                f"{weather.wind_speed_kph} km/h",
                                delta=f"Direção: {weather.wind_direction}"
                            )
                        
                        # Informações detalhadas
                        with st.expander("📋 Informações Detalhadas"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**📍 Localização:**")
                                st.write(f"• **Local:** {weather.location}")
                                st.write(f"• **Latitude:** {weather.latitude}")
                                st.write(f"• **Longitude:** {weather.longitude}")
                                st.write(f"• **Horário:** {'Dia' if weather.is_day else 'Noite'}")
                                
                                st.markdown("**🌦️ Condições:**")
                                st.write(f"• **Condição:** {weather.condition}")
                                st.write(f"• **Código:** {weather.condition_code}")
                                st.write(f"• **Precipitação:** {weather.precipitation_mm} mm")
                                st.write(f"• **Visibilidade:** {weather.visibility_km} km")
                                st.write(f"• **UV:** {weather.uv_index}")
                            
                            with col2:
                                st.markdown("**🌡️ Temperatura:**")
                                st.write(f"• **Atual:** {weather.temperature_c}°C ({weather.temperature_f}°F)")
                                st.write(f"• **Sensação:** {weather.feels_like_c}°C")
                                if weather.heat_index_c:
                                    st.write(f"• **Índice de calor:** {weather.heat_index_c}°C")
                                if weather.wind_chill_c:
                                    st.write(f"• **Sensação térmica:** {weather.wind_chill_c}°C")
                                
                                st.markdown("**💨 Vento:**")
                                st.write(f"• **Velocidade:** {weather.wind_speed_kph} km/h")
                                st.write(f"• **Direção:** {weather.wind_direction} ({weather.wind_degree}°)")
                                if weather.gust_kph:
                                    st.write(f"• **Rajadas:** {weather.gust_kph} km/h")
                        
                        # Análise de risco
                        st.markdown("### ⚠️ Análise de Risco Climático")
                        
                        risk_score = weather.get_risk_score()
                        risk_percent = risk_score * 100
                        
                        # Gauge de risco
                        fig_gauge = go.Figure(go.Indicator(
                            mode = "gauge+number+delta",
                            value = risk_percent,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': "Score de Risco (%)"},
                            delta = {'reference': 50},
                            gauge = {
                                'axis': {'range': [None, 100]},
                                'bar': {'color': "darkblue"},
                                'steps': [
                                    {'range': [0, 25], 'color': "lightgreen"},
                                    {'range': [25, 50], 'color': "yellow"},
                                    {'range': [50, 75], 'color': "orange"},
                                    {'range': [75, 100], 'color': "red"}],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': 75}
                            }
                        ))
                        
                        fig_gauge.update_layout(height=300)
                        st.plotly_chart(fig_gauge, use_container_width=True)
                        
                        # Fatores de risco
                        st.markdown("#### 🔍 Fatores que Influenciam o Risco:")
                        
                        factors = []
                        
                        if weather.temperature_c < 0 or weather.temperature_c > 40:
                            factors.append("🌡️ Temperatura extrema")
                        
                        if weather.precipitation_mm > 20:
                            factors.append(f"🌧️ Precipitação alta ({weather.precipitation_mm} mm)")
                        
                        if weather.wind_speed_kph > 30:
                            factors.append(f"💨 Vento forte ({weather.wind_speed_kph} km/h)")
                        
                        if weather.humidity_percent > 90:
                            factors.append(f"💧 Umidade muito alta ({weather.humidity_percent}%)")
                        
                        if weather.pressure_mb < 1000:
                            factors.append(f"📉 Pressão baixa ({weather.pressure_mb} mb)")
                        
                        if weather.uv_index > 8:
                            factors.append(f"☀️ UV alto ({weather.uv_index})")
                        
                        if factors:
                            for factor in factors:
                                st.warning(f"⚠️ {factor}")
                        else:
                            st.success("✅ Condições climáticas normais - baixo risco")
                        
                        # Dados brutos (JSON)
                        with st.expander("🔧 Dados Brutos (JSON)"):
                            st.json(weather.to_dict())
                    
                    else:
                        st.error("❌ Não foi possível obter dados para esta localização")
                        st.info("💡 Verifique se a localização está correta")
                
                except Exception as e:
                    st.error(f"❌ Erro ao buscar dados: {str(e)}")
        else:
            st.warning("⚠️ Por favor, insira uma localização")

def demo_multiple_locations():
    """Demonstração com múltiplas localizações"""
    
    st.markdown("## 🌍 Análise Comparativa de Múltiplas Localizações")
    
    # Verificar API
    api_working, _ = check_api_status()
    
    if not api_working:
        st.warning("⚠️ Configure a API primeiro para usar esta funcionalidade")
        return
    
    # Localizações pré-definidas
    preset_locations = {
        "Capitais Brasileiras": [
            "São Paulo, Brazil",
            "Rio de Janeiro, Brazil", 
            "Brasília, Brazil",
            "Salvador, Brazil",
            "Belo Horizonte, Brazil"
        ],
        "Regiões Metropolitanas": [
            "São Paulo, Brazil",
            "Campinas, Brazil",
            "Santos, Brazil",
            "São José dos Campos, Brazil"
        ],
        "CEPs de São Paulo": [
            "01310-100",  # Centro
            "04038-001",  # Vila Olímpia
            "05508-900",  # Butantã
            "08260-001"   # Itaquera
        ]
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        preset = st.selectbox("📋 Escolha um conjunto pré-definido:", list(preset_locations.keys()))
    
    with col2:
        if st.button("🔄 Carregar Localizações", use_container_width=True):
            st.session_state.locations = preset_locations[preset]
    
    # Editor de localizações
    locations_text = st.text_area(
        "🗺️ Localizações (uma por linha):",
        value='\n'.join(st.session_state.get('locations', preset_locations[preset])),
        height=100,
        help="Digite uma localização por linha. Pode ser cidade, CEP ou coordenadas."
    )
    
    locations = [loc.strip() for loc in locations_text.split('\n') if loc.strip()]
    
    if st.button("🌦️ Obter Dados Climáticos", type="primary", use_container_width=True):
        if locations:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            weather_data = []
            
            try:
                from src.weather import WeatherClient
                from config.settings import API_CONFIG
                
                api_key = API_CONFIG['weather']['weatherapi_key']
                client = WeatherClient(api_key)
                
                for i, location in enumerate(locations):
                    status_text.text(f"Obtendo dados para: {location}")
                    progress_bar.progress((i + 1) / len(locations))
                    
                    # Determinar tipo de busca
                    if location.count(',') == 1 and all(part.replace('.', '').replace('-', '').isdigit() for part in location.split(',')):
                        # Coordenadas
                        lat, lon = map(float, location.split(','))
                        weather = client.get_weather_by_coordinates(lat, lon)
                    elif '-' in location and location.replace('-', '').isdigit():
                        # CEP
                        weather = client.get_weather_by_cep(location)
                    else:
                        # Cidade
                        weather = client.get_current_weather(location)
                    
                    if weather:
                        weather_data.append({
                            'location': location,
                            'weather': weather
                        })
                
                status_text.text("✅ Dados obtidos com sucesso!")
                progress_bar.progress(1.0)
                
                if weather_data:
                    # Criar DataFrame para análise
                    df_data = []
                    
                    for item in weather_data:
                        weather = item['weather']
                        df_data.append({
                            'Localização': item['location'],
                            'Temperatura (°C)': weather.temperature_c,
                            'Sensação (°C)': weather.feels_like_c,
                            'Umidade (%)': weather.humidity_percent,
                            'Vento (km/h)': weather.wind_speed_kph,
                            'Precipitação (mm)': weather.precipitation_mm,
                            'Pressão (mb)': weather.pressure_mb,
                            'UV': weather.uv_index,
                            'Condição': weather.condition,
                            'Risco (%)': round(weather.get_risk_score() * 100, 1),
                            'Nível de Risco': weather.get_risk_level()
                        })
                    
                    df = pd.DataFrame(df_data)
                    
                    # Mostrar tabela
                    st.markdown("### 📊 Resumo Comparativo")
                    st.dataframe(df, use_container_width=True)
                    
                    # Gráficos comparativos
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Gráfico de temperatura
                        fig_temp = px.bar(
                            df,
                            x='Localização',
                            y='Temperatura (°C)',
                            color='Risco (%)',
                            title="🌡️ Temperatura por Localização",
                            color_continuous_scale='RdYlBu_r'
                        )
                        fig_temp.update_xaxes(tickangle=45)
                        st.plotly_chart(fig_temp, use_container_width=True)
                    
                    with col2:
                        # Gráfico de risco
                        fig_risk = px.scatter(
                            df,
                            x='Umidade (%)',
                            y='Vento (km/h)',
                            size='Risco (%)',
                            color='Nível de Risco',
                            hover_data=['Localização', 'Temperatura (°C)'],
                            title="⚠️ Análise de Risco: Umidade vs Vento",
                            color_discrete_map={
                                'Baixo': '#00cc66',
                                'Médio': '#ffa421',
                                'Alto': '#ff7f0e',
                                'Crítico': '#ff4b4b'
                            }
                        )
                        st.plotly_chart(fig_risk, use_container_width=True)
                    
                    # Ranking de risco
                    st.markdown("### 🏆 Ranking por Nível de Risco")
                    
                    df_sorted = df.sort_values('Risco (%)', ascending=False)
                    
                    for i, row in df_sorted.iterrows():
                        risk_emoji = {
                            'Baixo': '🟢',
                            'Médio': '🟡',
                            'Alto': '🟠',
                            'Crítico': '🔴'
                        }.get(row['Nível de Risco'], '⚪')
                        
                        st.markdown(f"""
                        **{risk_emoji} {row['Localização']}** - {row['Nível de Risco']} ({row['Risco (%)']}%)
                        - 🌡️ {row['Temperatura (°C)']}°C, 💧 {row['Umidade (%)']}%, 💨 {row['Vento (km/h)']} km/h
                        - 🌤️ {row['Condição']}
                        """)
                
                else:
                    st.error("❌ Não foi possível obter dados para nenhuma localização")
            
            except Exception as e:
                st.error(f"❌ Erro na análise: {str(e)}")
        
        else:
            st.warning("⚠️ Por favor, insira pelo menos uma localização")

def main():
    """Função principal da página"""
    
    st.title("🌤️ API Climática - WeatherAPI.com")
    st.markdown("Interface para configuração e demonstração da integração climática")
    
    # Sidebar com informações
    with st.sidebar:
        st.markdown("### 🌦️ WeatherAPI.com")
        st.info("""
        **Funcionalidades:**
        • Dados climáticos em tempo real
        • Busca por cidade, CEP ou coordenadas
        • Cache inteligente (1 hora)
        • Análise de risco automática
        • Múltiplas localizações
        """)
        
        st.markdown("### 📊 Dados Disponíveis")
        st.markdown("""
        • 🌡️ Temperatura atual e sensação
        • 💧 Umidade relativa
        • 💨 Vento (velocidade e direção)
        • 🌧️ Precipitação
        • 📊 Pressão atmosférica
        • ☀️ Índice UV
        • 🌤️ Condições climáticas
        • ⚠️ Score de risco calculado
        """)
        
        # Status da API
        api_working, status_msg = check_api_status()
        
        if api_working:
            st.success(f"✅ API: {status_msg}")
        else:
            st.error(f"❌ API: {status_msg}")
    
    # Tabs principais
    tab1, tab2, tab3 = st.tabs(["🔑 Configuração", "🔍 Busca Individual", "🌍 Análise Comparativa"])
    
    with tab1:
        configure_api_key()
    
    with tab2:
        demo_weather_data()
    
    with tab3:
        demo_multiple_locations()
    
    # Footer com cache info
    st.markdown("---")
    
    try:
        from src.weather import WeatherCache
        cache = WeatherCache()
        cache_info = cache.get_cache_info()
        
        if cache_info.get('total_files', 0) > 0:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💾 Arquivos em Cache", cache_info.get('total_files', 0))
            
            with col2:
                st.metric("📁 Tamanho do Cache", f"{cache_info.get('total_size_mb', 0)} MB")
            
            with col3:
                if st.button("🧹 Limpar Cache"):
                    removed = cache.clear()
                    st.success(f"✅ {removed} arquivos removidos do cache")
                    st.rerun()
    
    except:
        pass

if __name__ == "__main__":
    main()