"""
📚 DOCUMENTAÇÃO DA API - RADAR DE SINISTRO
Documentação completa das rotas da API REST
"""

import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd


def check_api_status():
    """Verifica se a API está rodando e acessível"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        return False


def show_api_documentation():
    """Página principal de documentação da API"""
    
    st.title("📚 Documentação da API")
    st.markdown("---")
    
    # Tabs para organizar a documentação
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Visão Geral", 
        "🔄 Cálculo de Risco", 
        "📋 Gestão de Apólices", 
        "🛡️ Coberturas", 
        "🧪 Teste Interativo"
    ])
    
    with tab1:
        show_api_overview()
    
    with tab2:
        show_risk_endpoints()
    
    with tab3:
        show_policies_endpoints()
    
    with tab4:
        show_coverages_endpoints()
    
    with tab5:
        show_interactive_testing()


def show_api_overview():
    """Visão geral da API"""
    
    st.header("🌟 Radar Sinistro API v1.0")
    
    st.markdown("""
    A **Radar Sinistro API** é uma API REST robusta para cálculo de risco de sinistros 
    e gestão de apólices de seguro com base em análise climática e características de imóveis.
    
    ### 🎯 Principais Funcionalidades
    
    - **Cálculo de Risco**: Análise preditiva individual e em lote
    - **Gestão de Apólices**: CRUD completo de apólices com consultas avançadas
    - **Análise de Coberturas**: Gestão e análise de risco por cobertura
    - **Rankings**: Classificações por risco e valor segurado
    - **Estatísticas**: Relatórios e métricas do portfólio
    """)
    
    # Informações técnicas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ⚙️ Informações Técnicas
        
        - **Base URL**: `http://localhost:8000/api/v1`
        - **Formato**: JSON
        - **Autenticação**: Não requerida (desenvolvimento)
        - **Rate Limiting**: Configurado por endpoint
        - **Documentação Swagger**: `/docs`
        - **ReDoc**: `/redoc`
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Status da API
        
        - **Status**: 🟢 Ativo
        - **Versão**: 1.0.0
        - **Última Atualização**: Outubro 2025
        - **Endpoints**: 20+ rotas disponíveis
        - **Modelos ML**: Carregados e operacionais
        """)
    
    # Códigos de resposta
    st.markdown("### 📋 Códigos de Resposta HTTP")
    
    status_codes = pd.DataFrame([
        {"Código": "200", "Status": "OK", "Descrição": "Requisição bem-sucedida"},
        {"Código": "400", "Status": "Bad Request", "Descrição": "Dados inválidos na requisição"},
        {"Código": "404", "Status": "Not Found", "Descrição": "Recurso não encontrado"},
        {"Código": "422", "Status": "Unprocessable Entity", "Descrição": "Erro de validação"},
        {"Código": "500", "Status": "Internal Server Error", "Descrição": "Erro interno do servidor"}
    ])
    
    st.dataframe(status_codes, width='stretch', hide_index=True)
    
    # Links úteis
    st.markdown("### 🔗 Links Úteis")
    
    # Verificar se a API está rodando
    api_status = check_api_status()
    
    if not api_status:
        st.warning("⚠️ A API não está rodando. Para acessar os links, inicie a API primeiro:")
        st.code("cd radar_sinistro && python start_api_simple.bat", language="bash")
        st.markdown("ou execute: `python -m uvicorn api.main:app --reload --port 8000`")
        st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if api_status:
            st.link_button(
                "📖 Swagger UI", 
                "http://localhost:8000/docs",
                width='stretch'
            )
        else:
            st.button("📖 Swagger UI", disabled=True, width='stretch')
            st.caption("API não disponível")
    
    with col2:
        if api_status:
            st.link_button(
                "📚 ReDoc", 
                "http://localhost:8000/redoc",
                width='stretch'
            )
        else:
            st.button("📚 ReDoc", disabled=True, width='stretch')
            st.caption("API não disponível")
    
    with col3:
        if api_status:
            st.link_button(
                "❤️ Health Check", 
                "http://localhost:8000/health",
                width='stretch'
            )
        else:
            st.button("❤️ Health Check", disabled=True, width='stretch')
            st.caption("API não disponível")


def show_risk_endpoints():
    """Documentação dos endpoints de cálculo de risco"""
    
    st.header("🔄 Endpoints de Cálculo de Risco")
    
    # Endpoint 1: Cálculo individual
    st.subheader("1. Cálculo Individual")
    st.code("POST /api/v1/risk/calculate", language="http")
    
    st.markdown("**Descrição**: Calcula o risco de sinistro para uma apólice individual")
    
    with st.expander("📥 Payload de Exemplo"):
        st.code("""
{
  "numero_apolice": "POL-2025-001234",
  "segurado": "João da Silva",
  "cep": "01234567",
  "valor_segurado": 350000.00,
  "tipo_residencia": "Casa",
  "data_inicio": "2025-01-15"
}
        """, language="json")
    
    with st.expander("📤 Resposta de Exemplo"):
        st.code("""
{
  "success": true,
  "data": {
    "numero_apolice": "POL-2025-001234",
    "score_risco": 82.5,
    "nivel_risco": "ALTO",
    "probabilidade": 0.1847,
    "fatores_principais": [
      "Região de alto risco climático",
      "Valor segurado elevado",
      "Histórico de sinistros na região"
    ],
    "calculation_date": "2025-10-10T16:30:00"
  },
  "message": "Risco calculado com sucesso para apólice POL-2025-001234"
}
        """, language="json")
    
    # Endpoint 2: Cálculo em lote
    st.subheader("2. Cálculo em Lote")
    st.code("POST /api/v1/risk/calculate-batch", language="http")
    
    st.markdown("**Descrição**: Calcula o risco para múltiplas apólices (máximo 100)")
    
    with st.expander("📥 Payload de Exemplo"):
        st.code("""
{
  "policies": [
    {
      "numero_apolice": "POL-001",
      "segurado": "Cliente 1",
      "cep": "01234567",
      "valor_segurado": 250000.00,
      "tipo_residencia": "Casa",
      "data_inicio": "2025-01-15"
    },
    {
      "numero_apolice": "POL-002",
      "segurado": "Cliente 2",
      "cep": "98765432",
      "valor_segurado": 180000.00,
      "tipo_residencia": "Apartamento",
      "data_inicio": "2025-02-01"
    }
  ]
}
        """, language="json")
    
    # Endpoint 3: Calcular e salvar
    st.subheader("3. Calcular e Salvar")
    st.code("POST /api/v1/risk/calculate-and-save", language="http")
    
    st.markdown("**Descrição**: Calcula o risco e salva a apólice no banco de dados")


def show_policies_endpoints():
    """Documentação dos endpoints de apólices"""
    
    st.header("📋 Endpoints de Gestão de Apólices")
    
    # Listar apólices
    st.subheader("1. Listar Apólices")
    st.code("GET /api/v1/policies/", language="http")
    
    st.markdown("**Parâmetros de Query**:")
    
    params_df = pd.DataFrame([
        {"Parâmetro": "skip", "Tipo": "int", "Padrão": "0", "Descrição": "Registros para pular (paginação)"},
        {"Parâmetro": "limit", "Tipo": "int", "Padrão": "100", "Descrição": "Máximo de registros (1-1000)"},
        {"Parâmetro": "nivel_risco", "Tipo": "string", "Padrão": "null", "Descrição": "Filtrar por nível de risco"},
        {"Parâmetro": "segurado", "Tipo": "string", "Padrão": "null", "Descrição": "Buscar por nome do segurado"}
    ])
    
    st.dataframe(params_df, width='stretch', hide_index=True)
    
    # Buscar apólice específica
    st.subheader("2. Buscar Apólice")
    st.code("GET /api/v1/policies/{numero_apolice}", language="http")
    
    st.markdown("**Exemplo**: `GET /api/v1/policies/POL-2025-001234`")
    
    # Rankings
    st.subheader("3. Ranking por Risco")
    st.code("GET /api/v1/policies/rankings/risk", language="http")
    
    st.subheader("4. Ranking por Valor")
    st.code("GET /api/v1/policies/rankings/value", language="http")
    
    # Estatísticas
    st.subheader("5. Estatísticas Resumidas")
    st.code("GET /api/v1/policies/stats/summary", language="http")
    
    # Deletar apólice
    st.subheader("6. Remover Apólice")
    st.code("DELETE /api/v1/policies/{numero_apolice}", language="http")


def show_coverages_endpoints():
    """Documentação dos endpoints de coberturas"""
    
    st.header("🛡️ Endpoints de Coberturas")
    
    st.markdown("""
    Os endpoints de coberturas permitem análise detalhada de risco por tipo de cobertura,
    oferecendo insights granulares sobre o portfólio de seguros.
    """)
    
    # Listar todas as coberturas
    st.subheader("1. Listar Todas as Coberturas")
    st.code("GET /api/v1/coverages/", language="http")
    
    st.markdown("**Descrição**: Lista todas as coberturas disponíveis no sistema")
    
    with st.expander("📤 Resposta de Exemplo"):
        st.code("""
{
  "success": true,
  "data": [
    {
      "cd_cobertura": 1,
      "cd_produto": 100,
      "nm_cobertura": "Incêndio",
      "dv_basica": true,
      "created_at": "2025-01-01T00:00:00"
    },
    {
      "cd_cobertura": 2,
      "cd_produto": 100,
      "nm_cobertura": "Vendaval",
      "dv_basica": false,
      "created_at": "2025-01-01T00:00:00"
    }
  ],
  "total": 8,
  "message": "Encontradas 8 coberturas"
}
        """, language="json")
    
    # Coberturas com análise de risco
    st.subheader("2. Coberturas com Análise de Risco")
    st.code("GET /api/v1/coverages/risks/list", language="http")
    
    st.markdown("**Parâmetros de Query**:")
    
    risk_params_df = pd.DataFrame([
        {"Parâmetro": "skip", "Tipo": "int", "Descrição": "Paginação - registros para pular"},
        {"Parâmetro": "limit", "Tipo": "int", "Descrição": "Máximo de registros (1-1000)"},
        {"Parâmetro": "nivel_risco", "Tipo": "string", "Descrição": "Filtrar por nível (BAIXO, MÉDIO, ALTO, CRÍTICO)"},
        {"Parâmetro": "cd_produto", "Tipo": "int", "Descrição": "Filtrar por código do produto"},
        {"Parâmetro": "nr_apolice", "Tipo": "string", "Descrição": "Filtrar por número da apólice"},
        {"Parâmetro": "score_min", "Tipo": "float", "Descrição": "Score mínimo de risco (0-100)"},
        {"Parâmetro": "score_max", "Tipo": "float", "Descrição": "Score máximo de risco (0-100)"}
    ])
    
    st.dataframe(risk_params_df, width='stretch', hide_index=True)
    
    # Coberturas de uma apólice
    st.subheader("3. Coberturas de uma Apólice")
    st.code("GET /api/v1/coverages/policy/{nr_apolice}", language="http")
    
    st.markdown("**Exemplo**: `GET /api/v1/coverages/policy/POL-2025-001234`")
    
    # Ranking de coberturas
    st.subheader("4. Ranking por Risco")
    st.code("GET /api/v1/coverages/rankings/risk", language="http")
    
    # Coberturas de alto risco
    st.subheader("5. Coberturas de Alto Risco")
    st.code("GET /api/v1/coverages/risks/high-risk", language="http")
    
    st.markdown("**Parâmetros**:")
    st.markdown("- `threshold`: Score mínimo para alto risco (padrão: 75)")
    st.markdown("- `limit`: Máximo de resultados")
    
    # Coberturas por produto
    st.subheader("6. Coberturas por Produto")
    st.code("GET /api/v1/coverages/risks/by-product/{cd_produto}", language="http")
    
    # Estatísticas de coberturas
    st.subheader("7. Estatísticas de Coberturas")
    st.code("GET /api/v1/coverages/stats/summary", language="http")


def show_interactive_testing():
    """Seção de teste interativo da API"""
    
    st.header("🧪 Teste Interativo da API")
    
    st.markdown("""
    Use esta seção para testar os endpoints da API diretamente pela interface web.
    """)
    
    # Configuração da URL base
    col1, col2 = st.columns([2, 1])
    
    with col1:
        base_url = st.text_input(
            "URL Base da API:",
            value="http://localhost:8000/api/v1",
            help="URL base onde a API está rodando"
        )
    
    with col2:
        if st.button("🔍 Testar Conexão"):
            test_api_connection(base_url)
    
    st.markdown("---")
    
    # Seletor de endpoint
    endpoint_category = st.selectbox(
        "Categoria de Endpoint:",
        ["Health Check", "Cálculo de Risco", "Gestão de Apólices", "Coberturas"]
    )
    
    if endpoint_category == "Health Check":
        test_health_check(base_url)
    elif endpoint_category == "Cálculo de Risco":
        test_risk_calculation(base_url)
    elif endpoint_category == "Gestão de Apólices":
        test_policies_endpoints(base_url)
    elif endpoint_category == "Coberturas":
        test_coverages_endpoints(base_url)


def test_api_connection(base_url):
    """Testa a conexão com a API"""
    try:
        health_url = base_url.replace("/api/v1", "/health")
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            st.success("✅ Conexão com a API estabelecida com sucesso!")
            data = response.json()
            st.json(data)
        else:
            st.error(f"❌ Erro na conexão: Status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro de conexão: {str(e)}")
        
        # Instruções detalhadas para iniciar a API
        with st.expander("💡 Como iniciar a API", expanded=True):
            st.markdown("""
            **Opção 1 - Script automatizado:**
            ```bash
            start_api_simple.bat
            ```
            
            **Opção 2 - Comando direto:**
            ```bash
            python -m uvicorn api.main:app --reload --port 8000
            ```
            
            **Opção 3 - Com configurações avançadas:**
            ```bash
            start_api.bat
            ```
            
            Após iniciar a API, os endpoints estarão disponíveis em:
            - 📖 Swagger UI: http://localhost:8000/docs
            - 📚 ReDoc: http://localhost:8000/redoc
            - ❤️ Health: http://localhost:8000/health
            """)
            
            st.info("🔄 Aguarde alguns segundos para a API inicializar completamente.")


def test_health_check(base_url):
    """Teste do health check"""
    st.subheader("❤️ Health Check")
    
    if st.button("Executar Health Check"):
        try:
            health_url = base_url.replace("/api/v1", "/health")
            response = requests.get(health_url, timeout=5)
            
            st.markdown(f"**Status Code**: {response.status_code}")
            st.json(response.json())
            
        except Exception as e:
            st.error(f"Erro: {str(e)}")


def test_risk_calculation(base_url):
    """Teste de cálculo de risco"""
    st.subheader("🎯 Teste de Cálculo de Risco")
    
    # Formulário para dados da apólice
    with st.form("risk_calculation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            numero_apolice = st.text_input("Número da Apólice", value="TEST-001")
            segurado = st.text_input("Nome do Segurado", value="Teste da Silva")
            cep = st.text_input("CEP", value="01234567")
        
        with col2:
            valor_segurado = st.number_input("Valor Segurado", value=250000.0)
            tipo_residencia = st.selectbox("Tipo de Residência", ["Casa", "Apartamento", "Chácara"])
            data_inicio = st.date_input("Data de Início", value=datetime.now().date())
        
        submit = st.form_submit_button("🚀 Calcular Risco")
        
        if submit:
            payload = {
                "numero_apolice": numero_apolice,
                "segurado": segurado,
                "cep": cep,
                "valor_segurado": valor_segurado,
                "tipo_residencia": tipo_residencia,
                "data_inicio": data_inicio.isoformat()
            }
            
            try:
                response = requests.post(
                    f"{base_url}/risk/calculate",
                    json=payload,
                    timeout=10
                )
                
                st.markdown(f"**Status Code**: {response.status_code}")
                st.json(response.json())
                
            except Exception as e:
                st.error(f"Erro: {str(e)}")


def test_policies_endpoints(base_url):
    """Teste dos endpoints de apólices"""
    st.subheader("📋 Teste de Endpoints de Apólices")
    
    action = st.selectbox(
        "Ação:",
        ["Listar Apólices", "Buscar Apólice Específica", "Rankings", "Estatísticas"]
    )
    
    if action == "Listar Apólices":
        col1, col2, col3 = st.columns(3)
        
        with col1:
            skip = st.number_input("Skip", value=0, min_value=0)
        with col2:
            limit = st.number_input("Limit", value=10, min_value=1, max_value=100)
        with col3:
            nivel_risco = st.selectbox("Nível de Risco", [None, "BAIXO", "MÉDIO", "ALTO", "CRÍTICO"])
        
        if st.button("Listar"):
            params = {"skip": skip, "limit": limit}
            if nivel_risco:
                params["nivel_risco"] = nivel_risco
            
            try:
                response = requests.get(f"{base_url}/policies/", params=params)
                st.json(response.json())
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    elif action == "Buscar Apólice Específica":
        numero_apolice = st.text_input("Número da Apólice")
        
        if st.button("Buscar") and numero_apolice:
            try:
                response = requests.get(f"{base_url}/policies/{numero_apolice}")
                st.json(response.json())
            except Exception as e:
                st.error(f"Erro: {str(e)}")


def test_coverages_endpoints(base_url):
    """Teste dos endpoints de coberturas"""
    st.subheader("🛡️ Teste de Endpoints de Coberturas")
    
    action = st.selectbox(
        "Ação:",
        [
            "Listar Todas as Coberturas",
            "Coberturas com Análise de Risco",
            "Coberturas de uma Apólice",
            "Ranking por Risco",
            "Estatísticas"
        ]
    )
    
    if action == "Listar Todas as Coberturas":
        if st.button("Listar Coberturas"):
            try:
                response = requests.get(f"{base_url}/coverages/")
                st.json(response.json())
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    elif action == "Coberturas com Análise de Risco":
        col1, col2, col3 = st.columns(3)
        
        with col1:
            skip = st.number_input("Skip", value=0, min_value=0, key="cov_skip")
            limit = st.number_input("Limit", value=10, min_value=1, key="cov_limit")
        
        with col2:
            nivel_risco = st.selectbox("Nível de Risco", [None, "BAIXO", "MÉDIO", "ALTO", "CRÍTICO"], key="cov_nivel")
            cd_produto = st.number_input("Código do Produto", value=None, key="cov_produto")
        
        with col3:
            score_min = st.number_input("Score Mínimo", value=None, min_value=0.0, max_value=100.0, key="cov_score_min")
            score_max = st.number_input("Score Máximo", value=None, min_value=0.0, max_value=100.0, key="cov_score_max")
        
        if st.button("Buscar Coberturas com Risco"):
            params = {"skip": skip, "limit": limit}
            if nivel_risco:
                params["nivel_risco"] = nivel_risco
            if cd_produto:
                params["cd_produto"] = cd_produto
            if score_min is not None:
                params["score_min"] = score_min
            if score_max is not None:
                params["score_max"] = score_max
            
            try:
                response = requests.get(f"{base_url}/coverages/risks/list", params=params)
                st.json(response.json())
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    elif action == "Coberturas de uma Apólice":
        nr_apolice = st.text_input("Número da Apólice", key="cov_apolice")
        
        if st.button("Buscar Coberturas") and nr_apolice:
            try:
                response = requests.get(f"{base_url}/coverages/policy/{nr_apolice}")
                st.json(response.json())
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    elif action == "Ranking por Risco":
        col1, col2 = st.columns(2)
        
        with col1:
            order = st.selectbox("Ordem", ["desc", "asc"], key="cov_order")
        with col2:
            limit = st.number_input("Limit", value=10, min_value=1, max_value=100, key="cov_rank_limit")
        
        if st.button("Obter Ranking"):
            params = {"order": order, "limit": limit}
            
            try:
                response = requests.get(f"{base_url}/coverages/rankings/risk", params=params)
                st.json(response.json())
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    elif action == "Estatísticas":
        if st.button("Obter Estatísticas"):
            try:
                response = requests.get(f"{base_url}/coverages/stats/summary")
                st.json(response.json())
            except Exception as e:
                st.error(f"Erro: {str(e)}")
