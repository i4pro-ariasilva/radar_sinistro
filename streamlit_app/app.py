"""
Sistema de Radar de Risco Climático - Interface Streamlit
Aplicação principal com múltiplas páginas
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Radar de Risco Climático",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Adicionar o diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# CSS customizado - Compatível com temas claro e escuro
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    
    /* Cards com melhor contraste para ambos os temas */
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #1f77b4;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        color: #212529;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        border-color: #0d6efd;
    }
    
    .metric-card h3 {
        color: #1f77b4;
        margin-bottom: 0.75rem;
        font-size: 1.2rem;
        font-weight: 600;
    }
    
    .metric-card p {
        color: #495057;
        margin: 0;
        line-height: 1.5;
        font-size: 0.95rem;
    }
    
    /* Tema escuro - detecção automática */
    @media (prefers-color-scheme: dark) {
        .metric-card {
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            border-color: #4299e1;
            color: #e2e8f0;
        }
        
        .metric-card h3 {
            color: #63b3ed;
        }
        
        .metric-card p {
            color: #cbd5e0;
        }
    }
    
    /* Forçar estilo para tema escuro do Streamlit */
    [data-testid="stAppViewContainer"][data-theme="dark"] .metric-card,
    .stApp[data-theme="dark"] .metric-card {
        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%) !important;
        border-color: #4299e1 !important;
        color: #e2e8f0 !important;
    }
    
    [data-testid="stAppViewContainer"][data-theme="dark"] .metric-card h3,
    .stApp[data-theme="dark"] .metric-card h3 {
        color: #63b3ed !important;
    }
    
    [data-testid="stAppViewContainer"][data-theme="dark"] .metric-card p,
    .stApp[data-theme="dark"] .metric-card p {
        color: #cbd5e0 !important;
    }
    
    /* Classes específicas para níveis de risco */
    .risk-high {
        border-color: #e53e3e !important;
        background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
    }
    
    .risk-medium {
        border-color: #dd6b20 !important;
        background: linear-gradient(135deg, #feebc8 0%, #fbd38d 100%);
    }
    
    .risk-low {
        border-color: #38a169 !important;
        background: linear-gradient(135deg, #c6f6d5 0%, #9ae6b4 100%);
    }
    
    /* Tema escuro para cards de risco */
    @media (prefers-color-scheme: dark),
    [data-testid="stAppViewContainer"][data-theme="dark"],
    .stApp[data-theme="dark"] {
        .risk-high {
            background: linear-gradient(135deg, #742a2a 0%, #9c4221 100%) !important;
        }
        
        .risk-medium {
            background: linear-gradient(135deg, #975a16 0%, #b7791f 100%) !important;
        }
        
        .risk-low {
            background: linear-gradient(135deg, #276749 0%, #2f855a 100%) !important;
        }
    }
    
    /* Melhorar visibilidade geral */
    .sidebar .sidebar-content {
        background-color: var(--background-color);
    }
    
    .stAlert {
        margin-top: 1rem;
    }
    
    /* Garantir contraste em botões */
    .stButton > button {
        border: 2px solid #1f77b4;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        border-color: #0d6efd;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Página principal da aplicação"""
    
    # Script para detectar tema
    st.markdown("""
    <script>
        // Detectar mudanças de tema
        function updateTheme() {
            const streamlitDoc = window.parent.document;
            const theme = streamlitDoc.body.getAttribute('data-theme') || 
                         (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
            
            streamlitDoc.documentElement.setAttribute('data-detected-theme', theme);
        }
        
        // Executar quando a página carrega
        updateTheme();
        
        // Observar mudanças no tema
        const observer = new MutationObserver(updateTheme);
        observer.observe(window.parent.document.body, { 
            attributes: true, 
            attributeFilter: ['data-theme', 'class'] 
        });
        
        // Observar mudanças na preferência do sistema
        window.matchMedia('(prefers-color-scheme: dark)').addListener(updateTheme);
    </script>
    """, unsafe_allow_html=True)
    
    # Título principal
    st.markdown('<h1 class="main-header">🚗 Radar de Sinistros - Sistema de Análise</h1>', unsafe_allow_html=True)
    
    # Sidebar para navegação
    with st.sidebar:
        st.markdown("### 📋 Navegação")
        st.markdown("Use o menu abaixo para navegar entre as páginas:")
        
        st.markdown("---")
        st.markdown("### 📊 Páginas Disponíveis")
        st.markdown("🏠 **Dashboard** - Visão geral do sistema")
        st.markdown("📤 **Upload de Dados** - Carregar arquivos de apólices")
        st.markdown("⚠️ **Análise de Risco** - Mapas e análises")
        st.markdown("📈 **Relatórios** - Estatísticas e métricas")
        
        st.markdown("---")
        st.markdown("### ℹ️ Sobre o Sistema")
        st.info("""
        Este sistema integra dados de apólices com informações climáticas 
        para identificar regiões de alto risco e permitir ações preventivas.
        """)
    
    # Conteúdo principal
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🏠 Dashboard Principal</h3>
            <p>Visão geral do sistema com métricas principais, 
            gráficos de tendências e status do banco de dados.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Ir para Dashboard", key="dashboard", use_container_width=True):
            st.switch_page("pages/01_📊_Dashboard.py")
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📤 Upload de Dados</h3>
            <p>Carregue arquivos CSV de apólices, 
            processe dados e visualize relatórios de qualidade.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Processar Dados", key="upload", use_container_width=True):
            st.switch_page("pages/02_📤_Upload_de_Dados.py")
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>⚠️ Análise de Risco</h3>
            <p>Visualize mapas de risco, análises por região 
            e previsões climáticas integradas.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Analisar Risco", key="risk", use_container_width=True):
            st.switch_page("pages/03_⚠️_Análise_de_Risco.py")
    
    # Seção de início rápido
    st.markdown("---")
    st.markdown("## 🚀 Início Rápido")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 1️⃣ Primeiro Uso")
        st.markdown("""
        1. **Inicialize o sistema** - Configure banco e dependências
        2. **Gere dados de exemplo** - Para testar funcionalidades
        3. **Explore o dashboard** - Visualize métricas principais
        """)
        
        if st.button("🔧 Inicializar Sistema", use_container_width=True):
            with st.spinner("Inicializando sistema..."):
                try:
                    # Importar e executar inicialização
                    from config import create_directories
                    from database import get_database
                    
                    # Criar diretórios
                    create_directories()
                    
                    # Inicializar banco
                    db = get_database()
                    db.initialize_database()
                    
                    st.success("✅ Sistema inicializado com sucesso!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Erro na inicialização: {str(e)}")
    
    with col2:
        st.markdown("### 2️⃣ Dados de Exemplo")
        st.markdown("""
        1. **Gere dados fictícios** - 500 apólices + histórico de sinistros
        2. **Teste funcionalidades** - Upload, análise e relatórios
        3. **Explore visualizações** - Mapas e gráficos interativos
        """)
        
        if st.button("📊 Gerar Dados de Exemplo", use_container_width=True):
            with st.spinner("Gerando dados de exemplo..."):
                try:
                    from database import SampleDataGenerator, get_database
                    
                    db = get_database()
                    generator = SampleDataGenerator(db)
                    
                    # Gerar dados de exemplo
                    generator.generate_all_sample_data()
                    
                    st.success("✅ Dados de exemplo gerados com sucesso!")
                    st.info("💡 Agora você pode explorar todas as funcionalidades do sistema!")
                    
                except Exception as e:
                    st.error(f"❌ Erro ao gerar dados: {str(e)}")
    
    # Informações do sistema
    st.markdown("---")
    st.markdown("## 📋 Informações do Sistema")
    
    with st.expander("🔧 Configurações e Status"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Configurações")
            st.code(f"""
            Diretório: {ROOT_DIR}
            Python: {sys.version.split()[0]}
            Streamlit: {st.__version__}
            """)
        
        with col2:
            st.markdown("### Status do Sistema")
            try:
                from database import get_database
                db = get_database()
                
                if os.path.exists(db.db_path):
                    st.success("✅ Banco de dados conectado")
                else:
                    st.warning("⚠️ Banco não inicializado")
                    
            except Exception as e:
                st.error(f"❌ Erro de conexão: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: 2rem;">
        <p>🌦️ <strong>Sistema de Radar de Risco Climático</strong></p>
        <p>Desenvolvido com ❤️ para prevenção inteligente de sinistros</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()