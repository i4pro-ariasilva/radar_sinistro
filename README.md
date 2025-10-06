# Sistema de Radar de Risco Climático

Um sistema inteligente para previsão de riscos de sinistros baseado em dados climáticos e histórico de apólices de seguro.

##  Visão Geral

Este sistema integra dados de apólices de seguradoras com informações climáticas em tempo real para identificar regiões e propriedades com alto risco de sinistros, permitindo ações preventivas e melhor gestão de riscos.

##  Arquitetura do Sistema

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
   - API OpenMeteo (gratuita)
   - Cache inteligente
   - Dados meteorológicos em tempo real

##  Pré-requisitos

- **Python 3.8+**
- **Dependências listadas em 
equirements.txt**

##  Instalação e Setup

### 1. Clone ou baixe o projeto
```bash
cd radar_sinistro
````

### 2. Instalar dependências
```bash
pip install -r requirements.txt
````

### 3. Executar sistema
```bash
python main.py
````

##  Como Usar

### Menu Principal
Execute o script principal para acessar todas as funcionalidades:

```bash
python main.py
````

**Opções disponíveis:**
1. **Inicializar sistema completo** - Setup de banco e configurações
2. **Gerar dados de exemplo** - Criar dataset para demonstração
3. **Processar dados** - Pipeline completo de limpeza
4. **Treinar modelo ML** - Machine Learning com dados reais/simulados
5. **Testar predições** - Verificar funcionamento do modelo
6. **Status do Weather Service** - Verificar integração climática
7. **Demo completo** - Execução end-to-end
8. **Estatísticas do banco** - Informações do database

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

##  Estrutura de Dados

### Apólices
- numero_apolice: Identificador único
- cep: Localização (formato XXXXX-XXX)
- 	ipo_residencia: casa/apartamento/sobrado
- alor_segurado: Valor da cobertura
- data_contratacao: Data da contratação

### Dados Climáticos
- temperatura_c: Temperatura em Celsius
- precipitacao_mm: Chuva em milímetros
- vento_kmh: Velocidade do vento
- umidade_percent: Umidade relativa

##  Configuração

### Arquivo config/settings.py
Principais configurações do sistema já estão pré-definidas para funcionamento imediato.

##  Pipeline de Machine Learning

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

##  Integração Climática

### API Utilizada
- **OpenMeteo**: Dados globais gratuitos (sem necessidade de API key)

### Cache Inteligente
- Dados climáticos: 1 hora
- Fallback automático

##  Estrutura do Projeto

```
radar_sinistro/
  data/                    # Dados do sistema
  database/                # Módulo de banco
  src/                     # Código fonte
  config/                  # Configurações
  logs/                    # Logs do sistema
 main.py                     # Script principal
 requirements.txt            # Dependências
```

##  Dados de Exemplo

O sistema inclui gerador de dados fictícios para demonstração:

- **500 apólices** de exemplo
- **100 sinistros** históricos
- Dados geograficamente distribuídos pelo Brasil

##  Solução de Problemas

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
rm *.db
python main.py  # Escolher opção 1
```

##  Suporte

Para dúvidas e problemas:

1. **Logs**: Verificar arquivo logs/radar_sistema.log
2. **Teste**: Executar python main.py e escolher opção de status

---

**Sistema de Radar Climático - Prevenindo sinistros através de dados inteligentes**

