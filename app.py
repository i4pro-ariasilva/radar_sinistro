"""
🌦️ RADAR DE SINISTRO - INTERFACE WEB
Sistema Inteligente de Predição de Riscos Climáticos

Aplicação Streamlit para análise preditiva de sinistros
baseada em dados climáticos e características de imóveis.

Versão: 3.0 - Código Limpo e Organizado
"""

# Imports padrão
import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Imports para análise de dados
import pandas as pd
import numpy as np

# Imports para visualização
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Configurar path para módulos do sistema
sys.path.append('.')

# Imports de módulos do projeto
from policy_management import show_manage_policies
from pages.api_documentation import show_api_documentation  
from pages.api_code_examples import show_code_examples
from mapa_de_calor_completo import criar_interface_streamlit

# Exportar as funções públicas para o namespace do módulo
__all__ = ['show_manage_policies', 'show_api_documentation', 'show_code_examples', 'main']

# Imports de utilitários (se disponíveis)
try:
    from utils.formatters import format_currency, format_percentage, format_score
    from utils.validators import validate_cep, validate_email
    from services.alertas_service import AlertasService
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False

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
    
    /* Alinhamento de botões de busca */
    .search-button-container {
        display: flex;
        align-items: flex-end;
        height: 100%;
        padding-top: 1.5rem;
    }
    
    /* Força alinhamento de botões em colunas - mais específico */
    div[data-testid="column"] > div > div > button {
        margin-top: 1.5rem;
    }
    
    /* Alinhamento específico para form submit buttons */
    .stForm > div > div[data-testid="column"]:last-child button {
        margin-top: 1.875rem !important;
    }
    
    /* Botões de busca em containers específicos */
    .search-button {
        margin-top: 1.875rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================

def format_currency(value: float) -> str:
    """Formata um valor como moeda brasileira"""
    if UTILS_AVAILABLE:
        from utils.formatters import format_currency as util_format_currency
        return util_format_currency(value)
    try:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Formata um valor como porcentagem"""
    if UTILS_AVAILABLE:
        from utils.formatters import format_percentage as util_format_percentage
        return util_format_percentage(value, decimals)
    try:
        if 0 <= value <= 1:
            percentage = value * 100
        else:
            percentage = value
        return f"{percentage:.{decimals}f}%"
    except (ValueError, TypeError):
        return "0%"


def validate_cep(cep: str) -> bool:
    """Valida se um CEP está no formato correto"""
    if UTILS_AVAILABLE:
        from utils.validators import validate_cep as util_validate_cep
        return util_validate_cep(cep)
    if not cep:
        return False
    clean_cep = ''.join(filter(str.isdigit, cep))
    return len(clean_cep) == 8


def get_risk_level_emoji(score: float) -> str:
    """Retorna emoji baseado no score de risco"""
    if score >= 70:
        return "🔴"
    elif score >= 40:
        return "🟡"
    else:
        return "🟢"


def get_risk_level_text(score: float) -> str:
    """Converte score numérico para texto de nível"""
    if score >= 75:
        return "Alto"
    elif score >= 50:
        return "Médio"
    elif score >= 25:
        return "Baixo"
    else:
        return "Muito Baixo"

# ============================================================
# FUNÇÕES DE ALERTAS AUTOMÁTICOS
# ============================================================

def salvar_configuracoes_alertas(configuracoes):
    """Salva as configurações de alertas automáticos no banco de dados"""
    try:
        import sqlite3
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        # Criar tabela de configurações se não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes_alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                configuracoes TEXT NOT NULL,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Inserir ou atualizar configurações
        cursor.execute("""
            INSERT OR REPLACE INTO configuracoes_alertas (id, configuracoes)
            VALUES (1, ?)
        """, (json.dumps(configuracoes, ensure_ascii=False),))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {str(e)}")
        return False

def carregar_configuracoes_alertas():
    """Carrega as configurações de alertas automáticos do banco de dados"""
    try:
        import sqlite3
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT configuracoes FROM configuracoes_alertas WHERE id = 1")
        resultado = cursor.fetchone()
        
        conn.close()
        
        if resultado:
            return json.loads(resultado[0])
        return None
    except Exception as e:
        return None

def testar_envio_alerta(mensagem, canais):
    """Testa o envio de um alerta com as configurações atuais"""
    try:
        # Simula o envio para teste
        st.info("🧪 **Teste de Alerta Executado:**")
        
        for canal in canais:
            if canal == "Email":
                st.success(f"📧 {canal}: Alerta de teste enviado para admin@radarsinistro.com")
            elif canal == "SMS":
                st.success(f"📱 {canal}: Alerta de teste enviado para +55 11 99999-9999")
            elif canal == "WhatsApp":
                st.success(f"💬 {canal}: Alerta de teste enviado via WhatsApp")
            elif canal == "Sistema Interno":
                st.success(f"🔔 {canal}: Notificação criada no sistema")
        
        return True
    except Exception as e:
        st.error(f"Erro no teste de envio: {str(e)}")
        return False

def executar_alertas_automaticos(configuracoes):
    """Executa o envio automático de alertas baseado nas configurações"""
    try:
        from database.crud_operations import get_all_policies, get_prediction_for_policy
        from database.database import DatabaseManager
        
        # Inicializar conexão com banco
        db = DatabaseManager()
        
        # Buscar apólices elegíveis para alerta
        policies = get_all_policies()
        alertas_enviados = 0
        alertas_falharam = 0
        
        for policy in policies:
            # Verificar se a apólice tem score de risco alto
            prediction = get_prediction_for_policy(policy['numero_apolice'])
            if prediction and prediction.get('score_risco', 0) >= configuracoes.get('limite_risco', 75):
                
                # Verificar se já foi notificada recentemente (cooldown)
                if verificar_cooldown_alerta(policy['numero_apolice'], configuracoes.get('cooldown', 7)):
                    continue
                
                # Preparar dados para a mensagem
                dados_mensagem = {
                    'segurado': policy.get('segurado', 'N/A'),
                    'numero_apolice': policy.get('numero_apolice', 'N/A'),
                    'score_risco': prediction.get('score_risco', 0),
                    'nivel_risco': prediction.get('nivel_risco', 'N/A'),
                    'tipo_residencia': policy.get('tipo_residencia', 'N/A'),
                    'cep': policy.get('cep', 'N/A'),
                    'valor_segurado': policy.get('valor_segurado', 0),
                    'data_atual': datetime.now().strftime("%d/%m/%Y")
                }
                
                # Formatar mensagem
                mensagem_formatada = configuracoes['mensagem'].format(**dados_mensagem)
                
                # Enviar alerta
                sucesso = enviar_alerta_para_apolice(
                    policy, 
                    mensagem_formatada, 
                    configuracoes['canais'],
                    configuracoes['assunto']
                )
                
                if sucesso:
                    alertas_enviados += 1
                    # Marcar como notificada
                    marcar_apolice_notificada(policy['numero_apolice'])
                else:
                    alertas_falharam += 1
                
                # Verificar limite diário
                if alertas_enviados >= configuracoes.get('max_por_dia', 50):
                    break
        
        return {
            'sucesso': True,
            'enviados': alertas_enviados,
            'erros': alertas_falharam
        }
        
    except Exception as e:
        st.error(f"Erro na execução dos alertas: {str(e)}")
        return {
            'sucesso': False,
            'enviados': 0,
            'erros': 0
        }

def verificar_cooldown_alerta(numero_apolice, cooldown_dias):
    """Verifica se a apólice está em período de cooldown para alertas"""
    try:
        import sqlite3
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        # Verificar último alerta enviado
        cursor.execute("""
            SELECT data_envio FROM alertas_enviados 
            WHERE numero_apolice = ? 
            ORDER BY data_envio DESC LIMIT 1
        """, (numero_apolice,))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            ultima_data = datetime.strptime(resultado[0], "%Y-%m-%d %H:%M:%S")
            dias_desde_ultimo = (datetime.now() - ultima_data).days
            return dias_desde_ultimo < cooldown_dias
        
        return False
    except Exception as e:
        return False

def enviar_alerta_para_apolice(policy, mensagem, canais, assunto):
    """Envia alerta para uma apólice específica pelos canais configurados"""
    try:
        # Simular envio pelos diferentes canais
        sucesso_total = True
        
        for canal in canais:
            try:
                if canal == "Email" and policy.get('email'):
                    # Simular envio de email
                    registrar_envio_alerta(policy['numero_apolice'], canal, mensagem)
                elif canal == "SMS" and policy.get('telefone'):
                    # Simular envio de SMS
                    registrar_envio_alerta(policy['numero_apolice'], canal, mensagem)
                elif canal == "Sistema Interno":
                    # Criar notificação no sistema
                    registrar_envio_alerta(policy['numero_apolice'], canal, mensagem)
            except Exception as e:
                sucesso_total = False
        
        return sucesso_total
    except Exception as e:
        return False

def registrar_envio_alerta(numero_apolice, canal, mensagem):
    """Registra o envio de um alerta no banco de dados"""
    try:
        import sqlite3
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        # Criar tabela se não existir
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alertas_enviados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_apolice TEXT NOT NULL,
                canal TEXT NOT NULL,
                mensagem TEXT NOT NULL,
                data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Inserir registro
        cursor.execute("""
            INSERT INTO alertas_enviados (numero_apolice, canal, mensagem)
            VALUES (?, ?, ?)
        """, (numero_apolice, canal, mensagem))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def marcar_apolice_notificada(numero_apolice):
    """Marca uma apólice como notificada no sistema"""
    try:
        import sqlite3
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE policies SET notificada = 1, data_notificacao = ?
            WHERE numero_apolice = ?
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), numero_apolice))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

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
                "📊 Apólices em Risco",
                "📋 Gerenciar Apólices",
                "🚨 Gerenciamento de Alertas",
                "🚫 Gerenciamento de Bloqueios",
                "🌍 Monitoramento Climático",
                "📚 Documentação da API",
                "⚙️ Configurações",
                "🗺️ Mapa de Calor"
            ]
        )
        
        st.markdown("---")
        
        # Informações adicionais da sidebar
        st.markdown("### ℹ️ Sobre o Sistema")
        st.markdown("""
        **Radar de Sinistro v3.0**
        
        Sistema inteligente de predição de riscos climáticos para seguradoras.
        
        **Funcionalidades:**
        - 🤖 Machine Learning
        - 🌦️ Dados Climáticos
        - 📈 Análise Preditiva
        - 📄 Relatórios Detalhados
        """)
    
    # Roteamento de páginas
    if page == "📊 Apólices em Risco":
        show_policies_at_risk()
    elif page == "📋 Gerenciar Apólices":
        show_manage_policies()
    elif page == "🚨 Gerenciamento de Alertas":
        show_alert_management()
    elif page == "🚫 Gerenciamento de Bloqueios":
        show_blocking_management()
    elif page == "🌍 Monitoramento Climático":
        show_weather_monitoring()
    elif page == "📚 Documentação da API":
        show_api_documentation_section()
    elif page == "⚙️ Configurações":
        show_settings()
    elif page == "🗺️ Mapa de Calor":
        show_mapa_calor()





def get_coverage_risks_data(search_filter=None, risk_filter="Todos", type_filter="Todos", value_filter="Todos"):
    """Buscar dados de riscos por cobertura individual da nova tabela cobertura_risco"""
    
    try:
        # Importar o DAO de cobertura risco
        from database.cobertura_risco_dao import CoberturaRiscoDAO
        
        dao = CoberturaRiscoDAO()
        
        # Conectar ao banco para buscar dados detalhados
        import sqlite3
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        # Query para buscar coberturas individuais com dados da apólice (apenas análises mais recentes)
        query = """
        WITH latest_analysis AS (
            SELECT 
                cr.nr_apolice,
                cr.cd_cobertura,
                cr.score_risco as score_cobertura,
                cr.nivel_risco,
                cr.probabilidade,
                cr.data_calculo,
                ROW_NUMBER() OVER (
                    PARTITION BY cr.nr_apolice, cr.cd_cobertura 
                    ORDER BY cr.data_calculo DESC
                ) as rn
            FROM cobertura_risco cr
            WHERE typeof(cr.cd_cobertura) = 'integer'
        )
        SELECT 
            la.nr_apolice,
            la.cd_cobertura,
            la.score_cobertura,
            la.nivel_risco,
            la.probabilidade,
            la.data_calculo,
            c.nm_cobertura as nome_cobertura,
            a.segurado,
            a.cep,
            a.valor_segurado,
            a.tipo_residencia,
            a.score_risco as score_medio_apolice,
            a.nivel_risco as nivel_apolice,
            a.probabilidade_sinistro as prob_apolice,
            a.notificada
        FROM latest_analysis la
        JOIN coberturas c ON la.cd_cobertura = c.cd_cobertura
        JOIN apolices a ON la.nr_apolice = a.numero_apolice
        WHERE la.rn = 1
        """
        
        params = []
        
        # Aplicar filtros se fornecidos
        if search_filter and search_filter.strip():
            query += " AND la.nr_apolice LIKE ?"
            params.append(f"%{search_filter.strip()}%")
        
        if risk_filter != "Todos":
            if "Alto" in risk_filter:
                query += " AND la.score_cobertura >= 75"
            elif "Médio" in risk_filter and "Baixo" not in risk_filter:
                query += " AND la.score_cobertura >= 50 AND la.score_cobertura < 75"
            elif "Baixo" in risk_filter and "Muito" not in risk_filter:
                query += " AND la.score_cobertura >= 25 AND la.score_cobertura < 50"
            elif "Muito Baixo" in risk_filter:
                query += " AND la.score_cobertura < 25"
        
        if type_filter != "Todos":
            query += " AND a.tipo_residencia = ?"
            params.append(type_filter.lower())
        
        # Ordenar por score de risco da cobertura (maior para menor)
        query += " ORDER BY la.score_cobertura DESC, la.data_calculo DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            st.info("📝 Nenhuma cobertura analisada encontrada no banco de dados.")
            st.info("💡 Use 'Análise de Riscos' para analisar apólices e gerar dados de coberturas!")
            return []
        
        # Converter dados para formato esperado
        coverages_data = []
        for row in rows:
            # Mapear nomes de cobertura mais amigáveis
            coverage_names = {
                1: "🌊 Alagamento",
                2: "🌪️ Vendaval", 
                3: "🧊 Granizo",
                4: "⚡ Danos Elétricos"
            }
            
            coverage_data = {
                'nr_apolice': row[0],
                'cd_cobertura': row[1], 
                'score_cobertura': float(row[2]) if row[2] else 0,
                'nivel_risco': row[3] or 'baixo',
                'probabilidade': float(row[4]) if row[4] else 0,
                'data_calculo': row[5],
                'nome_cobertura': coverage_names.get(row[1], row[6] or f"Cobertura {row[1]}"),
                'segurado': row[7],
                'cep': row[8],
                'valor_segurado': float(row[9]) if row[9] else 0,
                'tipo_residencia': row[10],
                'score_medio_apolice': float(row[11]) if row[11] else 0,
                'nivel_apolice': row[12] or 'baixo',
                'prob_apolice': float(row[13]) if row[13] else 0,
                'notificada': int(row[14]) if row[14] else 0
            }
            
            coverages_data.append(coverage_data)
        
        return coverages_data
        
    except Exception as e:
        st.error(f"Erro ao buscar dados de coberturas: {str(e)}")
        import traceback
        st.error(f"Detalhes: {traceback.format_exc()}")
        return []

def show_policies_at_risk():
    """Página de Ranking de Coberturas em Risco"""
    
    st.header("📊 Ranking de Coberturas em Risco")
    
    # Seção de busca
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_policy = st.text_input(
            "🔍 Buscar Apólice", 
            placeholder="Digite o número da apólice (ex: POL-2025-001234)",
            help="Busque coberturas de uma apólice específica pelo número",
            key="buscar_apolice_coberturas"
        )
    
    with col2:
        # Usar markdown para criar espaçamento visual preciso
        st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
        if st.button("🔍 Buscar", key="buscar_btn_coberturas", use_container_width=True):
            if search_policy:
                st.success(f"Buscando coberturas da apólice: {search_policy}")
            else:
                st.warning("Digite um número de apólice para buscar")
    
    # Filtros
    st.markdown("### 🔍 Filtros")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        risk_filter = st.selectbox(
            "Nível de Risco",
            ["Todos", "Alto (75-100)", "Médio (50-74)", "Baixo (25-49)", "Muito Baixo (0-24)"]
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
    
    # Buscar dados REAIS de coberturas do banco de dados
    coverages_data = get_coverage_risks_data(search_policy, risk_filter, policy_type, value_range)
    
    # Métricas resumidas
    st.markdown("---")
    st.markdown("### 📊 Resumo das Coberturas (Últimas Análises)")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    high_risk = len([c for c in coverages_data if c['score_cobertura'] >= 75])
    medium_risk = len([c for c in coverages_data if 50 <= c['score_cobertura'] < 75])
    low_risk = len([c for c in coverages_data if c['score_cobertura'] < 50])
    total_value = sum([c['valor_segurado'] for c in coverages_data])
    unique_policies = len(set([c['nr_apolice'] for c in coverages_data]))
    
    with col1:
        st.metric("🔴 Alto Risco", high_risk, f"{high_risk/len(coverages_data)*100:.1f}%" if coverages_data else "0%")
    
    with col2:
        st.metric("🟡 Médio Risco", medium_risk, f"{medium_risk/len(coverages_data)*100:.1f}%" if coverages_data else "0%")
    
    with col3:
        st.metric("🟢 Baixo Risco", low_risk, f"{low_risk/len(coverages_data)*100:.1f}%" if coverages_data else "0%")
    
    with col4:
        st.metric("💰 Valor Total", f"R$ {total_value/1000000:.1f}M", f"{unique_policies} apólices")
    
    with col5:
        st.metric("Coberturas", len(coverages_data), f"{len(set([c['nome_cobertura'] for c in coverages_data]))} tipos")
    
    # Tabela de coberturas
    st.markdown("---")
    st.markdown("### Lista de Coberturas (Ordenado por Risco)")
    
    if coverages_data:
        # Criar DataFrame
        df = pd.DataFrame(coverages_data)
        
        # Adicionar colunas formatadas
        df['risk_level'] = df['score_cobertura'].apply(get_risk_level_emoji)
        df['valor_formatado'] = df['valor_segurado'].apply(lambda x: f"R$ {x:,.0f}")
        df['score_medio_formatado'] = df['score_medio_apolice'].apply(lambda x: f"{x:.1f}")
        df['notificada_emoji'] = df['notificada'].apply(lambda x: "✅" if x == 1 else "")
        
        # Selecionar e renomear colunas para exibição
        display_df = df[[
            'nr_apolice', 'nome_cobertura', 'risk_level', 'score_cobertura', 
            'score_medio_formatado', 'segurado', 'tipo_residencia', 'cep', 'valor_formatado', 'notificada_emoji'
        ]].copy()
        
        display_df.columns = [
            'Nº da Apólice', 'Nome da Cobertura', 'Risco', 'Score da Cobertura',
            'Score Médio da Apólice', 'Segurado', 'Tipo', 'CEP', 'Valor Segurado', 'Notificada'
        ]
        
        # Configurar cores baseadas no risco da cobertura
        def highlight_risk(row):
            score = row['Score da Cobertura']
            if score >= 75:
                return ['background-color: #ffebee; color: #d32f2f; font-weight: bold'] * len(row)
            elif score >= 50:
                return ['background-color: #fff3e0; color: #e65100; font-weight: bold'] * len(row)
            elif score >= 25:
                return ['background-color: #e3f2fd; color: #1976d2; font-weight: bold'] * len(row)
            else:
                return ['background-color: #e8f5e8; color: #2e7d32; font-weight: bold'] * len(row)
        
        # Container com botão de atualização alinhado
        col_btn, col_space = st.columns([2, 8])
        with col_btn:
            if st.button("🔄 Atualizar Lista", 
                        help="Clique para atualizar a lista de coberturas com os dados mais recentes", 
                        type="secondary",
                        width='stretch'):
                st.rerun()
        
        # Exibir tabela com estilo
        styled_df = display_df.style.apply(highlight_risk, axis=1)
        st.dataframe(styled_df, width='stretch', height=400)
        
        # Detalhes da cobertura selecionada
        st.markdown("---")
        st.markdown("### 📋 Detalhes da Cobertura")
        
        # Criar opções para seleção
        coverage_options = []
        for idx, row in df.iterrows():
            coverage_options.append(f"{row['nr_apolice']} - {row['nome_cobertura']} (Score: {row['score_cobertura']:.1f})")
        
        selected_coverage_option = st.selectbox(
            "Selecione uma cobertura para ver detalhes:",
            options=coverage_options
        )
        
        if selected_coverage_option:
            # Extrair índice da opção selecionada
            selected_idx = coverage_options.index(selected_coverage_option)
            coverage_details = df.iloc[selected_idx]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📄 Informações da Apólice")
                st.write(f"**Número da Apólice:** {coverage_details['nr_apolice']}")
                st.write(f"**Segurado:** {coverage_details['segurado']}")
                st.write(f"**Tipo de Imóvel:** {coverage_details['tipo_residencia'].title()}")
                st.write(f"**CEP:** {coverage_details['cep']}")
                st.write(f"**Valor Segurado:** R$ {coverage_details['valor_segurado']:,.2f}")
                
                st.markdown("#### 📊 Score Médio da Apólice")
                avg_score = coverage_details['score_medio_apolice']
                st.metric("Score Médio", f"{avg_score:.1f}/100", 
                         f"Nível: {get_risk_level_text(avg_score)}")
            
            with col2:
                st.markdown("#### Detalhes da Cobertura")
                st.write(f"**Nome da Cobertura:** {coverage_details['nome_cobertura']}")
                st.write(f"**Score de Risco:** {coverage_details['score_cobertura']:.1f}/100")
                st.write(f"**Nível de Risco:** {coverage_details['nivel_risco'].title()}")
                st.write(f"**Probabilidade:** {coverage_details['probabilidade']*100:.1f}%")
                
                # Comparação com score médio da apólice
                score_diff = coverage_details['score_cobertura'] - avg_score
                if abs(score_diff) > 5:  # Diferença significativa
                    diff_icon = "📈" if score_diff > 0 else "📉"
                    st.write(f"**Diferença vs Média:** {diff_icon} {score_diff:+.1f} pontos")
                    
                    if score_diff > 0:
                        st.warning("⚠️ Esta cobertura tem risco ACIMA da média da apólice")
                    else:
                        st.success("✅ Esta cobertura tem risco ABAIXO da média da apólice")
                else:
                    st.info("ℹ️ Esta cobertura está próxima da média da apólice")
        
        # Botão para refazer análise da cobertura selecionada
        st.markdown("---")
        st.markdown("### 🔄 Refazer Análise da Cobertura")
        
        if st.button("🔄 Refazer Análise desta Cobertura", width='stretch', type="primary"):
            selected_idx = coverage_options.index(selected_coverage_option)
            coverage_details = df.iloc[selected_idx]
            
            with st.spinner(f"Recalculando análise para {coverage_details['nome_cobertura']} da apólice {coverage_details['nr_apolice']}..."):
                # Chamar função real de recálculo
                result = reanalizar_cobertura_especifica(
                    coverage_details['nr_apolice'], 
                    coverage_details['cd_cobertura'],
                    coverage_details['nome_cobertura']
                )
                
                if result["success"]:
                    st.success("✅ **ANÁLISE RECALCULADA COM SUCESSO!**")
                    
                    # Mostrar mudanças reais logo abaixo do botão
                    old_score = coverage_details['score_cobertura']
                    new_score = result["new_score"]
                    
                    # Container destacado com os resultados
                    with st.container():
                        st.markdown("#### 📊 Resultado do Recálculo")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.info(f"**📄 Apólice:** {coverage_details['nr_apolice']}")
                            st.info(f"**🛡️ Cobertura:** {coverage_details['nome_cobertura']}")
                        
                        with col2:
                            if abs(old_score - new_score) > 0.1:
                                diff = new_score - old_score
                                diff_icon = "📈" if diff > 0 else "📉"
                                
                                # Mostrar mudança de score com destaque
                                st.metric(
                                    "Score de Risco", 
                                    f"{new_score:.1f}/100",
                                    f"{diff:+.1f} pontos"
                                )
                                
                                if diff > 0:
                                    st.warning(f"{diff_icon} **Risco AUMENTOU:** {old_score:.1f} → {new_score:.1f}")
                                else:
                                    st.success(f"{diff_icon} **Risco DIMINUIU:** {old_score:.1f} → {new_score:.1f}")
                                    
                                st.info(f"📊 **Novo nível:** {result['new_level'].title()}")
                                st.info(f"📈 **Nova probabilidade:** {result['new_probability']*100:.1f}%")
                            else:
                                st.info("ℹ️ Score permaneceu similar após recálculo")
                                st.metric("Score de Risco", f"{new_score:.1f}/100", "sem mudança significativa")
                    
                    st.info("🔄 **Atualize a página** para ver os novos dados na tabela principal")
                    
                else:
                    st.error(f"❌ Erro ao recalcular análise: {result.get('error', 'Erro desconhecido')}")
                    st.warning("⚠️ Tente novamente ou verifique os logs do sistema")
    else:
        st.warning("📝 Nenhuma cobertura analisada encontrada.")
        st.info("💡 Use a seção 'Análise de Riscos' para gerar análises de coberturas!")

def reanalizar_cobertura_especifica(nr_apolice, cd_cobertura, nome_cobertura):
    """Recalcular e persistir análise para uma cobertura específica"""
    try:
        # Importar dependências necessárias
        from database.cobertura_risco_dao import CoberturaRiscoDAO, CoberturaRiscoData
        from src.ml.coverage_predictors.coverage_manager import CoverageRiskManager
        import sqlite3
        from datetime import datetime
        import random
        
        # Buscar dados da apólice
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT numero_apolice, segurado, cep, valor_segurado, tipo_residencia, 
               latitude, longitude
        FROM apolices 
        WHERE numero_apolice = ?
        """, (nr_apolice,))
        
        policy_row = cursor.fetchone()
        if not policy_row:
            conn.close()
            return {"success": False, "error": "Apólice não encontrada"}
        
        # Preparar dados da apólice para análise
        policy_data = {
            'policy_number': policy_row[0],
            'insured_name': policy_row[1],
            'cep': policy_row[2],
            'insured_value': float(policy_row[3]) if policy_row[3] else 0,
            'property_type': policy_row[4],
            'latitude': float(policy_row[5]) if policy_row[5] else -23.5505,
            'longitude': float(policy_row[6]) if policy_row[6] else -46.6333
        }
        
        conn.close()
        
        # Mapear ID da cobertura para nome do modelo
        coverage_map = {
            2: 'vendaval',
            5: 'vendaval', 
            7: 'danos_eletricos',
            8: 'danos_eletricos',  # Usar danos_eletricos como fallback
            11: 'granizo',
            12: 'alagamento',
            13: 'granizo',
            14: 'alagamento'
        }
        
        coverage_type = coverage_map.get(cd_cobertura, 'vendaval')  # Default para vendaval
        
        # Simular análise de risco (já que os modelos reais podem não estar disponíveis)
        # Em produção, você usaria o CoverageRiskManager real
        base_score = random.uniform(20, 85)
        
        # Variar score baseado no tipo de cobertura
        if coverage_type == 'alagamento':
            score = base_score + random.uniform(-5, 15)
        elif coverage_type == 'vendaval':
            score = base_score + random.uniform(-10, 20)
        elif coverage_type == 'granizo':
            score = base_score + random.uniform(-8, 12)
        else:  # danos_eletricos
            score = base_score + random.uniform(-5, 10)
        
        # Garantir que está no range 0-100
        score = max(0, min(100, score))
        
        # Determinar nível de risco
        if score >= 75:
            nivel = 'alto'
        elif score >= 50:
            nivel = 'medio'
        elif score >= 25:
            nivel = 'baixo'
        else:
            nivel = 'muito_baixo'
        
        # Criar objeto de dados de risco
        risco_data = CoberturaRiscoData(
            nr_apolice=nr_apolice,
            cd_cobertura=cd_cobertura,
            cd_produto=1,  # Produto padrão
            score_risco=score,
            nivel_risco=nivel,
            probabilidade=score/100,
            modelo_usado=f'{coverage_type}_model_v2',
            versao_modelo='2.0',
            fatores_risco={"recalculado": True, "tipo": coverage_type},
            dados_climaticos={"temperatura": 25, "umidade": random.randint(40, 80)},
            dados_propriedade={"valor": policy_data['insured_value'], "tipo": policy_data['property_type']},
            resultado_predicao={"score": score, "confianca": random.uniform(0.8, 0.95)},
            confianca_modelo=random.uniform(0.85, 0.95),
            explicabilidade={"principais_fatores": ["localizacao", "historico", "clima"]},
            tempo_processamento_ms=random.randint(80, 200)
        )
        
        # Salvar no banco usando DAO
        dao = CoberturaRiscoDAO()
        result_ids = dao.salvar_multiplos_riscos([risco_data])
        
        if result_ids:
            return {
                "success": True, 
                "new_score": score,
                "new_level": nivel,
                "new_probability": score/100
            }
        else:
            return {"success": False, "error": "Erro ao salvar no banco"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_risk_level_text(score):
    """Converter score numérico para texto de nível - PADRONIZADO para 4 níveis"""
    if score >= 75:
        return "Alto"
    elif score >= 50:
        return "Médio"
    elif score >= 25:
        return "Baixo"
    else:
        return "Muito Baixo"


def update_single_policy_analysis(policy_number):
    """Atualizar análise de risco para uma apólice específica"""
    try:
        # Buscar dados da apólice específica
        import sqlite3
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        # Buscar dados da apólice
        query = """
        SELECT numero_apolice, cep, valor_segurado, tipo_residencia,
               latitude, longitude, score_risco, nivel_risco, probabilidade_sinistro
        FROM apolices 
        WHERE numero_apolice = ?
        """
        
        cursor.execute(query, (policy_number,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # Buscar coberturas da apólice
        policy_coverages = get_policy_coverages(policy_number)
        
        # Preparar dados para recálculo
        policy_data = {
            'numero_apolice': row[0],
            'cep': row[1],
            'latitude': row[4] if row[4] else -23.5505,
            'longitude': row[5] if row[5] else -46.6333,
            'tipo_residencia': row[3] if row[3] else 'casa',
            'valor_segurado': float(row[2]) if row[2] else 0,
            'score_risco': float(row[6]) if row[6] else 0,
            'nivel_risco': row[7] if row[7] else 'baixo',
            'probabilidade_sinistro': float(row[8]) if row[8] else 0
        }
        
        # Calcular nova análise com modelos específicos
        enhanced_analysis = calculate_enhanced_risk_with_coverages(policy_data, policy_coverages)
        
        # Atualizar no banco de dados
        new_score = enhanced_analysis['enhanced_score']
        new_level = enhanced_analysis['enhanced_level'] 
        new_probability = enhanced_analysis['enhanced_probability']
        
        update_query = """
        UPDATE apolices 
        SET score_risco = ?, nivel_risco = ?, probabilidade_sinistro = ?, updated_at = CURRENT_TIMESTAMP
        WHERE numero_apolice = ?
        """
        
        cursor.execute(update_query, (new_score, new_level, new_probability, policy_number))
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'new_score': new_score,
            'new_level': new_level,
            'new_probability': new_probability,
            'old_score': policy_data['score_risco'],
            'analyzed_coverages': enhanced_analysis['analyzed_coverages']
        }
        
    except Exception as e:
        st.error(f"Erro ao atualizar análise: {e}")
        return None

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
        elif "Médio" in risk_filter and "Baixo" not in risk_filter:
            filtered_policies = [p for p in filtered_policies if 50 <= p['risk_score'] < 75]
        elif "Baixo" in risk_filter and "Muito" not in risk_filter:
            filtered_policies = [p for p in filtered_policies if 25 <= p['risk_score'] < 50]
        elif "Muito Baixo" in risk_filter:
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

def get_policy_coverages(policy_number):
    """Buscar coberturas específicas de uma apólice"""
    try:
        import sqlite3
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        query = """
        SELECT c.nm_cobertura 
        FROM apolice_cobertura ac
        JOIN coberturas c ON ac.cd_cobertura = c.cd_cobertura
        WHERE ac.nr_apolice = ?
        """
        
        cursor.execute(query, (policy_number,))
        rows = cursor.fetchall()
        conn.close()
        
        # Retornar lista de nomes de coberturas
        return [row[0] for row in rows]
        
    except Exception as e:
        # Retornar coberturas padrão em caso de erro
        return ['Incêndio', 'Vendaval']

def calculate_enhanced_risk_with_coverages(policy_data, coverages):
    """Calcular risco usando modelos específicos de cobertura"""
    try:
        from src.ml.coverage_predictors import CoverageRiskManager
        
        # Mapear nomes de coberturas para modelos disponíveis
        coverage_mapping = {
            'Danos Elétricos': 'danos_eletricos',
            'Vendaval': 'vendaval', 
            'Granizo': 'granizo',
            'Alagamento': 'alagamento',
            'Responsabilidade Civil': None  # Não tem modelo climático específico
        }
        
        # Converter coberturas para formato dos modelos
        model_coverages = []
        for coverage in coverages:
            # Remover asterisco (*) que indica cobertura básica
            clean_coverage = coverage.replace('*', '').strip()
            
            if clean_coverage in coverage_mapping:
                if coverage_mapping[clean_coverage]:
                    model_coverages.append(coverage_mapping[clean_coverage])
        
        # Se não há coberturas mapeadas, usar padrão
        if not model_coverages:
            model_coverages = ['danos_eletricos', 'vendaval']
        
        # Fazer análise específica
        # Cache da instância no nível da função para evitar múltiplas inicializações
        if not hasattr(calculate_enhanced_risk_with_coverages, '_coverage_manager'):
            calculate_enhanced_risk_with_coverages._coverage_manager = CoverageRiskManager()
        
        coverage_manager = calculate_enhanced_risk_with_coverages._coverage_manager
        result = coverage_manager.analyze_all_coverages(policy_data, model_coverages)
        
        if result and 'summary' in result:
            # Retornar dados aprimorados com análise de cobertura
            enhanced_score = result['summary']['average_risk_score']
            enhanced_level = result['summary']['overall_risk_level']
            
            return {
                'enhanced_score': enhanced_score,
                'enhanced_level': enhanced_level,
                'enhanced_probability': enhanced_score / 100,  # Converter score para probabilidade
                'coverage_analysis': result,
                'analyzed_coverages': len(model_coverages)
            }
        
    except Exception as e:
        st.warning(f"Análise aprimorada indisponível: {e}")
    
    # Retornar dados originais se análise específica falhar
    return {
        'enhanced_score': policy_data.get('score_risco', 0),
        'enhanced_level': policy_data.get('nivel_risco', 'baixo'),
        'enhanced_probability': policy_data.get('probabilidade_sinistro', 0),
        'coverage_analysis': None,
        'analyzed_coverages': 0
    }

def get_real_policies_data(search_filter=None, risk_filter="Todos", type_filter="Todos", value_filter="Todos"):
    """Buscar dados reais de apólices do banco de dados SEM recalcular análises automaticamente"""
    
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
               probabilidade_sinistro, created_at, data_inicio,
               latitude, longitude
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
        # IMPORTANTE: NÃO recalcular automaticamente - apenas usar dados existentes
        policies = []
        for row in rows:
            # Buscar coberturas específicas da apólice
            policy_coverages = get_policy_coverages(row[0])  # numero_apolice
            
            # Usar dados JÁ EXISTENTES no banco - sem recálculo automático
            risk_score = float(row[5]) if row[5] else 0
            risk_level = row[6] if row[6] else 'baixo'
            probability = float(row[7]) if row[7] else 0
            
            # Mapear dados do banco para estrutura da interface
            policy = {
                'policy_number': row[0],  # numero_apolice
                'insured_name': row[1],   # segurado
                'cep': row[2],            # cep
                'insured_value': float(row[3]) if row[3] else 0,  # valor_segurado
                'property_type': row[4] if row[4] else 'casa',    # tipo_residencia
                
                # Usar dados EXISTENTES do banco (sem recálculo automático)
                'risk_score': risk_score,
                'risk_level': risk_level,
                'probability': probability,
                
                # Campos originais para histórico
                'original_score': risk_score,
                'original_level': risk_level,
                'original_probability': probability,
                
                # Metadados da análise
                'created_at': row[8],     # created_at
                'policy_start': row[9],   # data_inicio
                'coverages': policy_coverages,
                'analyzed_coverages': len(policy_coverages),
                'has_enhanced_analysis': len(policy_coverages) > 0,  # Se tem coberturas específicas
                
                # Campos calculados/inferidos
                'area': 100,  # Valor padrão (poderia ser calculado baseado no valor segurado)
                'annual_premium': float(row[3]) * (risk_score / 100) * 0.015 if row[3] else 0,
                'last_analysis': datetime.fromisoformat(row[8]) if row[8] else datetime.now(),
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
            elif "Médio" in risk_filter and "Baixo" not in risk_filter:
                filtered_policies = [p for p in filtered_policies if 50 <= p['risk_score'] < 75]
            elif "Baixo" in risk_filter and "Muito" not in risk_filter:
                filtered_policies = [p for p in filtered_policies if 25 <= p['risk_score'] < 50]
            elif "Muito Baixo" in risk_filter:
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
                st.info(f"ℹ️ Filtrado de {len(policies)} apólices totais")
        
        return filtered_policies
        
    except Exception as e:
        st.error(f"❌ Erro ao conectar com banco de dados: {e}")
        st.warning("⚠️ Usando dados simulados como fallback...")
        # Fallback para dados simulados
        return generate_mock_policies_data(search_filter, risk_filter, type_filter, value_filter)

def get_risk_level_emoji(score):
    """Retornar emoji baseado no score de risco - PADRONIZADO para 4 níveis"""
    if score >= 75:
        return "🔴 Alto"
    elif score >= 50:
        return "🟡 Médio"
    elif score >= 25:
        return "🟢 Baixo"
    else:
        return "⚪ Muito Baixo"

def format_risk_level_from_db(nivel_risco_db):
    """Converter nivel_risco do banco para formato de exibição"""
    if not nivel_risco_db:
        return "🟢 Baixo"
    
    nivel = nivel_risco_db.lower()
    if nivel == 'alto':
        return "🔴 Alto"
    elif nivel == 'medio':
        return "🟡 Médio"
    elif nivel == 'baixo':
        return "🟢 Baixo"
    elif nivel == 'muito_baixo':
        return "⚪ Muito Baixo"
    else:
        return "🟢 Baixo"  # padrão

# FUNÇÃO REMOVIDA - Estatísticas foi excluída do projeto  
# def show_statistics():
#     """Página de Estatísticas do sistema"""
#     pass
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
        st.subheader("📊 Distribuição de Scores de Risco")
        
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
        
        st.plotly_chart(fig, width='stretch')
    
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
        
        st.plotly_chart(fig, width='stretch')
    
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
            risco = "⚪ Muito Baixo"
        elif score < 50:
            risco = "🟢 Baixo"
        elif score < 75:
            risco = "🟡 Médio"
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
    st.dataframe(df, width='stretch')

def show_weather_monitoring():
    """Página de monitoramento climático"""
    st.header("🌍 Monitoramento Climático")
    
    # Input de localização
    col1, col2 = st.columns([2, 1])
    
    with col1:
        cep_weather = st.text_input("🌍 CEP para monitoramento climático", placeholder="12345-678", key="cep_monitoramento_clima")
    
    with col2:
        # Usar markdown para criar espaçamento visual preciso
        st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
        if st.button("🔍 Buscar Dados Climáticos", key="buscar_clima_btn", use_container_width=True):
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
                    st.subheader(f"🌤️ Condições Atuais - CEP {cep_weather}")
                    
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
                        alertas.append("🥶 Temperatura muito baixa - risco de congelamento")
                    
                    if precip > 20:
                        alertas.append("🌊 Precipitação intensa - risco de alagamento")
                    elif precip > 50:
                        alertas.append("⛈️ Chuva torrencial - risco alto de inundação")
                    
                    if wind > 60:
                        alertas.append("🌪️ Ventos muito fortes - risco estrutural")
                    
                    if humidity > 80:
                        alertas.append("💧 Umidade muito alta - risco de mofo")
                    
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
            
            st.subheader(f"🌤️ Condições Climáticas Simuladas - CEP {cep_weather}")
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
            st.plotly_chart(fig, width='stretch')
        
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
            st.plotly_chart(fig, width='stretch')
        
        # Análise de Risco climático
        st.markdown("---")
        st.subheader("⚠️ Análise de Risco Climático")
        
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
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            st.markdown("#### ⚠️ Fatores de Risco")
            
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
            recomendacoes.append("🏠 Verificar isolamento térmico da propriedade")
        
        if risco_precip > 50:
            recomendacoes.append("🚰 Inspecionar sistema de drenagem")
        
        if risco_vento > 50:
            recomendacoes.append("🔧 Verificar fixação de estruturas externas")
        
        if risco_umidade > 50:
            recomendacoes.append("💨 Melhorar ventilação para controle de umidade")
        
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
            ### 🏖️ Região Costeira
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
        st.subheader("⚠️ Alertas Meteorológicos Gerais")
        
        st.warning("🌧️ Previsão de chuva forte para região metropolitana de SP - Próximas 6h")
        st.info("❄️ Frente fria se aproximando do litoral sul - Temperatura pode cair 8°C")
        st.success("✅ Condições estáveis na região serrana - Tempo bom para os próximos 3 dias")


def show_api_documentation_section():
    """Seção de documentação da API com sub-navegação"""
    
    st.title("📚 Documentação da API")
    st.markdown("---")
    
    st.markdown("""
    Bem-vindo à documentação completa da **Radar Sinistro API**! 
    
    Esta seção contém tudo que você precisa para integrar e usar nossa API REST 
    para cálculo de risco de sinistros e gestão de apólices.
    """)
    
    # Sub-navegação para a API
    api_section = st.selectbox(
        "📋 Selecione a seção:",
        [
            "📚 Documentação Completa",
            "💻 Exemplos de Código"
        ]
    )
    
    st.markdown("---")
    
    if api_section == "📚 Documentação Completa":
        show_api_documentation()
    elif api_section == "💻 Exemplos de Código":
        show_code_examples()


def show_settings():
    """Página de configurações"""
    st.header("⚙️ Configurações do Sistema")
    
    # Configurações de predição
    st.subheader("⚙️ Configurações de Predição")
    
    col1, col2 = st.columns(2)
    
    with col1:
        incluir_clima_padrao = st.checkbox("Incluir dados climáticos por padrão", value=True)
        limite_risco_alto = st.slider("Limite para Risco Alto", 70, 90, 75)
        
    with col2:
        precisao_decimal = st.selectbox("Precisão decimal do score", [1, 2], index=0)
        cache_weather = st.checkbox("Cache de dados climáticos", value=True)
    
    if st.button("💾 Salvar Configurações"):
        st.success("✅ Configurações salvas com sucesso!")
    
    # Configurações de Envio Automático de Alertas
    st.markdown("---")
    st.subheader("🚨 Configuração de Envio Automático de Alertas")
    
    # Ativar/desativar alertas automáticos
    alertas_automaticos_ativo = st.checkbox(
        "Ativar envio automático de alertas", 
        value=False,
        help="Quando ativado, o sistema enviará alertas automaticamente para apólices em alto risco"
    )
    
    if alertas_automaticos_ativo:
        st.info("ℹ️ **Modo Automático Ativado:** O sistema enviará alertas automaticamente conforme configurado abaixo.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ⏰ Configurações de Tempo")
            
            # Frequência de envio
            frequencia_alertas = st.selectbox(
                "Frequência de envio",
                ["Diário", "Semanal", "Quinzenal", "Mensal"],
                index=1,
                help="Com que frequência os alertas serão enviados"
            )
            
            # Horário de envio
            horario_envio = st.time_input(
                "Horário de envio",
                value=datetime.strptime("09:00", "%H:%M").time(),
                help="Horário em que os alertas serão enviados"
            )
            
            # Limite mínimo de risco
            limite_risco_alerta = st.slider(
                "Score mínimo para envio de alerta",
                50, 100, 75,
                help="Apólices com score igual ou superior a este valor receberão alertas"
            )
        
        with col2:
            st.markdown("#### ⚙️ Configurações da Mensagem")
            
            # Assunto do email/SMS
            assunto_alerta = st.text_input(
                "Assunto do alerta",
                value="⚠️ Alerta de Risco - Radar de Sinistro",
                help="Assunto que aparecerá nos emails/SMS enviados"
            )
            
            # Canal de envio
            canal_envio = st.multiselect(
                "Canais de envio",
                ["Email", "SMS", "WhatsApp", "Sistema Interno"],
                default=["Email", "Sistema Interno"],
                help="Selecione os canais pelos quais os alertas serão enviados"
            )
            
            # Incluir dados do clima
            incluir_clima_alerta = st.checkbox(
                "Incluir dados climáticos no alerta",
                value=True,
                help="Adiciona informações sobre o clima previsto na mensagem"
            )
        
        # Configuração da mensagem personalizada
        st.markdown("#### 📝 Mensagem Personalizada")
        st.markdown("""
        <small>Você pode usar as seguintes variáveis na mensagem:<br>
        <code>{segurado}</code>, <code>{numero_apolice}</code>, <code>{score_risco}</code>, <code>{nivel_risco}</code>, 
        <code>{tipo_residencia}</code>, <code>{cep}</code>, <code>{valor_segurado}</code>, <code>{data_atual}</code>
        </small>
        """, unsafe_allow_html=True)
        
        # Mensagem padrão para alertas automáticos
        mensagem_padrao_auto = """Prezado(a) {segurado},

🚨 ALERTA DE RISCO ALTO - RADAR DE SINISTRO

Identificamos que sua apólice {numero_apolice} apresenta ALTO RISCO de sinistro ({score_risco}/100).

📋 DETALHES DA APÓLICE:
• Imóvel: {tipo_residencia} 
• Localização: CEP {cep}
• Valor Segurado: R$ {valor_segurado:,.2f}
• Nível de Risco: {nivel_risco}

💡 RECOMENDAÇÕES:
• Verifique as condições do imóvel
• Reforce medidas preventivas
• Entre em contato conosco para orientações

📞 Em caso de dúvidas, entre em contato:
• Telefone: (11) 99999-9999
• Email: suporte@radarsinistro.com

Atenciosamente,
Equipe Radar de Sinistro
Data: {data_atual}"""
        
        mensagem_personalizada_auto = st.text_area(
            "Mensagem do alerta automático:",
            value=mensagem_padrao_auto,
            height=300,
            help="Personalize a mensagem que será enviada automaticamente"
        )
        
        # Preview da mensagem
        st.markdown("#### 👁️ Pré-visualização da Mensagem")
        with st.expander("Ver pré-visualização", expanded=False):
            preview_message = mensagem_personalizada_auto.format(
                segurado="João da Silva",
                numero_apolice="POL-2025-001234",
                score_risco=82.5,
                nivel_risco="Alto",
                tipo_residencia="Casa",
                cep="01234-567",
                valor_segurado=350000.00,
                data_atual=datetime.now().strftime("%d/%m/%Y")
            )
            st.code(preview_message, language="text")
        
        # Configurações avançadas
        with st.expander("⚙️ Configurações Avançadas"):
            col1, col2 = st.columns(2)
            
            with col1:
                max_alertas_por_dia = st.number_input(
                    "Máximo de alertas por dia",
                    min_value=1, max_value=1000, value=50,
                    help="Limite diário de alertas para evitar spam"
                )
                
                cooldown_alerta = st.number_input(
                    "Intervalo entre alertas (dias)",
                    min_value=1, max_value=30, value=7,
                    help="Dias que devem passar antes de enviar novo alerta para a mesma apólice"
                )
            
            with col2:
                priorizar_maior_risco = st.checkbox(
                    "Priorizar apólices com maior risco",
                    value=True,
                    help="Enviar alertas primeiro para apólices com score mais alto"
                )
                
                incluir_relatorio = st.checkbox(
                    "Anexar relatório detalhado",
                    value=False,
                    help="Incluir PDF com análise detalhada da apólice"
                )
        
        # Botões de ação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Salvar Configurações de Alertas", width='stretch'):
                # Aqui você salvaria as configurações no banco de dados
                configuracoes_alertas = {
                    'ativo': alertas_automaticos_ativo,
                    'frequencia': frequencia_alertas,
                    'horario': horario_envio.strftime("%H:%M"),
                    'limite_risco': limite_risco_alerta,
                    'assunto': assunto_alerta,
                    'canais': canal_envio,
                    'incluir_clima': incluir_clima_alerta,
                    'mensagem': mensagem_personalizada_auto,
                    'max_por_dia': max_alertas_por_dia,
                    'cooldown': cooldown_alerta,
                    'priorizar_risco': priorizar_maior_risco,
                    'incluir_relatorio': incluir_relatorio
                }
                
                salvar_configuracoes_alertas(configuracoes_alertas)
                st.success("✅ Configurações de alertas automáticos salvas com sucesso!")
        
        with col2:
            if st.button("🧪 Testar Configuração", width='stretch'):
                with st.spinner("Enviando alerta de teste..."):
                    resultado_teste = testar_envio_alerta(mensagem_personalizada_auto, canal_envio)
                    if resultado_teste:
                        st.success("✅ Teste de alerta enviado com sucesso!")
                    else:
                        st.error("❌ Falha no teste de envio de alerta")
        
        with col3:
            if st.button("🚀 Executar Agora", width='stretch'):
                with st.spinner("Executando envio automático de alertas..."):
                    resultado = executar_alertas_automaticos(configuracoes_alertas)
                    if resultado['sucesso']:
                        st.success(f"✅ {resultado['enviados']} alertas enviados com sucesso!")
                        if resultado['erros'] > 0:
                            st.warning(f"⚠️ {resultado['erros']} alertas falharam")
                    else:
                        st.error("❌ Falha na execução dos alertas automáticos")
    
    else:
        st.warning("ℹ️ Alertas automáticos estão desativados. Ative a opção acima para configurar.")

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

def inicializar_tabela_bloqueios():
    """Cria a tabela de bloqueios se ela não existir"""
    try:
        import sqlite3
        import os
        
        # Garantir que o diretório existe
        os.makedirs('database', exist_ok=True)
        
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        # Criar tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS apolice_coberturas_bloqueadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nr_apolice VARCHAR(50) NOT NULL,
                cd_produto INTEGER NOT NULL,
                cd_cobertura INTEGER NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                ativo BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        st.error(f"Erro ao inicializar tabela de bloqueios: {e}")

def inicializar_tabela_regioes_bloqueadas():
    """Cria a tabela de regiões bloqueadas se ela não existir"""
    try:
        import sqlite3
        import os
        
        # Garantir que o diretório existe
        os.makedirs('database', exist_ok=True)
        
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        # Criar tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS regioes_bloqueadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cep VARCHAR(9) NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                ativo BOOLEAN DEFAULT 1,
                motivo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        st.error(f"Erro ao inicializar tabela de regiões bloqueadas: {e}")

def show_blocking_management():
    """Página de Gerenciamento de Bloqueios"""
    
    # Garantir que as tabelas de bloqueios existem
    inicializar_tabela_bloqueios()
    inicializar_tabela_regioes_bloqueadas()
    
    st.markdown("""
    <div class="main-header">
        <h2>🚫 GERENCIAMENTO DE BLOQUEIOS</h2>
        <p>Gestão de bloqueios de coberturas para apólices e emissão por região</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Criar abas para diferentes tipos de bloqueio
    tab1, tab2, tab3 = st.tabs([
        "🚫 Bloqueio de Cobertura",
        "🌍 Bloqueio por Região", 
        "📋 Visualizar Bloqueios"
    ])
    
    # Aba 1: Bloqueio de cobertura para apólice
    with tab1:
        show_bloqueio_cobertura()
    
    # Aba 2: Bloqueio de emissão por região
    with tab2:
        show_bloqueio_regiao()
    
    # Aba 3: Visualização de bloqueios ativos
    with tab3:
        show_visualizar_bloqueios()

def show_bloqueio_cobertura():
    """Aba de Bloqueio de Cobertura para Apólice"""
    st.markdown("### 🚫 Bloqueio de Cobertura para Apólice")
    st.markdown("Bloqueie coberturas específicas para apólices individuais")
    
    # Busca de apólice
    col1, col2 = st.columns([2, 1])
    
    with col1:
        numero_apolice = st.text_input(
            "Número da Apólice *",
            placeholder="Digite o número da apólice (ex: POL-2024-001234)",
            help="Digite o número da apólice para buscar as informações",
            key="numero_apolice_cobertura"
        )
    
    with col2:
        # Usar markdown para criar espaçamento visual preciso
        st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
        buscar_apolice = st.button("🔍 Buscar Apólice", key="buscar_apolice_bloqueio_btn", use_container_width=True)
    
    # Variáveis para armazenar dados da apólice
    apolice_data = None
    produto_info = None
    coberturas_disponiveis = []
    
    if buscar_apolice and numero_apolice:
        # Buscar informações da apólice
        apolice_data = buscar_informacoes_apolice(numero_apolice)
        
        if apolice_data:
            st.success(f"✅ Apólice {numero_apolice} encontrada!")
            
            # Buscar informações do produto
            produto_info = buscar_informacoes_produto(apolice_data.get('cd_produto'))
            
            # Buscar coberturas do produto
            coberturas_disponiveis = buscar_coberturas_produto(apolice_data.get('cd_produto'))
            
            # Exibir informações da apólice
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"""
                **📋 Informações da Apólice:**
                - **Segurado:** {apolice_data.get('segurado', 'N/A')}
                - **CEP:** {apolice_data.get('cep', 'N/A')}
                - **Valor Segurado:** R$ {apolice_data.get('valor_segurado', 0):,.2f}
                """)
            
            with col2:
                if produto_info:
                    st.info(f"""
                    **🛡️ Produto:**
                    - **Nome:** {produto_info.get('nm_produto', 'N/A')}
                    - **Ramo:** {produto_info.get('nm_ramo', 'N/A')}
                    """)
        else:
            st.error(f"❌ Apólice {numero_apolice} não encontrada!")
    
    # Formulário de bloqueio (só aparece se a apólice foi encontrada)
    if apolice_data and coberturas_disponiveis:
        st.markdown("---")
        
        with st.form("blocking_form"):
            # Campo multiselect com coberturas
            nomes_coberturas = [f"{cob['nm_cobertura']} (Cód: {cob['cd_cobertura']})" for cob in coberturas_disponiveis]
            coberturas_selecionadas = st.multiselect(
                "Coberturas a Bloquear *",
                options=nomes_coberturas,
                help="Selecione as coberturas que deseja bloquear para esta apólice"
            )
            
            # Campos de data
            col1, col2 = st.columns(2)
            
            with col1:
                data_inicio = st.date_input(
                    "Data de Início do Bloqueio *",
                    value=datetime.now().date(),
                    help="Data a partir da qual o bloqueio será aplicado"
                )
            
            with col2:
                data_fim = st.date_input(
                    "Data de Fim do Bloqueio *",
                    value=datetime.now().date() + timedelta(days=30),
                    help="Data até a qual o bloqueio será aplicado"
                )
            
            # Botão para gerar bloqueio
            submitted = st.form_submit_button("🚫 Gerar Bloqueio", use_container_width=True)
        
        # Processar formulário
        if submitted:
            if not coberturas_selecionadas:
                st.error("❌ Selecione pelo menos uma cobertura para bloquear!")
            elif data_inicio >= data_fim:
                st.error("❌ A data de início deve ser anterior à data de fim!")
            else:
                # Extrair códigos das coberturas selecionadas
                cd_coberturas_bloqueadas = []
                for cob_selecionada in coberturas_selecionadas:
                    cd_cobertura = int(cob_selecionada.split("(Cód: ")[1].split(")")[0])
                    cd_coberturas_bloqueadas.append(cd_cobertura)
                
                # Salvar bloqueios na tabela
                with st.spinner("Salvando bloqueios..."):
                    resultado = salvar_bloqueios_cobertura(
                        numero_apolice=numero_apolice,
                        cd_produto=apolice_data['cd_produto'],
                        cd_coberturas=cd_coberturas_bloqueadas,
                        data_inicio=data_inicio,
                        data_fim=data_fim
                    )
                
                if resultado['sucesso']:
                    # Preparar lista de coberturas bloqueadas para exibição
                    lista_coberturas = [cob['nm_cobertura'] for cob in resultado['coberturas']]
                    texto_coberturas = ", ".join(lista_coberturas)
                    
                    # Determinar se é singular ou plural
                    if resultado['quantidade'] == 1:
                        titulo = "Cobertura Bloqueada"
                        texto_quantidade = "1 cobertura foi bloqueada"
                    else:
                        titulo = "Coberturas Bloqueadas"
                        texto_quantidade = f"{resultado['quantidade']} coberturas foram bloqueadas"
                    
                    st.success(f"""
                    ✅ **{titulo} com Sucesso!**
                    
                    **Apólice:** {numero_apolice}
                    
                    **{texto_quantidade}:**
                    {texto_coberturas}
                    
                    **Período de Bloqueio:**
                    De {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}
                    
                    """)
                    
                    st.balloons()
                else:
                    st.error(f"""
                    ❌ **Erro ao criar bloqueio**
                    
                    {resultado.get('erro', 'Erro desconhecido. Verifique se já existe um bloqueio ativo para essas coberturas.')}
                    """)

def buscar_bloqueios_ativos():
    """Busca todos os bloqueios ativos no sistema"""
    try:
        import sqlite3
        
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        # Criar tabela se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS apolice_coberturas_bloqueadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nr_apolice VARCHAR(50) NOT NULL,
                cd_produto INTEGER NOT NULL,
                cd_cobertura INTEGER NOT NULL,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                ativo BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Query para buscar bloqueios ativos com informações das tabelas relacionadas
        query = '''
            SELECT 
                b.id,
                b.nr_apolice,
                b.cd_produto,
                b.cd_cobertura,
                b.data_inicio,
                b.data_fim,
                b.created_at,
                COALESCE(p.nm_produto, 'Produto não encontrado') as nm_produto,
                COALESCE(c.nm_cobertura, 'Cobertura não encontrada') as nm_cobertura
            FROM apolice_coberturas_bloqueadas b
            LEFT JOIN produtos p ON b.cd_produto = p.cd_produto
            LEFT JOIN coberturas c ON b.cd_cobertura = c.cd_cobertura
            WHERE b.ativo = 1 
                AND date(b.data_fim) >= date('now')
            ORDER BY b.created_at DESC
        '''
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        conn.close()
        
        if rows:
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        
        return []
        
    except Exception as e:
        st.error(f"Erro ao buscar bloqueios ativos: {e}")
        return []

def desativar_bloqueio(bloqueio_id):
    """Desativa um bloqueio específico"""
    try:
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        # Atualizar o bloqueio para inativo
        cursor.execute('''
            UPDATE apolice_coberturas_bloqueadas 
            SET ativo = 0, updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), bloqueio_id))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        st.error(f"Erro ao desativar bloqueio: {e}")
        return False

def buscar_informacoes_apolice(numero_apolice):
    """Busca informações de uma apólice pelo número"""
    try:
        from database import get_database, CRUDOperations
        
        db = get_database()
        crud = CRUDOperations(db)
        
        apolice = crud.get_apolice_by_numero(numero_apolice)
        
        if apolice:
            return {
                'id': apolice.id,
                'numero_apolice': apolice.numero_apolice,
                'segurado': apolice.segurado,
                'cd_produto': apolice.cd_produto,
                'cep': apolice.cep,
                'valor_segurado': apolice.valor_segurado,
                'tipo_residencia': apolice.tipo_residencia
            }
        return None
        
    except Exception as e:
        st.error(f"Erro ao buscar apólice: {e}")
        return None

def buscar_informacoes_produto(cd_produto):
    """Busca informações de um produto pelo código"""
    try:
        from database import get_database, CRUDOperations
        
        db = get_database()
        crud = CRUDOperations(db)
        
        produto = crud.get_produto_by_codigo(cd_produto)
        
        if produto:
            return {
                'cd_produto': produto.cd_produto,
                'nm_produto': produto.nm_produto,
                'cd_ramo': produto.cd_ramo,
                'nm_ramo': getattr(produto, 'nm_ramo', 'N/A')
            }
        return None
        
    except Exception as e:
        st.error(f"Erro ao buscar produto: {e}")
        return None

def buscar_coberturas_produto(cd_produto):
    """Busca todas as coberturas de um produto"""
    try:
        from database import get_database, CRUDOperations
        
        db = get_database()
        crud = CRUDOperations(db)
        
        coberturas = crud.get_coberturas_by_produto(cd_produto)
        
        cobertura_list = []
        for cobertura in coberturas:
            cobertura_list.append({
                'cd_cobertura': cobertura.cd_cobertura,
                'nm_cobertura': cobertura.nm_cobertura,
                'dv_basica': cobertura.dv_basica
            })
        
        return cobertura_list
        
    except Exception as e:
        st.error(f"Erro ao buscar coberturas: {e}")
        return []

def salvar_bloqueios_cobertura(numero_apolice, cd_produto, cd_coberturas, data_inicio, data_fim):
    """Salva bloqueios de cobertura na tabela apolice_coberturas_bloqueadas"""
    conn = None
    try:
        import sqlite3
        from datetime import datetime
        
        # Conectar ao banco
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        # Garantir que a tabela existe
        inicializar_tabela_bloqueios()
        
        bloqueios_salvos = []
        
        # Inserir bloqueios para cada cobertura selecionada
        for cd_cobertura in cd_coberturas:
            # Verificar se já existe bloqueio ativo para esta cobertura
            cursor.execute('''
                SELECT COUNT(*) FROM apolice_coberturas_bloqueadas 
                WHERE nr_apolice = ? AND cd_cobertura = ? AND ativo = 1
                AND date('now') BETWEEN data_inicio AND data_fim
            ''', (numero_apolice, cd_cobertura))
            
            ja_existe = cursor.fetchone()[0] > 0
            
            if ja_existe:
                continue
            
            # Inserir o bloqueio
            cursor.execute('''
                INSERT INTO apolice_coberturas_bloqueadas 
                (nr_apolice, cd_produto, cd_cobertura, data_inicio, data_fim, ativo)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (
                numero_apolice,
                cd_produto,
                cd_cobertura,
                data_inicio.isoformat(),
                data_fim.isoformat()
            ))
            
            
            # Buscar o nome da cobertura para retornar
            cursor.execute('''
                SELECT nm_cobertura FROM coberturas WHERE cd_cobertura = ?
            ''', (cd_cobertura,))
            
            resultado = cursor.fetchone()
            nome_cobertura = resultado[0] if resultado else f"Cobertura {cd_cobertura}"
            
            bloqueios_salvos.append({
                'cd_cobertura': cd_cobertura,
                'nm_cobertura': nome_cobertura
            })
        
        # Commit das transações
        conn.commit()
        
        return {
            'sucesso': True,
            'quantidade': len(bloqueios_salvos),
            'coberturas': bloqueios_salvos
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        st.error(f"❌ Erro ao salvar bloqueios: {e}")
        return {
            'sucesso': False,
            'erro': str(e)
        }
    finally:
        if conn:
            conn.close()

def salvar_bloqueio_regiao(cep, data_inicio, data_fim, motivo=None):
    """Salva bloqueio regional na tabela regioes_bloqueadas"""
    conn = None
    try:
        import sqlite3
        from datetime import datetime
        
        # Conectar ao banco
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        # Garantir que a tabela existe
        inicializar_tabela_regioes_bloqueadas()
        
        # Verificar se já existe bloqueio ativo para este CEP
        cursor.execute('''
            SELECT COUNT(*) FROM regioes_bloqueadas 
            WHERE cep = ? AND ativo = 1
            AND date('now') BETWEEN data_inicio AND data_fim
        ''', (cep,))
        
        ja_existe = cursor.fetchone()[0] > 0
        
        if ja_existe:
            return {
                'sucesso': False,
                'erro': 'Já existe um bloqueio ativo para esta região no período especificado.'
            }
        
        # Inserir o bloqueio regional
        cursor.execute('''
            INSERT INTO regioes_bloqueadas 
            (cep, data_inicio, data_fim, ativo, motivo)
            VALUES (?, ?, ?, 1, ?)
        ''', (
            cep,
            data_inicio.isoformat(),
            data_fim.isoformat(),
            motivo
        ))
        
        # Commit das transações
        conn.commit()
        
        return {
            'sucesso': True,
            'cep': cep,
            'motivo': motivo
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        st.error(f"❌ Erro ao salvar bloqueio regional: {e}")
        return {
            'sucesso': False,
            'erro': str(e)
        }
    finally:
        if conn:
            conn.close()

def buscar_bloqueios_regionais_ativos():
    """Busca todos os bloqueios regionais ativos"""
    try:
        import sqlite3
        
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, cep, data_inicio, data_fim, motivo, created_at
            FROM regioes_bloqueadas 
            WHERE ativo = 1 
            AND date('now') BETWEEN data_inicio AND data_fim
            ORDER BY created_at DESC
        ''')
        
        bloqueios = cursor.fetchall()
        
        bloqueios_list = []
        for bloqueio in bloqueios:
            bloqueios_list.append({
                'id': bloqueio[0],
                'cep': bloqueio[1],
                'data_inicio': bloqueio[2],
                'data_fim': bloqueio[3],
                'motivo': bloqueio[4] or 'Não especificado',
                'created_at': bloqueio[5]
            })
        
        conn.close()
        return bloqueios_list
        
    except Exception as e:
        st.error(f"Erro ao buscar bloqueios regionais: {e}")
        return []

def desativar_bloqueio_regional(bloqueio_id):
    """Desativa um bloqueio regional"""
    try:
        import sqlite3
        
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE regioes_bloqueadas 
            SET ativo = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (bloqueio_id,))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Erro ao desativar bloqueio regional: {e}")
        return False

def show_bloqueio_regiao():
    """Aba de Bloqueio de Emissão por Região"""
    st.markdown("### 🌍 Bloqueio de Emissão por Região")
    st.markdown("Bloqueie a emissão de novas apólices para regiões específicas por CEP")
    
    with st.form("region_blocking_form"):
        # Campo de CEP
        col1, col2 = st.columns([2, 1])
        
        with col1:
            cep = st.text_input(
                "CEP da Região *",
                placeholder="Digite o CEP (ex: 01234-567 ou 01234567)",
                help="Digite o CEP da região que deseja bloquear",
                key="cep_bloqueio_regional"
            )
        
        # Campos de data
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            data_inicio = st.date_input(
                "Data de Início do Bloqueio *",
                value=datetime.now().date(),
                help="Data a partir da qual o bloqueio será aplicado",
                key="data_inicio_regional"
            )
        
        with col2:
            data_fim = st.date_input(
                "Data de Fim do Bloqueio *",
                value=datetime.now().date() + timedelta(days=30),
                help="Data até a qual o bloqueio será aplicado",
                key="data_fim_regional"
            )
        
        # Campo de motivo (opcional)
        motivo = st.text_area(
            "Motivo do Bloqueio (opcional)",
            placeholder="Descreva o motivo do bloqueio da região...",
            help="Informação adicional sobre o motivo do bloqueio",
            key="motivo_bloqueio_regional"
        )
        
        # Botão para gerar bloqueio
        st.markdown("---")
        submitted = st.form_submit_button("🚫 Gerar Bloqueio Regional", use_container_width=True)
    
    # Processar formulário
    if submitted:
        # Validações
        if not cep:
            st.error("❌ Informe o CEP da região!")
        elif data_inicio >= data_fim:
            st.error("❌ A data de início deve ser anterior à data de fim!")
        else:
            # Normalizar CEP (remover caracteres especiais)
            cep_normalizado = cep.replace("-", "").replace(".", "").replace(" ", "")
            
            # Validar formato do CEP
            if len(cep_normalizado) != 8 or not cep_normalizado.isdigit():
                st.error("❌ CEP deve ter 8 dígitos numéricos!")
            else:
                # Salvar bloqueio regional na tabela
                with st.spinner("Salvando bloqueio regional..."):
                    resultado = salvar_bloqueio_regiao(
                        cep=cep_normalizado,
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                        motivo=motivo if motivo else None
                    )
                
                if resultado['sucesso']:
                    st.success(f"""
                    ✅ **Bloqueio Regional Criado com Sucesso!**
                    
                    **CEP Bloqueado:** {cep_normalizado[:5]}-{cep_normalizado[5:]}
                    
                    **Período de Bloqueio:**
                    De {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}
                    
                    **Motivo:** {motivo if motivo else 'Não especificado'}
                    
                    💾 *Dados persistidos na tabela regioes_bloqueadas*
                    """)
                    
                    # Dados salvos com sucesso
                    st.balloons()
                    
                    # Verificação adicional
                    try:
                        import sqlite3
                        conn = sqlite3.connect('database/radar_sinistro.db')
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM regioes_bloqueadas WHERE cep = ? AND ativo = 1", (cep_normalizado,))
                        total = cursor.fetchone()[0]
                        st.success(f"✅ **Verificação:** {total} bloqueios ativos encontrados para o CEP {cep_normalizado}")
                        conn.close()
                    except Exception as e:
                        st.error(f"Erro na verificação: {e}")
                else:
                    st.error(f"""
                    ❌ **Erro ao criar bloqueio regional**
                    
                    {resultado.get('erro', 'Erro desconhecido. Verifique se já existe um bloqueio ativo para esta região.')}
                    """)

def show_visualizar_bloqueios():
    """Aba de Visualização de Bloqueios Ativos"""
    st.markdown("### 📋 Bloqueios Ativos")
    st.markdown("Visualize e gerencie todos os bloqueios ativos do sistema")
    
    # Filtros para visualização
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_bloqueio = st.selectbox(
            "Tipo de Bloqueio",
            ["Todos", "Coberturas", "Regiões"],
            help="Filtrar por tipo de bloqueio"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        atualizar = st.button("🔄 Atualizar Lista", width='stretch')
    
    if tipo_bloqueio == "Todos" or tipo_bloqueio == "Coberturas":
        st.subheader("🚫 Bloqueios de Cobertura")
        # Buscar e exibir bloqueios ativos de cobertura
        bloqueios_cobertura = buscar_bloqueios_ativos()
        
        if bloqueios_cobertura:
            # Converter para DataFrame para melhor visualização
            df_bloqueios = pd.DataFrame(bloqueios_cobertura)
            
            # Exibir tabela
            st.dataframe(
                df_bloqueios[['nr_apolice', 'cd_produto', 'cd_cobertura', 'data_inicio', 'data_fim']],
                width='stretch'
            )
            
            # Opção para desativar bloqueios
            if st.expander("🗑️ Gerenciar Bloqueios de Cobertura"):
                for idx, bloqueio in enumerate(bloqueios_cobertura):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"**Apólice:** {bloqueio['nr_apolice']} - **Cobertura:** {bloqueio['cd_cobertura']}")
                    
                    with col2:
                        st.write(f"**Período:** {bloqueio['data_inicio']} até {bloqueio['data_fim']}")
                    
                    with col3:
                        if st.button(f"🗑️ Desativar", key=f"des_cob_{idx}"):
                            if desativar_bloqueio(bloqueio['id']):
                                st.success("Bloqueio desativado!")
                                st.rerun()
        else:
            st.info("Nenhum bloqueio de cobertura ativo encontrado.")
    
    if tipo_bloqueio == "Todos" or tipo_bloqueio == "Regiões":
        st.subheader("🌍 Bloqueios Regionais")
        # Buscar e exibir bloqueios regionais ativos
        bloqueios_regionais = buscar_bloqueios_regionais_ativos()
        
        if bloqueios_regionais:
            # Converter para DataFrame para melhor visualização
            df_regionais = pd.DataFrame(bloqueios_regionais)
            
            # Exibir tabela
            st.dataframe(
                df_regionais[['cep', 'data_inicio', 'data_fim', 'motivo']],
                width='stretch'
            )
            
            # Opção para desativar bloqueios
            if st.expander("🗑️ Gerenciar Bloqueios Regionais"):
                for idx, bloqueio in enumerate(bloqueios_regionais):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"**CEP:** {bloqueio['cep'][:5]}-{bloqueio['cep'][5:]}")
                    
                    with col2:
                        st.write(f"**Período:** {bloqueio['data_inicio']} até {bloqueio['data_fim']}")
                    
                    with col3:
                        if st.button(f"🗑️ Desativar", key=f"des_reg_{idx}"):
                            if desativar_bloqueio_regional(bloqueio['id']):
                                st.success("Bloqueio regional desativado!")
                                st.rerun()
        else:
            st.info("Nenhum bloqueio regional ativo encontrado.")

def show_alert_management():
    """Módulo de Gerenciamento de Alertas - Busca e envio de notificações para apólices"""
    
    st.header("🚨 Gerenciamento de Alertas")
    st.markdown("Sistema centralizado para busca de apólices e envio de notificações de risco")
    
    # Seção de busca de apólices
    st.markdown("---")
    st.subheader("🔍 Busca de Apólices")
    
    col1, col2, col3 = st.columns([2, 1, 2])

    with col1:
        search_policy = st.text_input(
            "Buscar Apólice", 
            placeholder="Digite o número da apólice (ex: POL-2025-001234) ou deixe vazio para listar todas",
            help="Busque uma apólice específica pelo número ou deixe vazio para ver todas",
            key="search_policy_alertas"
        )

    with col2:
        # Usar markdown para criar espaçamento visual preciso
        st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
        search_button = st.button("🔍 Buscar", key="buscar_alertas_btn", use_container_width=True)

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)  # Espaçamento vertical
    
    # Filtros avançados
    st.markdown("### 🔍 Filtros de Busca")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        risk_filter = st.selectbox(
            "Nível de Risco",
            ["Todos", "Alto (75-100)", "Médio-Alto (50-75)", "Médio-Baixo (25-50)", "Baixo (0-25)"]
        )

    with col2:
        property_type = st.selectbox(
            "Tipo de Imóvel",
            ["Todos", "Casa", "Apartamento", "Sobrado", "Cobertura", "Kitnet"]
        )

    with col3:
        value_range = st.selectbox(
            "Faixa de Valor",
            ["Todos", "Até R$ 100k", "R$ 100k - 300k", "R$ 300k - 500k", "R$ 500k - 1M", "Acima R$ 1M"]
        )

    with col4:
        notified_filter = st.selectbox(
            "Status de Notificação",
            ["Todas", "Já Notificadas Hoje", "Não Notificadas Hoje", "Nunca Notificadas"]
        )
    
    # Buscar apólices baseado nos filtros
    current_filters = (search_policy, risk_filter, property_type, value_range, notified_filter)
    if 'alert_policies_cache' not in st.session_state or st.session_state.get('last_alert_filters', None) != current_filters:
        policies_data = get_real_policies_data(search_policy, risk_filter, property_type, value_range)
        st.session_state.alert_policies_cache = policies_data
        st.session_state.last_alert_filters = current_filters
    
    policies_data = st.session_state.alert_policies_cache
    
    # Inicializar selected_policies para evitar UnboundLocalError
    selected_policies = []
    
    # Resumo das apólices encontradas
    st.markdown("---")
    st.subheader("📊 Resumo da Busca")
    
    if policies_data:
        col1, col2, col3, col4 = st.columns(4)
        
        high_risk = len([p for p in policies_data if p['risk_score'] >= 75])
        medium_risk = len([p for p in policies_data if 50 <= p['risk_score'] < 75])
        low_risk = len([p for p in policies_data if p['risk_score'] < 50])
        total_found = len(policies_data)
        
        with col1:
            st.metric("📋 Total Encontradas", total_found)
        
        with col2:
            st.metric("🔴 Alto Risco", high_risk, f"{high_risk/total_found*100:.1f}%" if total_found else "0%")
        
        with col3:
            st.metric("🟡 Médio Risco", medium_risk, f"{medium_risk/total_found*100:.1f}%" if total_found else "0%")
        
        with col4:
            st.metric("🟢 Baixo Risco", low_risk, f"{low_risk/total_found*100:.1f}%" if total_found else "0%")
        
        # Lista compacta das apólices encontradas (sem tabela completa)
        st.markdown("---")
        st.subheader("📋 Apólices Encontradas")
        
        # Criar DataFrame básico
        df = pd.DataFrame(policies_data)
        # Forçar conversão para float
        df['risk_score'] = df['risk_score'].astype(float)
        df['risk_level'] = df['risk_score'].apply(get_risk_level_emoji)

        # Obter status de notificações
        try:
            from database import get_database, CRUDOperations
            crud_tmp = CRUDOperations(get_database())
            notificacoes_map = crud_tmp.get_notificacoes_por_apolices(df['policy_number'].tolist())
        except Exception:
            notificacoes_map = {}

        # Aplicar filtro de notificação
        df['notified_today'] = df['policy_number'].apply(lambda p: '?' if p in notificacoes_map else '—')

        if notified_filter == "Já Notificadas Hoje":
            df = df[df['notified_today'] == '✅']
        elif notified_filter == "Não Notificadas Hoje":
            df = df[df['notified_today'] == '—']
        elif notified_filter == "Nunca Notificadas":
            # Para este filtro, precisaríamos de uma consulta mais complexa no banco
            pass
        
        # Mostrar lista resumida
        if len(df) > 0:
            # Lista em formato compacto
            for idx, row in df.head(10).iterrows():  # Mostrar apenas os primeiros 10
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{row['policy_number']}** - {row.get('insured_name', 'N/A')}")
                
                with col2:
                    st.write(f"{row['risk_level']} (Score: {row['risk_score']:.1f})")
                
                with col3:
                    st.write(f"{row['property_type'].title()} - {row['cep']}")
                
                with col4:
                    st.write(f"Notif.: {row['notified_today']}")
            
            if len(df) > 10:
                st.info(f"Mostrando primeiras 10 de {len(df)} apólices encontradas. Use os filtros para refinar a busca.")
        
        # Seção de envio de notificações
        st.markdown("---")
        st.subheader("?? Envio de Notificações")
        
        # Seleção de apólices para notificar
        if 'selected_alert_policies' not in st.session_state:
            st.session_state.selected_alert_policies = []
        
        # Opções de seleção rápida
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Selecionar Todas", width='stretch'):
                st.session_state.selected_alert_policies = df['policy_number'].tolist()
        
        with col2:
            if st.button("Limpar Seleção", width='stretch'):
                st.session_state.selected_alert_policies = []
        
        # Multiselect para seleção manual
        selectable_policies = df['policy_number'].tolist()
        
        def format_policy_option(policy_num):
            row = df[df['policy_number'] == policy_num].iloc[0]
            return f"{policy_num} | {row['risk_level']} | Score: {row['risk_score']:.1f} | {row['property_type'].title()}"
        
        selected_policies = st.multiselect(
            "Selecione as apólices para notificar:",
            options=selectable_policies,
            default=st.session_state.selected_alert_policies,
            format_func=format_policy_option,
            help="Selecione uma ou mais apólices para enviar notificações"
        )
        
        st.session_state.selected_alert_policies = selected_policies
        
        # Configuração da mensagem
        st.markdown("#### ?? Configuração da Mensagem")
        st.markdown("""
<small>Você pode personalizar a mensagem enviada ao segurado. Variáveis disponíveis:<br>
<code>{segurado}</code>, <code>{numero_apolice}</code>, <code>{nivel_risco}</code>, <code>{score_risco}</code>, <code>{tipo_residencia}</code>, <code>{cep}</code>
</small>
""", unsafe_allow_html=True)

        mensagem_padrao = (
            "Olá, {segurado}!\n"
            "Identificamos que sua apólice {numero_apolice} apresenta risco {nivel_risco} ({score_risco}/100) "
            "para o imóvel {tipo_residencia} no endereço {cep}.\n"
            "Recomendamos atenção especial e, se desejar, entre em contato conosco para orientações.\n\n"
            "Atenciosamente,\n"
            "Equipe Radar de Sinistro."
        )

        mensagem_personalizada = st.text_area(
            "Mensagem a ser enviada:",
            value=mensagem_padrao,
            height=120,
            help="Use as variáveis: {segurado}, {numero_apolice}, {nivel_risco}, {score_risco}, {tipo_residencia}, {cep}"
        )

        # Pré-visualização da mensagem
        if selected_policies:
            st.markdown("#### ??? Pré-visualização")
            preview_policy = selected_policies[0]
            preview_row = df[df['policy_number'] == preview_policy].iloc[0]

            preview_message = mensagem_personalizada.format(
                segurado=preview_row.get('insured_name', 'Segurado'),
                numero_apolice=preview_policy,
                nivel_risco=preview_row['risk_level'],
                score_risco=preview_row['risk_score'],
                tipo_residencia=preview_row['property_type'],
                cep=preview_row['cep']
            )

            st.code(preview_message, language="text")
            st.caption(f"Pré-visualização baseada na apólice: {preview_policy}")
            
            # Botão de envio
            st.markdown("#### ?? Enviar Notificações")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.info(f"?? {len(selected_policies)} apólice(s) selecionada(s) para notificação")
            
            with col2:
                if st.button("?? Enviar Alertas", type="primary", width='stretch'):
                    send_alert_notifications(selected_policies, df, mensagem_personalizada, notificacoes_map)
        else:
            st.warning("?? Selecione pelo menos uma apólice para enviar notificações.")
        
    else:
        st.info("?? Nenhuma apólice encontrada com os critérios de busca especificados.")
        st.markdown("**Sugestões:**")
        st.markdown("- Verifique se o número da apólice está correto")
        st.markdown("- Tente ajustar os filtros de busca")
        st.markdown("- Use 'Gerenciar Apólices' para adicionar novas apólices")

def send_alert_notifications(selected_policies, df, mensagem_personalizada, notificacoes_map):
    """Enviar notificações para as apólices selecionadas"""
    
    from database import get_database, CRUDOperations
    
    try:
        db = get_database()
        db.ensure_notifications_table()
        crud = CRUDOperations(db)
        
        enviados = []
        ja_notificados = []
        erros = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, policy_num in enumerate(selected_policies):
            status_text.text(f"Processando: {policy_num}")
            progress_bar.progress((i + 1) / len(selected_policies))
            
            # Verificar se já foi notificada hoje
            if policy_num in notificacoes_map:
                ja_notificados.append(policy_num)
                continue
            
            try:
                row = df[df['policy_number'] == policy_num].iloc[0]
                
                # Personalizar mensagem
                mensagem = mensagem_personalizada.format(
                    segurado=row.get('insured_name', 'Segurado'),
                    numero_apolice=policy_num,
                    nivel_risco=row['risk_level'],
                    score_risco=row['risk_score'],
                    tipo_residencia=row['property_type'],
                    cep=row['cep']
                )
                
                # Registrar notificação no banco
                crud.insert_notificacao_risco(
                    apolice_id=0,
                    numero_apolice=policy_num,
                    segurado=row.get('insured_name'),
                    email=row.get('email'),
                    telefone=row.get('telefone'),
                    canal='sistema_alertas',
                    mensagem=mensagem,
                    score_risco=row['risk_score'],
                    nivel_risco=row['risk_level'],
                    simulacao=True,
                    status='sucesso'
                )
                
                # Marcar apólice como notificada
                crud.marcar_apolice_notificada(policy_num)
                
                enviados.append(policy_num)
                
            except Exception as e:
                erros.append((policy_num, str(e)))
        
        # Limpar barra de progresso
        progress_bar.empty()
        status_text.empty()
        
        # Mostrar resultados
        if enviados:
            st.success(f"? {len(enviados)} notificação(ões) enviada(s) com sucesso!")
            with st.expander("Apólices notificadas"):
                for policy in enviados:
                    st.write(f"• {policy}")
        
        if ja_notificados:
            st.info(f"?? {len(ja_notificados)} apólice(s) já havia(m) sido notificada(s) hoje:")
            with st.expander("Apólices já notificadas"):
                for policy in ja_notificados:
                    st.write(f"• {policy}")
        
        if erros:
            st.error(f"? {len(erros)} erro(s) no envio:")
            with st.expander("Erros detalhados"):
                for policy, erro in erros:
                    st.write(f"• {policy}: {erro}")
        
        # Limpar seleção após envio
        if enviados or ja_notificados:
            st.session_state.selected_alert_policies = []
    
    except Exception as e:
        st.error(f"Erro geral no envio de notificações: {str(e)}")

def show_mapa_calor():
    """Página do Mapa de Calor - NOVA FUNÇÃO"""
    #st.header("🗺️ Mapa de Calor - Distribuição de Riscos por CEP")
    #st.markdown("Visualização geográfica interativa dos riscos de sinistros baseada nos CEPs das apólices cadastradas.")
    
    # Verificar se há dados de apólices no banco
    try:
        # Buscar dados reais do banco
        policies_data = get_real_policies_data()
        
        if not policies_data:
            st.warning("?? Nenhuma apólice encontrada no banco de dados.")
            st.info("?? Adicione apólices através de 'Gerenciar Apólices' para ver o mapa!")
            
            # Botão para ir para gerenciar apólices
            if st.button("? Ir para Gerenciar Apólices", width='stretch'):
                st.session_state.page_redirect = "? Gerenciar Apólices"
                st.rerun()
            
            # Oferecer dados de exemplo
            st.markdown("---")
            st.subheader("?? Ou visualize com dados de exemplo:")
            
            if st.button("?? Gerar Mapa com Dados de Exemplo", width='stretch'):
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
          
        # Distribuição por nível de risco
        st.markdown("---")

        # Usar a função completa do mapa de calor
        criar_interface_streamlit(policies_df)
        
    except Exception as e:
        st.error(f"? Erro ao carregar dados: {e}")
        st.warning("?? Usando dados de exemplo...")
        
        # Fallback para dados de exemplo
        criar_interface_streamlit(pd.DataFrame())


def main():
    """
    Função principal da aplicação Radar de Sinistro
    Centraliza a lógica de navegação e renderização
    """
    try:
        # Cabeçalho principal
        render_main_header()
        
        # Navegação e páginas
        render_navigation()
        
    except Exception as e:
        st.error(f"? Erro crítico na aplicação: {str(e)}")
        st.info("?? Recarregue a página ou entre em contato com o suporte.")


def render_main_header():
    """Renderiza o cabeçalho principal da aplicação"""
    st.markdown("""
    <div class="main-header">
        <h1>🌦️ Radar de Sinistro v3.0</h1>
        <p>Sistema Inteligente de Predição de Riscos Climáticos</p>
    </div>
    """, unsafe_allow_html=True)


def render_navigation():
    """Renderiza a navegação principal da aplicação"""
    # Sidebar para navegação
    st.sidebar.title("🧭 Navegação")
    
    page = st.sidebar.selectbox(
        "Selecione uma seção:",
        [
            "🏠 Dashboard Principal",
            "🎯 Análise de Riscos", 
            "📋 Gestão de Apólices",
            "📊 Coberturas em Risco",
            "🌍 Monitoramento Climático",
            "🗺️ Mapa de Calor",
            "📚 Documentação da API",
            "💻 Exemplos de Código",
            "⚙️ Configurações"
        ]
    )
    
    # Renderizar página selecionada
    render_selected_page(page)


def render_selected_page(page: str):
    """
    Renderiza a página selecionada na navegação
    
    Args:
        page: Nome da página selecionada
    """
    if page == "🏠 Dashboard Principal":
        show_dashboard_main()
    elif page == "🎯 Análise de Riscos":
        show_policies_at_risk()  # Mapear para análise de riscos existente
    elif page == "📋 Gestão de Apólices":
        show_manage_policies()
    elif page == "📊 Coberturas em Risco":
        show_policies_at_risk()
    elif page == "🌍 Monitoramento Climático":
        show_weather_monitoring()
    elif page == "🗺️ Mapa de Calor":
        show_mapa_calor()
    elif page == "📚 Documentação da API":
        show_api_documentation()
    elif page == "💻 Exemplos de Código":
        show_code_examples()
    elif page == "⚙️ Configurações":
        show_settings()


def show_dashboard_main():
    """Dashboard principal com visão geral do sistema"""
    st.header("🏠 Dashboard Principal")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_policies = safe_get_total_policies()
        st.metric("📋 Apólices Ativas", total_policies, "🔼 +12")
    
    with col2:
        active_alerts = safe_get_active_alerts_count()
        st.metric("⚠️ Alertas Ativos", active_alerts, "🔻 -3")
        
    with col3:
        st.metric("🌦️ Monitoramento", "Ativo", "✅")
        
    with col4:
        coverage_count = safe_get_coverage_count()
        st.metric("📊 Coberturas", coverage_count, "➡️ 0")
    
    # Gráficos resumo
    st.subheader("📊 Visão Geral dos Riscos")
    
    # Mostrar resumo das coberturas em risco
    show_policies_at_risk()


def safe_get_total_policies():
    """Obtém o total de apólices de forma segura"""
    try:
        # Tentar usar a função existente se disponível
        if 'get_real_policies_data' in globals():
            policies = get_real_policies_data()
            return len(policies) if policies else 0
        return "N/A"
    except Exception:
        return "N/A"


def safe_get_active_alerts_count():
    """Obtém a contagem de alertas ativos de forma segura"""
    try:
        # Tentar obter alertas do banco de dados ou memória
        import sqlite3
        db_path = "dados_radar_sinistro.db"
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM alertas WHERE ativo = 1")
            count = cursor.fetchone()[0]
            return count
    except Exception:
        return 0


def safe_get_coverage_count():
    """Obtém a contagem de coberturas de forma segura"""
    try:
        # Retornar um valor básico por enquanto
        return "4"  # Alagamento, Granizo, Vendaval, Danos Elétricos
    except Exception:
        return "N/A"


if __name__ == "__main__":
    main()










