# 🌦️ Radar de Sinistro

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**"Reduza sua sinistralidade em até 40% com IA que antecipa riscos climáticos antes que se tornem sinistros milionários."** 📉💰🛡️

## 📝 Sobre o Projeto

O **Radar de Sinistro** é um sistema inteligente de predição de riscos climáticos para seguradoras, desenvolvido para análise preditiva de sinistros em apólices residenciais. Utilizando Machine Learning especializado por tipo de cobertura e dados meteorológicos em tempo real, a plataforma oferece gestão inteligente de riscos com precisão preditiva.

### 🎯 Características Principais

- **🧠 Machine Learning por Cobertura**: Modelos específicos para Vendaval, Granizo, Alagamento e Danos Elétricos
- **🌦️ Dados Climáticos em Tempo Real**: Integração com API OpenMeteo
- **📊 Dashboard Interativo**: Interface web moderna desenvolvida em Streamlit
- **🛡️ Gestão de Apólices**: Sistema completo de cadastro individual e em lote
- **🚫 Bloqueios Inteligentes**: Sistema de bloqueio preventivo por cobertura e região
- **📈 Análise de Risco**: Predição de riscos com classificação automática por CEP
- **🚨 Sistema de Alertas**: Notificações automáticas para situações de risco
- **🗃️ Banco de Dados SQLite**: Operações CRUD completas e persistência de dados
- **🔗 API REST**: Endpoints completos para integração com sistemas externos

### 🛠️ Tecnologias Utilizadas

- **Python 3.8+** - Linguagem principal
- **Streamlit** - Interface web interativa
- **FastAPI** - API REST moderna e rápida
- **SQLite** - Banco de dados local
- **Scikit-learn** - Modelos de Machine Learning
- **OpenMeteo API** - Dados climáticos gratuitos
- **Pandas & NumPy** - Processamento de dados
- **Plotly** - Visualizações interativas
- **Uvicorn** - Servidor ASGI para a API

## 🚀 Instalação e Execução

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### 1. Clone o Repositório
```bash
git clone https://github.com/i4pro-ariasilva/radar_sinistro.git
cd radar_sinistro
```

### 2. Instale as Dependências
```bash
pip install -r requirements.txt
```

### 3. Execute a Aplicação

#### Interface Web (Streamlit)
```bash
streamlit run app.py
```

#### API REST (FastAPI)
```bash
# Opção 1: Script automático (Windows)
.\start_api.bat

# Opção 2: Script simples
.\start_api_simple.bat

# Opção 3: Comando direto
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Acesse as Aplicações
- **Interface Web**: `http://localhost:8501`
- **API REST**: `http://localhost:8000`
- **Documentação da API**: `http://localhost:8000/docs`

## 📱 Funcionalidades da Interface

### 🏠 Apólices em Risco
- Dashboard principal com análise de risco em tempo real
- Lista ordenada por nível de risco (Alto/Médio/Baixo)
- Filtros por tipo de imóvel, valor segurado e coberturas
- Detalhamento individual com recomendações específicas

### ➕ Gerenciar Apólices
- Cadastro individual de apólices com análise automática de risco
- Upload em lote via planilha Excel/CSV
- Busca e filtros avançados
- Atualização e edição de apólices existentes

### 🚨 Gerenciamento de Alertas
- Sistema de notificações automáticas
- Configuração de alertas por nível de risco
- Histórico de alertas enviados
- Templates de notificação personalizáveis

### 🚫 Gerenciamento de Bloqueios
- **Bloqueio por Cobertura**: Bloquear coberturas específicas por apólice
- **Bloqueio Regional**: Bloquear emissões por CEP/região
- **Visualização de Bloqueios**: Painel de controle de bloqueios ativos
- **Gestão de Exceções**: Sistema de exceções para casos específicos

### 📚 Documentação da API
- **Documentação Completa**: Interface interativa com todos os endpoints
- **Exemplos de Código**: Implementações em Python, JavaScript, cURL, PowerShell
- **Teste de Conectividade**: Verificação de status da API em tempo real
- **Guias de Integração**: Documentação técnica detalhada

### ⚙️ Configurações
- Parâmetros de predição personalizáveis
- Configurações de cache e performance
- Informações do sistema e versões
- Logs e monitoramento do sistema

## 📊 Estrutura do Projeto

```
radar_sinistro/
├── app.py                      # Interface web principal (Streamlit)
├── policy_management.py        # Gestão de apólices
├── config.py                   # Configurações do sistema
├── requirements.txt            # Dependências Python
├── requirements_api.txt        # Dependências específicas da API
├── start_api.bat              # Script de inicialização da API
├── start_api_simple.bat       # Script simples da API
├── api/                       # Sistema de API REST
│   ├── main.py               # Aplicação FastAPI principal
│   ├── models/               # Modelos Pydantic
│   ├── routes/               # Endpoints da API
│   └── services/             # Lógica de negócio
├── pages/                     # Páginas da documentação da API
│   ├── api_documentation.py  # Documentação interativa
│   └── api_code_examples.py  # Exemplos de código
├── database/                  # Módulos do banco de dados
│   ├── models.py             # Modelos SQLAlchemy
│   ├── crud_operations.py    # Operações CRUD
│   ├── database.py           # Configuração do banco
│   └── radar_sinistro.db     # Banco SQLite
├── src/                       # Código fonte organizado
│   ├── ml/                   # Modelos de Machine Learning
│   │   └── coverage_predictors/  # Preditores por cobertura
│   ├── data_processing/      # Processamento de dados
│   ├── weather/              # Serviços climáticos
│   └── viz/                  # Visualizações
├── models/                    # Modelos ML treinados (*.pkl)
├── data/                      # Dados do sistema
│   ├── sample/               # Dados de amostra
│   └── training/             # Dados de treinamento
├── docs/                      # Documentação técnica
├── scripts/                   # Scripts utilitários
└── config/                    # Configurações adicionais
```

## 🔗 API REST

### Endpoints Principais

#### 📋 Coberturas
- `GET /api/v1/coverages/` - Lista todas as análises de cobertura
- `GET /api/v1/coverages/search` - Busca com filtros avançados
- `GET /api/v1/coverages/ranking` - Ranking por risco
- `GET /api/v1/coverages/statistics` - Estatísticas gerais

#### 🏠 Apólices
- `GET /api/v1/policies/` - Lista todas as apólices
- `POST /api/v1/policies/` - Cria nova apólice
- `GET /api/v1/policies/{id}` - Detalhes da apólice
- `PUT /api/v1/policies/{id}` - Atualiza apólice

#### 📊 Análise de Risco
- `GET /api/v1/risk/analysis` - Análise de risco por região
- `GET /api/v1/risk/predictions` - Predições ML

### Documentação da API
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`
## 🧠 Modelos de Machine Learning

### Preditores por Cobertura
O sistema utiliza modelos específicos para cada tipo de cobertura:

#### 🌪️ Vendaval
- **Precisão**: AUC 0.739
- **Características**: Velocidade do vento, pressão atmosférica, rajadas
- **Modelo**: `models/vendaval_model.pkl`

#### ⚡ Danos Elétricos  
- **Precisão**: AUC 0.861
- **Características**: Tempestades, descargas elétricas, umidade
- **Modelo**: `models/danos elétricos_model.pkl`

#### 🧊 Granizo
- **Precisão**: AUC 0.838
- **Características**: Diferencial de temperatura, convecção
- **Modelo**: `models/granizo_model.pkl`

#### 🌊 Alagamento
- **Precisão**: AUC 0.829
- **Características**: Precipitação, topografia, saturação do solo
- **Modelo**: `models/alagamento_model.pkl`

### Treinamento dos Modelos
```bash
# Retreinar todos os modelos
python train_coverage_models.py

# Treinar modelo específico
python src/ml/coverage_model_trainer.py --coverage vendaval
```

## 📈 Classificação de Riscos

### Níveis de Risco
- 🔴 **Alto Risco** (≥75): Atenção imediata necessária
- 🟡 **Médio Risco** (50-74): Monitoramento recomendado  
- 🟢 **Baixo Risco** (<50): Situação controlada

### Fatores de Análise
- **Dados Climáticos**: Condições meteorológicas atuais e previsões
- **Características do Imóvel**: Tipo, localização, valor segurado
- **Histórico Regional**: Padrões de sinistralidade por CEP
- **Modelos ML**: Predições específicas por cobertura

## 🔧 Configuração Avançada

### Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto para configurações personalizadas:
```env
DATABASE_PATH=database/radar_sinistro.db
WEATHER_CACHE_TIMEOUT=3600
LOG_LEVEL=INFO
API_PORT=8000
WEB_PORT=8501
```

### Configurações do Sistema
```python
# config.py
WEATHER_CACHE_TIMEOUT = 3600  # Cache de dados climáticos (segundos)
DEFAULT_RISK_THRESHOLD = 50   # Limite padrão de risco
ML_PREDICTION_ENABLED = True  # Ativar predições ML
```

### Configurações da API
```python
# api/main.py
API_VERSION = "v1"
API_PREFIX = "/api/v1"
CORS_ORIGINS = ["http://localhost:8501"]  # Permitir acesso do Streamlit
```

## 🔍 Dados de Entrada

### Estrutura de Apólices
```json
{
  "numero_apolice": "12345",
  "cep": "01310-100",
  "tipo_residencia": "Casa",
  "valor_segurado": 500000.00,
  "coberturas": ["vendaval", "granizo"],
  "coordenadas": {
    "latitude": -23.5505,
    "longitude": -46.6333
  }
}
```

### Dados Climáticos Coletados
- **Temperatura**: Atual, máxima, mínima
- **Precipitação**: Acumulada, intensidade
- **Vento**: Velocidade, direção, rajadas
- **Pressão Atmosférica**: hPa
- **Umidade Relativa**: %
- **Cobertura de Nuvens**: %
- **Índice UV**: Intensidade

## 🚀 Exemplos de Uso

### Interface Web
1. Acesse `http://localhost:8501`
2. Navegue pelas seções do menu lateral
3. Cadastre apólices ou faça upload em lote
4. Monitore riscos no dashboard principal

### API REST
```python
import requests

# Listar coberturas com risco alto
response = requests.get(
    "http://localhost:8000/api/v1/coverages/",
    params={"risk_level": "alto", "limit": 10}
)
coverages = response.json()

# Buscar apólices por CEP
response = requests.get(
    "http://localhost:8000/api/v1/policies/",
    params={"cep": "01310-100"}
)
policies = response.json()
```

### Integração com Sistemas Externos
```javascript
// JavaScript/Node.js
const axios = require('axios');

async function getCoverageAnalysis(policyId) {
    try {
        const response = await axios.get(
            `http://localhost:8000/api/v1/coverages/search`,
            { params: { numero_apolice: policyId } }
        );
        return response.data;
    } catch (error) {
        console.error('Erro na análise:', error);
    }
}
```

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para:

1. **Fork do projeto**
2. **Criar uma branch para sua feature**
   ```bash
   git checkout -b feature/MinhaFeature
   ```
3. **Commit suas mudanças**
   ```bash
   git commit -m 'feat: Adiciona nova funcionalidade'
   ```
4. **Push para a branch**
   ```bash
   git push origin feature/MinhaFeature
   ```
5. **Abrir um Pull Request**

### Estrutura de Commits
Utilize o padrão [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Documentação
- `style:` Formatação
- `refactor:` Refatoração
- `test:` Testes

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

- **Email**: ariasilva@i4pro.com.br
- **GitHub Issues**: [Reportar Problemas](https://github.com/i4pro-ariasilva/radar_sinistro/issues)
- **Documentação**: Disponível na interface web

---

## � Principais Benefícios

✅ **Redução de Sinistralidade**: Predição antecipada de riscos  
✅ **Automação Inteligente**: Bloqueios e alertas automáticos  
✅ **Interface Moderna**: Dashboard intuitivo e responsivo  
✅ **API Completa**: Integração fácil com sistemas existentes  
✅ **Modelos Específicos**: ML otimizado por tipo de cobertura  
✅ **Dados em Tempo Real**: Informações climáticas atualizadas  

⚡ **Transforme dados meteorológicos em vantagem competitiva para sua seguradora!** 🌦️📊

---

<div align="center">

**🌦️ Radar de Sinistro v3.0** | *Sistema Inteligente de Predição de Riscos Climáticos*

*Desenvolvido com ❤️ para o futuro das seguradoras*

</div>



