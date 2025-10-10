"""
📋 EXEMPLOS DE CÓDIGO - RADAR DE SINISTRO API
Exemplos práticos de uso da API em diferentes linguagens
"""

import streamlit as st
import json


def show_code_examples():
    """Página com exemplos de código para usar a API"""
    
    st.title("💻 Exemplos de Código")
    st.markdown("---")
    
    st.markdown("""
    Esta seção contém exemplos práticos de como usar a **Radar Sinistro API** 
    em diferentes linguagens de programação.
    """)
    
    # Tabs para diferentes linguagens
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🐍 Python", 
        "☕ JavaScript", 
        "📱 cURL", 
        "⚡ PowerShell",
        "🔧 Postman"
    ])
    
    with tab1:
        show_python_examples()
    
    with tab2:
        show_javascript_examples()
    
    with tab3:
        show_curl_examples()
    
    with tab4:
        show_powershell_examples()
    
    with tab5:
        show_postman_examples()


def show_python_examples():
    """Exemplos em Python"""
    
    st.header("🐍 Exemplos em Python")
    
    # Configuração inicial
    st.subheader("1. Configuração Inicial")
    
    st.code("""
import requests
import json
from datetime import datetime

# Configuração da API
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

class RadarSinistroAPI:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.headers = HEADERS
    
    def health_check(self):
        \"\"\"Verifica se a API está funcionando\"\"\"
        response = requests.get(f"{self.base_url.replace('/api/v1', '')}/health")
        return response.json()
    """, language="python")
    
    # Cálculo de risco
    st.subheader("2. Cálculo de Risco Individual")
    
    st.code("""
def calcular_risco_individual(api, apolice_data):
    \"\"\"Calcula risco para uma apólice\"\"\"
    endpoint = f"{api.base_url}/risk/calculate"
    
    response = requests.post(
        endpoint,
        headers=api.headers,
        json=apolice_data
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Erro {response.status_code}: {response.text}")

# Exemplo de uso
api = RadarSinistroAPI()

apolice = {
    "numero_apolice": "POL-2025-001234",
    "segurado": "João da Silva",
    "cep": "01234567",
    "valor_segurado": 350000.00,
    "tipo_residencia": "Casa",
    "data_inicio": "2025-01-15"
}

try:
    resultado = calcular_risco_individual(api, apolice)
    
    print(f"Score de Risco: {resultado['data']['score_risco']}")
    print(f"Nível de Risco: {resultado['data']['nivel_risco']}")
    print(f"Probabilidade: {resultado['data']['probabilidade']:.4f}")
    
except Exception as e:
    print(f"Erro: {e}")
    """, language="python")
    
    # Cálculo em lote
    st.subheader("3. Cálculo de Risco em Lote")
    
    st.code("""
def calcular_risco_lote(api, lista_apolices):
    \"\"\"Calcula risco para múltiplas apólices\"\"\"
    endpoint = f"{api.base_url}/risk/calculate-batch"
    
    payload = {"policies": lista_apolices}
    
    response = requests.post(
        endpoint,
        headers=api.headers,
        json=payload
    )
    
    return response.json()

# Exemplo com múltiplas apólices
apolices = [
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

resultado_lote = calcular_risco_lote(api, apolices)

print(f"Processadas: {resultado_lote['total_processed']}")
print(f"Sucessos: {resultado_lote['successful']}")
print(f"Falhas: {resultado_lote['failed']}")
    """, language="python")
    
    # Gestão de apólices
    st.subheader("4. Gestão de Apólices")
    
    st.code("""
def listar_apolices(api, skip=0, limit=100, filtros=None):
    \"\"\"Lista apólices com paginação e filtros\"\"\"
    endpoint = f"{api.base_url}/policies/"
    
    params = {"skip": skip, "limit": limit}
    if filtros:
        params.update(filtros)
    
    response = requests.get(endpoint, params=params)
    return response.json()

def buscar_apolice(api, numero_apolice):
    \"\"\"Busca uma apólice específica\"\"\"
    endpoint = f"{api.base_url}/policies/{numero_apolice}"
    response = requests.get(endpoint)
    return response.json()

def ranking_risco(api, order="desc", limit=50):
    \"\"\"Obtém ranking por risco\"\"\"
    endpoint = f"{api.base_url}/policies/rankings/risk"
    params = {"order": order, "limit": limit}
    response = requests.get(endpoint, params=params)
    return response.json()

# Exemplos de uso
apolices = listar_apolices(api, limit=10)
print(f"Total de apólices: {apolices['total']}")

apolice_especifica = buscar_apolice(api, "POL-2025-001234")
if apolice_especifica['success']:
    print(f"Segurado: {apolice_especifica['data']['segurado']}")

ranking = ranking_risco(api, limit=5)
print("Top 5 apólices de maior risco:")
for i, apolice in enumerate(ranking['data'], 1):
    print(f"{i}. {apolice['segurado']} - Score: {apolice['score_risco']}")
    """, language="python")
    
    # Análise de coberturas
    st.subheader("5. Análise de Coberturas")
    
    st.code("""
def listar_coberturas(api):
    \"\"\"Lista todas as coberturas disponíveis\"\"\"
    endpoint = f"{api.base_url}/coverages/"
    response = requests.get(endpoint)
    return response.json()

def coberturas_com_risco(api, filtros=None):
    \"\"\"Lista coberturas com análise de risco\"\"\"
    endpoint = f"{api.base_url}/coverages/risks/list"
    
    params = {"skip": 0, "limit": 100}
    if filtros:
        params.update(filtros)
    
    response = requests.get(endpoint, params=params)
    return response.json()

def coberturas_apolice(api, nr_apolice):
    \"\"\"Obtém coberturas de uma apólice específica\"\"\"
    endpoint = f"{api.base_url}/coverages/policy/{nr_apolice}"
    response = requests.get(endpoint)
    return response.json()

def alto_risco_coberturas(api, threshold=75):
    \"\"\"Lista coberturas de alto risco\"\"\"
    endpoint = f"{api.base_url}/coverages/risks/high-risk"
    params = {"threshold": threshold, "limit": 100}
    response = requests.get(endpoint, params=params)
    return response.json()

# Exemplos de uso
coberturas = listar_coberturas(api)
print(f"Coberturas disponíveis: {coberturas['total']}")

# Filtrar coberturas de alto risco
filtros_risco = {"nivel_risco": "ALTO", "score_min": 80}
alto_risco = coberturas_com_risco(api, filtros_risco)
print(f"Coberturas de alto risco: {len(alto_risco['data'])}")

# Analisar apólice específica
cob_apolice = coberturas_apolice(api, "POL-2025-001234")
if cob_apolice['success']:
    data = cob_apolice['data']
    print(f"Apólice: {data['nr_apolice']}")
    print(f"Segurado: {data['segurado']}")
    print(f"Total de coberturas: {data['total_coberturas']}")
    print(f"Score médio: {data['score_risco_medio']:.2f}")
    print(f"Nível geral: {data['nivel_risco_geral']}")
    """, language="python")


def show_javascript_examples():
    """Exemplos em JavaScript"""
    
    st.header("☕ Exemplos em JavaScript")
    
    # Configuração inicial
    st.subheader("1. Configuração com Fetch API")
    
    st.code("""
class RadarSinistroAPI {
    constructor(baseUrl = 'http://localhost:8000/api/v1') {
        this.baseUrl = baseUrl;
        this.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }

    async healthCheck() {
        const response = await fetch(this.baseUrl.replace('/api/v1', '') + '/health');
        return await response.json();
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: this.headers,
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${data.message || 'Erro na requisição'}`);
            }
            
            return data;
        } catch (error) {
            console.error('Erro na API:', error);
            throw error;
        }
    }
}
    """, language="javascript")
    
    # Cálculo de risco
    st.subheader("2. Cálculo de Risco")
    
    st.code("""
// Cálculo de risco individual
async function calcularRiscoIndividual(api, apoliceData) {
    return await api.request('/risk/calculate', {
        method: 'POST',
        body: JSON.stringify(apoliceData)
    });
}

// Cálculo de risco em lote
async function calcularRiscoLote(api, listaApolices) {
    return await api.request('/risk/calculate-batch', {
        method: 'POST',
        body: JSON.stringify({ policies: listaApolices })
    });
}

// Exemplo de uso
const api = new RadarSinistroAPI();

const apolice = {
    numero_apolice: "POL-2025-001234",
    segurado: "João da Silva",
    cep: "01234567",
    valor_segurado: 350000.00,
    tipo_residencia: "Casa",
    data_inicio: "2025-01-15"
};

// Usar async/await
async function exemploCalculo() {
    try {
        const resultado = await calcularRiscoIndividual(api, apolice);
        
        console.log(`Score de Risco: ${resultado.data.score_risco}`);
        console.log(`Nível de Risco: ${resultado.data.nivel_risco}`);
        console.log(`Probabilidade: ${resultado.data.probabilidade.toFixed(4)}`);
        
    } catch (error) {
        console.error('Erro no cálculo:', error.message);
    }
}

exemploCalculo();
    """, language="javascript")
    
    # Gestão de apólices
    st.subheader("3. Gestão de Apólices")
    
    st.code("""
// Listar apólices
async function listarApolices(api, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const endpoint = `/policies/${queryString ? '?' + queryString : ''}`;
    return await api.request(endpoint);
}

// Buscar apólice específica
async function buscarApolice(api, numeroApolice) {
    return await api.request(`/policies/${numeroApolice}`);
}

// Ranking por risco
async function rankingRisco(api, order = 'desc', limit = 50) {
    const params = new URLSearchParams({ order, limit });
    return await api.request(`/policies/rankings/risk?${params}`);
}

// Estatísticas
async function estatisticasApolices(api) {
    return await api.request('/policies/stats/summary');
}

// Exemplo de uso com Promise
listarApolices(api, { limit: 10, nivel_risco: 'ALTO' })
    .then(apolices => {
        console.log(`Total de apólices: ${apolices.total}`);
        apolices.data.forEach(apolice => {
            console.log(`${apolice.segurado} - Score: ${apolice.score_risco}`);
        });
    })
    .catch(error => console.error('Erro:', error));
    """, language="javascript")
    
    # Análise de coberturas
    st.subheader("4. Análise de Coberturas")
    
    st.code("""
// Listar todas as coberturas
async function listarCoberturas(api) {
    return await api.request('/coverages/');
}

// Coberturas com análise de risco
async function coberturasComRisco(api, filtros = {}) {
    const params = new URLSearchParams({ skip: 0, limit: 100, ...filtros });
    return await api.request(`/coverages/risks/list?${params}`);
}

// Coberturas de uma apólice
async function coberturasApolice(api, nrApolice) {
    return await api.request(`/coverages/policy/${nrApolice}`);
}

// Coberturas de alto risco
async function altoRiscoCoberturas(api, threshold = 75) {
    const params = new URLSearchParams({ threshold, limit: 100 });
    return await api.request(`/coverages/risks/high-risk?${params}`);
}

// Exemplo com múltiplas chamadas
async function analisarPortfolio(api) {
    try {
        const [coberturas, altoRisco, estatisticas] = await Promise.all([
            listarCoberturas(api),
            altoRiscoCoberturas(api, 80),
            api.request('/coverages/stats/summary')
        ]);

        console.log('=== ANÁLISE DO PORTFÓLIO ===');
        console.log(`Total de coberturas: ${coberturas.total}`);
        console.log(`Coberturas de alto risco: ${altoRisco.total_high_risk}`);
        console.log(`Score médio: ${estatisticas.data.estatisticas_score.media}`);

    } catch (error) {
        console.error('Erro na análise:', error);
    }
}

analisarPortfolio(api);
    """, language="javascript")


def show_curl_examples():
    """Exemplos em cURL"""
    
    st.header("📱 Exemplos em cURL")
    
    # Health check
    st.subheader("1. Health Check")
    
    st.code("""
# Verificar status da API
curl -X GET http://localhost:8000/health \\
  -H "Accept: application/json"
    """, language="bash")
    
    # Cálculo de risco
    st.subheader("2. Cálculo de Risco Individual")
    
    st.code("""
# Calcular risco para uma apólice
curl -X POST http://localhost:8000/api/v1/risk/calculate \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json" \\
  -d '{
    "numero_apolice": "POL-2025-001234",
    "segurado": "João da Silva",
    "cep": "01234567",
    "valor_segurado": 350000.00,
    "tipo_residencia": "Casa",
    "data_inicio": "2025-01-15"
  }'
    """, language="bash")
    
    # Cálculo em lote
    st.subheader("3. Cálculo de Risco em Lote")
    
    st.code("""
# Calcular risco para múltiplas apólices
curl -X POST http://localhost:8000/api/v1/risk/calculate-batch \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json" \\
  -d '{
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
  }'
    """, language="bash")
    
    # Listar apólices
    st.subheader("4. Gestão de Apólices")
    
    st.code("""
# Listar todas as apólices
curl -X GET "http://localhost:8000/api/v1/policies/" \\
  -H "Accept: application/json"

# Listar com paginação e filtros
curl -X GET "http://localhost:8000/api/v1/policies/?skip=0&limit=10&nivel_risco=ALTO" \\
  -H "Accept: application/json"

# Buscar apólice específica
curl -X GET "http://localhost:8000/api/v1/policies/POL-2025-001234" \\
  -H "Accept: application/json"

# Ranking por risco
curl -X GET "http://localhost:8000/api/v1/policies/rankings/risk?order=desc&limit=10" \\
  -H "Accept: application/json"

# Estatísticas das apólices
curl -X GET "http://localhost:8000/api/v1/policies/stats/summary" \\
  -H "Accept: application/json"

# Deletar apólice
curl -X DELETE "http://localhost:8000/api/v1/policies/POL-2025-001234" \\
  -H "Accept: application/json"
    """, language="bash")
    
    # Coberturas
    st.subheader("5. Análise de Coberturas")
    
    st.code("""
# Listar todas as coberturas
curl -X GET "http://localhost:8000/api/v1/coverages/" \\
  -H "Accept: application/json"

# Coberturas com análise de risco
curl -X GET "http://localhost:8000/api/v1/coverages/risks/list?skip=0&limit=10" \\
  -H "Accept: application/json"

# Coberturas com filtros
curl -X GET "http://localhost:8000/api/v1/coverages/risks/list?nivel_risco=ALTO&score_min=80" \\
  -H "Accept: application/json"

# Coberturas de uma apólice específica
curl -X GET "http://localhost:8000/api/v1/coverages/policy/POL-2025-001234" \\
  -H "Accept: application/json"

# Ranking de coberturas por risco
curl -X GET "http://localhost:8000/api/v1/coverages/rankings/risk?order=desc&limit=10" \\
  -H "Accept: application/json"

# Coberturas de alto risco
curl -X GET "http://localhost:8000/api/v1/coverages/risks/high-risk?threshold=75&limit=50" \\
  -H "Accept: application/json"

# Coberturas por produto
curl -X GET "http://localhost:8000/api/v1/coverages/risks/by-product/100?limit=20" \\
  -H "Accept: application/json"

# Estatísticas de coberturas
curl -X GET "http://localhost:8000/api/v1/coverages/stats/summary" \\
  -H "Accept: application/json"
    """, language="bash")


def show_powershell_examples():
    """Exemplos em PowerShell"""
    
    st.header("⚡ Exemplos em PowerShell")
    
    # Configuração inicial
    st.subheader("1. Configuração e Health Check")
    
    st.code("""
# Configuração inicial
$BaseUrl = "http://localhost:8000/api/v1"
$Headers = @{
    "Content-Type" = "application/json"
    "Accept" = "application/json"
}

# Health Check
function Test-RadarSinistroAPI {
    try {
        $healthUrl = $BaseUrl.Replace("/api/v1", "/health")
        $response = Invoke-RestMethod -Uri $healthUrl -Method GET
        Write-Host "✅ API está funcionando: $($response.status)" -ForegroundColor Green
        return $response
    }
    catch {
        Write-Host "❌ Erro na API: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

Test-RadarSinistroAPI
    """, language="powershell")
    
    # Cálculo de risco
    st.subheader("2. Cálculo de Risco")
    
    st.code("""
# Função para calcular risco individual
function Invoke-CalculoRisco {
    param(
        [string]$NumeroApolice,
        [string]$Segurado,
        [string]$CEP,
        [double]$ValorSegurado,
        [string]$TipoResidencia,
        [string]$DataInicio
    )
    
    $body = @{
        numero_apolice = $NumeroApolice
        segurado = $Segurado
        cep = $CEP
        valor_segurado = $ValorSegurado
        tipo_residencia = $TipoResidencia
        data_inicio = $DataInicio
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/risk/calculate" -Method POST -Headers $Headers -Body $body
        
        Write-Host "=== RESULTADO DO CÁLCULO ===" -ForegroundColor Yellow
        Write-Host "Apólice: $($response.data.numero_apolice)" -ForegroundColor Cyan
        Write-Host "Score de Risco: $($response.data.score_risco)" -ForegroundColor Cyan
        Write-Host "Nível de Risco: $($response.data.nivel_risco)" -ForegroundColor Cyan
        Write-Host "Probabilidade: $($response.data.probabilidade)" -ForegroundColor Cyan
        
        return $response
    }
    catch {
        Write-Host "❌ Erro no cálculo: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Exemplo de uso
$resultado = Invoke-CalculoRisco -NumeroApolice "POL-2025-001234" -Segurado "João da Silva" -CEP "01234567" -ValorSegurado 350000.00 -TipoResidencia "Casa" -DataInicio "2025-01-15"
    """, language="powershell")
    
    # Gestão de apólices
    st.subheader("3. Gestão de Apólices")
    
    st.code("""
# Listar apólices
function Get-Apolices {
    param(
        [int]$Skip = 0,
        [int]$Limit = 100,
        [string]$NivelRisco = $null,
        [string]$Segurado = $null
    )
    
    $params = @{
        skip = $Skip
        limit = $Limit
    }
    
    if ($NivelRisco) { $params.nivel_risco = $NivelRisco }
    if ($Segurado) { $params.segurado = $Segurado }
    
    $queryString = ($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "&"
    $uri = "$BaseUrl/policies/?$queryString"
    
    try {
        $response = Invoke-RestMethod -Uri $uri -Method GET -Headers $Headers
        
        Write-Host "=== LISTAGEM DE APÓLICES ===" -ForegroundColor Yellow
        Write-Host "Total encontradas: $($response.total)" -ForegroundColor Green
        Write-Host "Página: $($response.page) | Por página: $($response.per_page)" -ForegroundColor Green
        
        foreach ($apolice in $response.data) {
            Write-Host "• $($apolice.segurado) - $($apolice.numero_apolice) - Score: $($apolice.score_risco)" -ForegroundColor Cyan
        }
        
        return $response
    }
    catch {
        Write-Host "❌ Erro ao listar apólices: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Buscar apólice específica
function Get-ApoliceEspecifica {
    param([string]$NumeroApolice)
    
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/policies/$NumeroApolice" -Method GET -Headers $Headers
        
        if ($response.success) {
            $apolice = $response.data
            Write-Host "=== DETALHES DA APÓLICE ===" -ForegroundColor Yellow
            Write-Host "Número: $($apolice.numero_apolice)" -ForegroundColor Cyan
            Write-Host "Segurado: $($apolice.segurado)" -ForegroundColor Cyan
            Write-Host "CEP: $($apolice.cep)" -ForegroundColor Cyan
            Write-Host "Valor Segurado: R$ $($apolice.valor_segurado)" -ForegroundColor Cyan
            Write-Host "Score de Risco: $($apolice.score_risco)" -ForegroundColor Cyan
            Write-Host "Nível de Risco: $($apolice.nivel_risco)" -ForegroundColor Cyan
        }
        
        return $response
    }
    catch {
        Write-Host "❌ Erro ao buscar apólice: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Exemplos de uso
Get-Apolices -Limit 5 -NivelRisco "ALTO"
Get-ApoliceEspecifica -NumeroApolice "POL-2025-001234"
    """, language="powershell")
    
    # Análise de coberturas
    st.subheader("4. Análise de Coberturas")
    
    st.code("""
# Listar coberturas com análise de risco
function Get-CoberturasRisco {
    param(
        [int]$Skip = 0,
        [int]$Limit = 50,
        [string]$NivelRisco = $null,
        [double]$ScoreMin = $null,
        [double]$ScoreMax = $null
    )
    
    $params = @{
        skip = $Skip
        limit = $Limit
    }
    
    if ($NivelRisco) { $params.nivel_risco = $NivelRisco }
    if ($ScoreMin) { $params.score_min = $ScoreMin }
    if ($ScoreMax) { $params.score_max = $ScoreMax }
    
    $queryString = ($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "&"
    $uri = "$BaseUrl/coverages/risks/list?$queryString"
    
    try {
        $response = Invoke-RestMethod -Uri $uri -Method GET -Headers $Headers
        
        Write-Host "=== COBERTURAS COM ANÁLISE DE RISCO ===" -ForegroundColor Yellow
        Write-Host "Total encontradas: $($response.total)" -ForegroundColor Green
        
        foreach ($cobertura in $response.data) {
            Write-Host "• $($cobertura.nm_cobertura) - Apólice: $($cobertura.nr_apolice) - Score: $($cobertura.score_risco)" -ForegroundColor Cyan
        }
        
        return $response
    }
    catch {
        Write-Host "❌ Erro ao buscar coberturas: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Coberturas de uma apólice específica
function Get-CoberturasApolice {
    param([string]$NumeroApolice)
    
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/coverages/policy/$NumeroApolice" -Method GET -Headers $Headers
        
        if ($response.success) {
            $data = $response.data
            Write-Host "=== COBERTURAS DA APÓLICE $($data.nr_apolice) ===" -ForegroundColor Yellow
            Write-Host "Segurado: $($data.segurado)" -ForegroundColor Green
            Write-Host "Total de coberturas: $($data.total_coberturas)" -ForegroundColor Green
            Write-Host "Score médio: $($data.score_risco_medio)" -ForegroundColor Green
            Write-Host "Nível geral: $($data.nivel_risco_geral)" -ForegroundColor Green
            
            Write-Host "`nDetalhes das coberturas:" -ForegroundColor Yellow
            foreach ($cobertura in $data.coberturas) {
                Write-Host "• $($cobertura.nm_cobertura) - Score: $($cobertura.score_risco) - Nível: $($cobertura.nivel_risco)" -ForegroundColor Cyan
            }
        }
        
        return $response
    }
    catch {
        Write-Host "❌ Erro ao buscar coberturas da apólice: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Exemplos de uso
Get-CoberturasRisco -NivelRisco "ALTO" -ScoreMin 75
Get-CoberturasApolice -NumeroApolice "POL-2025-001234"
    """, language="powershell")


def show_postman_examples():
    """Exemplos para Postman"""
    
    st.header("🔧 Configuração no Postman")
    
    st.markdown("""
    Esta seção mostra como configurar e usar a **Radar Sinistro API** no Postman,
    incluindo coleções prontas e variáveis de ambiente.
    """)
    
    # Configuração de ambiente
    st.subheader("1. Configuração do Ambiente")
    
    st.markdown("**Criando um Environment no Postman:**")
    
    environment_json = {
        "name": "Radar Sinistro API",
        "values": [
            {
                "key": "base_url",
                "value": "http://localhost:8000/api/v1",
                "enabled": True
            },
            {
                "key": "health_url",
                "value": "http://localhost:8000/health",
                "enabled": True
            }
        ]
    }
    
    st.code(json.dumps(environment_json, indent=2), language="json")
    
    # Coleção do Postman
    st.subheader("2. Coleção Completa para Importar")
    
    st.markdown("**Cole este JSON no Postman (Import > Raw Text):**")
    
    postman_collection = {
        "info": {
            "name": "Radar Sinistro API",
            "description": "API para cálculo de risco de sinistros e gestão de apólices",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {
                "key": "base_url",
                "value": "http://localhost:8000/api/v1"
            }
        ],
        "item": [
            {
                "name": "Health Check",
                "request": {
                    "method": "GET",
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}/../health",
                        "host": ["{{base_url}}"],
                        "path": ["..", "health"]
                    }
                }
            },
            {
                "name": "Risk Calculation",
                "item": [
                    {
                        "name": "Calculate Individual Risk",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "numero_apolice": "POL-2025-001234",
                                    "segurado": "João da Silva",
                                    "cep": "01234567",
                                    "valor_segurado": 350000.00,
                                    "tipo_residencia": "Casa",
                                    "data_inicio": "2025-01-15"
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{base_url}}/risk/calculate",
                                "host": ["{{base_url}}"],
                                "path": ["risk", "calculate"]
                            }
                        }
                    },
                    {
                        "name": "Calculate Batch Risk",
                        "request": {
                            "method": "POST",
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
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
                                }, indent=2)
                            },
                            "url": {
                                "raw": "{{base_url}}/risk/calculate-batch",
                                "host": ["{{base_url}}"],
                                "path": ["risk", "calculate-batch"]
                            }
                        }
                    }
                ]
            },
            {
                "name": "Policy Management",
                "item": [
                    {
                        "name": "List Policies",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/policies/?skip=0&limit=10",
                                "host": ["{{base_url}}"],
                                "path": ["policies", ""],
                                "query": [
                                    {"key": "skip", "value": "0"},
                                    {"key": "limit", "value": "10"}
                                ]
                            }
                        }
                    },
                    {
                        "name": "Get Policy by Number",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/policies/POL-2025-001234",
                                "host": ["{{base_url}}"],
                                "path": ["policies", "POL-2025-001234"]
                            }
                        }
                    },
                    {
                        "name": "Risk Rankings",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/policies/rankings/risk?order=desc&limit=10",
                                "host": ["{{base_url}}"],
                                "path": ["policies", "rankings", "risk"],
                                "query": [
                                    {"key": "order", "value": "desc"},
                                    {"key": "limit", "value": "10"}
                                ]
                            }
                        }
                    }
                ]
            },
            {
                "name": "Coverage Analysis",
                "item": [
                    {
                        "name": "List All Coverages",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/coverages/",
                                "host": ["{{base_url}}"],
                                "path": ["coverages", ""]
                            }
                        }
                    },
                    {
                        "name": "Coverage Risk Analysis",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/coverages/risks/list?skip=0&limit=10",
                                "host": ["{{base_url}}"],
                                "path": ["coverages", "risks", "list"],
                                "query": [
                                    {"key": "skip", "value": "0"},
                                    {"key": "limit", "value": "10"}
                                ]
                            }
                        }
                    },
                    {
                        "name": "Policy Coverages",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/coverages/policy/POL-2025-001234",
                                "host": ["{{base_url}}"],
                                "path": ["coverages", "policy", "POL-2025-001234"]
                            }
                        }
                    },
                    {
                        "name": "High Risk Coverages",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": {
                                "raw": "{{base_url}}/coverages/risks/high-risk?threshold=75&limit=50",
                                "host": ["{{base_url}}"],
                                "path": ["coverages", "risks", "high-risk"],
                                "query": [
                                    {"key": "threshold", "value": "75"},
                                    {"key": "limit", "value": "50"}
                                ]
                            }
                        }
                    }
                ]
            }
        ]
    }
    
    st.code(json.dumps(postman_collection, indent=2), language="json")
    
    # Instruções de uso
    st.subheader("3. Como Usar no Postman")
    
    st.markdown("""
    **Passos para configurar:**
    
    1. **Importar Environment:**
       - Clique em "Import" no Postman
       - Cole o JSON do Environment acima
       - Salve como "Radar Sinistro API"
    
    2. **Importar Collection:**
       - Clique em "Import" no Postman
       - Cole o JSON da Collection acima
       - A coleção será criada com todas as requisições
    
    3. **Configurar Environment:**
       - Selecione o environment "Radar Sinistro API"
       - Verifique se a variável `base_url` está correta
    
    4. **Testar Endpoints:**
       - Comece com "Health Check" para verificar se a API está funcionando
       - Use os outros endpoints conforme necessário
       - Modifique os parâmetros e payloads conforme sua necessidade
    
    **Dicas:**
    - Use variáveis `{{base_url}}` para facilitar mudanças de ambiente
    - Salve respostas como exemplos para documentação
    - Use testes automatizados com scripts no Postman
    - Configure Pre-request Scripts para autenticação se necessário
    """)
    
    # Testes automatizados
    st.subheader("4. Scripts de Teste Automatizado")
    
    st.markdown("**Script para adicionar na aba 'Tests' das requisições:**")
    
    st.code("""
// Teste básico de status
pm.test("Status code é 200", function () {
    pm.response.to.have.status(200);
});

// Teste de tempo de resposta
pm.test("Tempo de resposta menor que 2000ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(2000);
});

// Teste de estrutura da resposta
pm.test("Resposta contém success", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('success');
});

// Teste específico para cálculo de risco
pm.test("Score de risco está no range válido", function () {
    const jsonData = pm.response.json();
    if (jsonData.success && jsonData.data && jsonData.data.score_risco) {
        pm.expect(jsonData.data.score_risco).to.be.at.least(0);
        pm.expect(jsonData.data.score_risco).to.be.at.most(100);
    }
});

// Salvar dados para próximas requisições
if (pm.response.json().success) {
    const responseData = pm.response.json().data;
    if (responseData.numero_apolice) {
        pm.environment.set("last_policy_number", responseData.numero_apolice);
    }
}
    """, language="javascript")