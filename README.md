# 🌦️ Radar de Sinistro

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io/)
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
- **🗃️ Banco de Dados SQLite**: Operações CRUD completas e persistência de dados

### 🛠️ Tecnologias Utilizadas

- **Python 3.8+** - Linguagem principal
- **Streamlit** - Interface web interativa
- **SQLite** - Banco de dados local
- **Scikit-learn** - Modelos de Machine Learning
- **OpenMeteo API** - Dados climáticos gratuitos
- **Pandas & NumPy** - Processamento de dados
- **Plotly** - Visualizações interativas

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

#### Opção 1: Usando Streamlit diretamente
```bash
streamlit run app.py
```

#### Opção 2: Usando o script batch (Windows)
```bash
start_radar_sinistro.bat
```

#### Opção 3: Executar com configurações avançadas
```bash
start_advanced.bat
```

### 4. Acesse a Aplicação
Abra seu navegador e acesse: `http://localhost:8501`

## 📱 Funcionalidades da Interface

### 🏠 Gestão de Apólices
- Cadastro individual de apólices com análise automática de risco
- Upload em lote via planilha Excel/CSV
- Busca e filtros avançados
- Atualização de análises de risco

### 🚫 Sistema de Bloqueios
- **Bloqueio por Cobertura**: Bloquear coberturas específicas por apólice
- **Bloqueio Regional**: Bloquear emissões por CEP/região
- **Visualização de Bloqueios**: Painel de controle de bloqueios ativos

### 🌡️ Monitoramento Climático
- Dados meteorológicos em tempo real por CEP
- Análise de risco climático por região
- Histórico de condições climáticas

### ⚙️ Configurações
- Parâmetros de predição personalizáveis
- Informações do sistema e versões
- Configurações de precisão e cache

## 📊 Estrutura do Projeto

```
radar_sinistro/
├── app.py                      # Aplicação principal Streamlit
├── config.py                   # Configurações do sistema
├── policy_management.py        # Gestão de apólices
├── web_ml_integration.py       # Integração com ML
├── train_coverage_models.py    # Treinamento dos modelos
├── config/                     # Configurações adicionais
├── database/                   # Módulos do banco de dados
├── src/                        # Código fonte organizado
│   ├── ml/                     # Modelos de Machine Learning
│   ├── data_processing/        # Processamento de dados
│   ├── weather/                # Serviços climáticos
│   └── viz/                    # Visualizações
├── models/                     # Modelos ML treinados
├── data/                       # Dados processados
└── requirements.txt            # Dependências Python
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto para configurações personalizadas:
```env
DATABASE_PATH=database/radar_sinistro.db
WEATHER_CACHE_TIMEOUT=3600
LOG_LEVEL=INFO
```

### Treinamento de Modelos
Para retreinar os modelos de ML:
```bash
python train_coverage_models.py
```

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para:
1. Fazer fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abrir um Pull Request

---

⚡ **Transforme dados meteorológicos em vantagem competitiva para sua seguradora!** 🌦️📊
```
streamlit run app.py
```

4. **Acesse no navegador**: http://localhost:8501

## 📋 Funcionalidades

### 🏠 Gerenciamento de Apólices
- Cadastro individual com validação de dados
- Upload em lote via CSV/Excel
- Análise automática de risco por cobertura selecionada
- Validação de dados e coordenadas geográficas

### 🎯 Modelos Específicos por Cobertura
- **Vendaval**: Análise baseada em velocidade do vento e pressão atmosférica
- **Granizo**: Predição usando diferencial de temperatura e umidade
- **Alagamento**: Modelo focado em precipitação e topografia
- **Danos Elétricos**: Análise de tempestades e descargas elétricas

### 📊 Dashboard de Risco
- Lista de apólices ordenada por nível de risco
- Filtros por tipo de imóvel, valor segurado e período
- Detalhamento individual com recomendações específicas
- Comparação entre análise padrão e ML específica

### 🌦️ Integração Climática
- Dados meteorológicos em tempo real
- Cache inteligente para otimização
- Fallback automático em caso de indisponibilidade

## 🔧 Estrutura do Projeto

```
radar_sinistro/
├── app.py                          # Interface web principal
├── policy_management.py            # Gestão de apólices
├── requirements.txt                # Dependências
├── database/                       # Banco de dados e modelos
├── src/
│   ├── ml/
│   │   └── coverage_predictors/    # Modelos específicos por cobertura
│   │       ├── danos_eletricos.py
│   │       ├── vendaval.py
│   │       ├── granizo.py
│   │       ├── alagamento.py
│   │       └── coverage_manager.py
│   ├── weather/                    # Integração climática
│   └── data_processing/            # Processamento de dados
├── models/                         # Modelos ML treinados
└── scripts/                        # Scripts utilitários
```

## 📈 Modelos de Machine Learning

### Treinamento
O sistema inclui modelos pré-treinados com performance validada:

- **Danos Elétricos**: AUC 0.861
- **Vendaval**: AUC 0.739  
- **Granizo**: AUC 0.838
- **Alagamento**: AUC 0.829

### Retreinamento
```bash
python src/ml/coverage_model_trainer.py
```

## 🎛️ Configuração

### Configuração do Sistema
```python
# policy_management.py
REGION_BLOCK_FEATURE_ENABLED = False  # Sistema de bloqueio desabilitado
```

### Banco de Dados
O SQLite é criado automaticamente na primeira execução. O sistema agora processa todas as apólices sem restrições regionais.

## 📊 Classificação de Riscos

- 🔴 **Alto Risco** (≥75): Atenção imediata necessária
- 🟡 **Médio Risco** (50-74): Monitoramento recomendado  
- 🟢 **Baixo Risco** (<50): Situação controlada

## 🔍 Dados de Entrada

### Apólices
- Número da apólice, CEP, tipo de residência
- Valor segurado, coberturas selecionadas
- Coordenadas geográficas (opcional)

### Dados Climáticos
- Temperatura, precipitação, velocidade do vento
- Pressão atmosférica, umidade relativa
- Cobertura de nuvens, índice UV


---

**Prevenindo sinistros através de análise climática inteligente** 🌦️🛡️



