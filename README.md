# Sistema de Radar de Risco Climático

Um sistema inteligente para previsão de riscos de sinistros baseado em dados climáticos e histórico de apólices de seguro.

## 🎯 Visão Geral

Este protótipo integra dados de apólices de seguradoras com informações climáticas em tempo real para identificar regiões e propriedades com alto risco de sinistros, permitindo ações preventivas e melhor gestão de riscos.

## 🏗️ Arquitetura do Sistema

### Componentes Principais

1. **Módulo de Processamento de Dados**
   - Limpeza e validação de dados de apólices
   - Suporte a múltiplos formatos (CSV, Excel, JSON)
   - Relatórios de qualidade de dados

2. **Módulo de Banco de Dados**
   - SQLite para desenvolvimento
   - Modelos de dados otimizados
   - Operações CRUD completas

3. **Engine de Machine Learning**
   - Modelo XGBoost para predição de riscos
   - Feature engineering automático
   - Avaliação de performance

4. **Integração Climática**
   - APIs de dados meteorológicos
   - Cache inteligente
   - Múltiplas fontes de dados

5. **Serviços de Geolocalização**
   - Conversão CEP ↔ Coordenadas
   - Cálculos de proximidade geográfica

6. **Motor de Análise de Risco**
   - Scoring em tempo real
   - Agregação de múltiplas variáveis
   - Classificação por níveis de risco

## 📋 Pré-requisitos

- **Python 3.8+**
- **Dependências listadas em `requirements.txt`**
- **Chave de API OpenWeather (opcional)**

## 🚀 Instalação e Setup

### 1. Clone ou baixe o projeto
```bash
cd radar_sinistro
```

### 2. Setup automático
```bash
python scripts/setup_environment.py
```

### 3. Setup manual (alternativo)
```bash
# Instalar dependências
pip install -r requirements.txt

# Inicializar sistema
python main.py
```

## 💻 Como Usar

### Menu Principal
Execute o script principal para acessar todas as funcionalidades:

```bash
python main.py
```

**Opções disponíveis:**
1. **Inicializar sistema completo** - Setup de banco e configurações
2. **Gerar dados de exemplo** - Criar dataset para demonstração
3. **Processar dados** - Pipeline completo de limpeza
4. **Demo completo** - Execução end-to-end
5. **Verificar qualidade** - Relatórios de validação
6. **Estatísticas do banco** - Informações do database

### Processamento de Dados

```python
from src.data_processing import PolicyDataProcessor

# Inicializar processador
processor = PolicyDataProcessor()

# Processar arquivo de apólices
df = processor.load_and_process('caminho/para/apolices.csv')

# Obter relatório de qualidade
report = processor.get_quality_report()
print(f"Taxa de sucesso: {report['taxa_sucesso']}%")
```

### Operações de Banco

```python
from database import get_database, CRUDOperations

# Conectar ao banco
db = get_database()
crud = CRUDOperations(db)

# Buscar apólices por região
apolices = crud.get_apolices_by_region(cep_prefix="01310")

# Inserir nova apólice
from database.models import Apolice
nova_apolice = Apolice(
    numero_apolice="POL123456",
    cep="01310-100",
    tipo_residencia="casa",
    valor_segurado=350000.00,
    data_contratacao=datetime.now()
)
crud.insert_apolice(nova_apolice)
```

## 📊 Estrutura de Dados

### Apólices
- `numero_apolice`: Identificador único
- `cep`: Localização (formato XXXXX-XXX)
- `tipo_residencia`: casa/apartamento/sobrado
- `valor_segurado`: Valor da cobertura
- `data_contratacao`: Data da contratação
- `latitude/longitude`: Coordenadas (opcional)

### Sinistros Históricos
- `data_sinistro`: Quando ocorreu
- `tipo_sinistro`: Enchente/Vendaval/Granizo/etc
- `valor_prejuizo`: Valor do dano
- `condicoes_climaticas`: Dados do tempo no dia

### Dados Climáticos
- `temperatura_c`: Temperatura em Celsius
- `precipitacao_mm`: Chuva em milímetros
- `vento_kmh`: Velocidade do vento
- `umidade_percent`: Umidade relativa

## 🔧 Configuração

### Arquivo `config/settings.py`
Principais configurações do sistema:

```python
# APIs externas
API_CONFIG = {
    'weather': {
        'openweather_api_key': 'sua_chave_aqui'
    }
}

# Limites de risco
RISK_CONFIG = {
    'score_thresholds': {
        'baixo': 25,
        'medio': 50, 
        'alto': 75,
        'critico': 100
    }
}
```

### Variáveis de Ambiente (.env)
```bash
OPENWEATHER_API_KEY=sua_chave_api
FLASK_ENV=development
LOG_LEVEL=INFO
```

## 📈 Pipeline de Machine Learning

### 1. Preparação dos Dados
- Limpeza automática de dados
- Feature engineering 
- Encoding de variáveis categóricas

### 2. Treinamento
- Algoritmo: XGBoost
- Validação cruzada
- Otimização de hiperparâmetros

### 3. Predição
- Score de risco (0-100)
- Classificação por níveis
- Fatores de influência

## 🌦️ Integração Climática

### APIs Suportadas
- **OpenWeatherMap**: Dados globais
- **INMET**: Dados brasileiros
- **Nominatim**: Geocoding

### Cache Inteligente
- Dados climáticos: 1 hora
- Coordenadas: 30 dias
- Fallback automático entre APIs

## 🔍 Validação e Qualidade

### Validações Automáticas
- ✅ Formato de CEP brasileiro
- ✅ Valores de seguro dentro de faixas realistas
- ✅ Datas válidas
- ✅ Tipos de residência padronizados
- ✅ Coordenadas geográficas do Brasil

### Métricas de Qualidade
- **Completude**: % de campos preenchidos
- **Validade**: % de dados válidos
- **Duplicatas**: Registros duplicados
- **Score geral**: Métrica agregada

## 📁 Estrutura do Projeto

```
radar_sinistro/
├── 📂 data/                    # Dados do sistema
│   ├── raw/                    # Dados brutos
│   ├── processed/              # Dados limpos
│   ├── cache/                  # Cache de APIs
│   └── sample/                 # Dados de exemplo
├── 📂 database/                # Módulo de banco 
│   ├── database.py            # Conexão e setup
│   ├── models.py              # Modelos de dados
│   ├── crud_operations.py     # Operações CRUD
│   └── init_db.sql           # Schema do banco
├── 📂 src/                     # Código fonte
│   ├── data_processing/       # Processamento 
│   ├── ml/                    # Machine Learning 
│   ├── weather/               # APIs climáticas 
│   ├── geo/                   # Geolocalização 
│   ├── risk/                  # Análise de risco 
│   ├── api/                   # Backend API 
│   └── viz/                   # Visualizações 
├── 📂 frontend/                # Interface web 
├── 📂 config/                  # Configurações
├── 📂 scripts/                 # Scripts utilitários
├── 📂 tests/                   # Testes automatizados
├── 📂 docs/                    # Documentação
├── main.py                    # Script principal
└── requirements.txt           # Dependências
```

## 🧪 Dados de Exemplo

O sistema inclui gerador de dados fictícios para demonstração:

- **500 apólices** de exemplo
- **100 sinistros** históricos
- **200 registros** climáticos
- Dados geograficamente distribuídos pelo Brasil

```python
# Gerar dados de exemplo
python -c "from database import SampleDataGenerator; SampleDataGenerator().generate_all_sample_data()"
```

## 🐛 Solução de Problemas

### Problemas Comuns

**Erro de importação de módulos**
```bash
# Verificar se está no diretório correto
cd radar_sinistro
python main.py
```

**Banco de dados corrompido**
```bash
# Recriar banco
rm radar_climatico.db
python main.py  # Escolher opção 1
```

**Problemas com encoding**
```python
# O sistema detecta automaticamente, mas pode forçar:
df = processor.load_and_process('arquivo.csv', encoding='utf-8')
```

## 🚀 Próximos Passos

### Funcionalidades Futuras
- 🗺️ Interface web com mapas interativos
- 📱 API REST completa
- 🚨 Sistema de alertas automáticos
- 📊 Dashboards em tempo real
- 🤖 ML mais avançado com Deep Learning

## 📞 Suporte

Para dúvidas e problemas:

1. **Logs**: Verificar arquivo `logs/radar_sistema.log`
2. **Documentação**: Consultar arquivos em `docs/`
3. **Código**: Cada módulo tem exemplos de uso

## 📄 Licença

Este é um protótipo desenvolvido para fins educacionais e demonstração.

---

**Desenvolvido com ❤️ para o Hackathon da i4pro**

*Sistema de Radar Climático - Prevenindo sinistros através de dados inteligentes*
