# Sistema de Radar de Risco Climático

Um sistema inteligente para previsão de riscos de sinistros baseado em dados climáticos e histórico de apólices de seguro com interface web interativa.

##  Visão Geral

Este sistema integra dados de apólices de seguradoras com informações climáticas em tempo real para identificar regiões e propriedades com alto risco de sinistros, permitindo ações preventivas e melhor gestão de riscos. O sistema conta com uma interface web moderna desenvolvida em Streamlit para facilitar o uso por parte dos usuários.

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
requirements.txt**

##  Instalação e Execução

### 1. Clone ou baixe o projeto
```bash
cd radar_sinistro
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Executar Interface Web (Recomendado)

**Opção 1: Usando arquivos de inicialização (Windows)**
- Execute `start_radar_sinistro.bat` (inicialização completa com verificações)
- Execute `run.bat` (inicialização rápida)
- Execute `start_advanced.bat` (inicialização configurável)

**Opção 2: Comando direto**
```bash
streamlit run app.py
```

**Opção 3: Sistema via linha de comando**
```bash
python main.py
```

O sistema iniciará automaticamente no navegador em: http://localhost:8501

##  Interface Web - Seções do Sistema

### 📊 **Dashboard Principal**
Visão geral do sistema com estatísticas consolidadas, indicadores de performance e resumo dos riscos identificados. Apresenta métricas em tempo real e gráficos de acompanhamento.

### 🏠 **Gerenciar Apólices**
Interface para cadastro e gerenciamento de apólices de seguro. Permite criar novas apólices, editar informações existentes e visualizar detalhes completos dos contratos. Inclui cálculo automático de risco básico baseado nos dados informados.

### ⚠️ **Apólices em Risco**
Seção dedicada à análise de risco das apólices cadastradas. Utiliza o modelo de Machine Learning treinado para identificar e classificar apólices com diferentes níveis de risco (Muito Baixo, Baixo, Médio, Alto). Apresenta análises detalhadas e fatores que contribuem para o risco.

### 🌍 **Análise Geográfica**
Visualização de dados geográficos com mapas interativos mostrando a distribuição de apólices e riscos por região. Permite identificar áreas de maior concentração de riscos e padrões geográficos relevantes.

### 🌦️ **Monitoramento Climático**
Seção para acompanhamento de dados climáticos em tempo real. Integra informações meteorológicas atualizadas que influenciam no cálculo de riscos, incluindo temperatura, precipitação, vento e umidade.

### 📈 **Relatórios e Analytics**
Geração de relatórios detalhados e análises estatísticas. Oferece insights sobre tendências, performance do modelo e métricas de negócio para tomada de decisões estratégicas.

---

## Sistema de Linha de Comando (Alternativo)

### Menu Principal
Execute o script principal para acessar todas as funcionalidades:

```bash
python main.py
```


**Opções disponíveis:**

1. **Inicializar sistema completo** - Setup de banco e configurações
2. **Gerar dados de exemplo** - Criar dataset para demonstração
3. **Processar dados (Pipeline)** - Pipeline completo de limpeza
4. **Treinar modelo (Dados REAIS)** - ML com dados climáticos reais
5. **Treinar modelo (Dados SIMULADOS)** - ML com dados simulados
6. **Testar predições** - Verificar funcionamento do modelo
7. **Status do Weather Service** - Verificar integração climática
9. **Demo completo (Full Pipeline)** - Execução end-to-end
10. **Status geral do sistema** - Monitoramento completo
11. **Estatísticas do banco** - Informações do database
12. **Limpar cache climático** - Limpar cache de APIs

0 - **Sair** - Encerrar sistema

##  Arquivos de Inicialização (Windows)

O projeto inclui arquivos `.bat` para facilitar a execução:

### `start_radar_sinistro.bat` (Recomendado)
- Verificação completa do ambiente Python
- Instalação automática de dependências se necessário
- Inicialização do Streamlit com tratamento de erros
- Abertura automática do navegador

### `run.bat` 
- Inicialização rápida e direta
- Para usuários com ambiente já configurado

### `start_advanced.bat`
- Opções configuráveis de execução
- Menu interativo para diferentes modos de inicialização

*Para instruções detalhadas, consulte o arquivo `INICIALIZADORES.md`*

##  Modelos de Machine Learning Incluídos

O projeto vem com modelos pré-treinados prontos para uso:

- **radar_model.pkl**: Modelo principal XGBoost treinado
- **scaler.pkl**: Normalizador de features
- **feature_columns.pkl**: Colunas de características
- **label_encoders.pkl**: Codificadores de variáveis categóricas  
- **model_metadata.pkl**: Metadados e configurações do modelo

**Vantagem**: Não é necessário treinar o modelo novamente - o sistema funciona imediatamente após a instalação.

##  Classificação de Riscos

O sistema utiliza uma escala padronizada para classificação de riscos:

- **🔴 Alto Risco** (Score ≥ 75): Situações que requerem atenção imediata
- **🟡 Médio Risco** (Score ≥ 50): Situações que necessitam monitoramento  
- **🔵 Baixo Risco** (Score ≥ 25): Situações estáveis com risco controlado
- **🟢 Muito Baixo Risco** (Score < 25): Situações de baixíssimo risco

##  Estrutura de Dados

### Apólices
- numero_apolice: Identificador único
- cep: Localização (formato XXXXX-XXX)
- tipo_residencia: casa/apartamento/sobrado
- valor_segurado: Valor da cobertura
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
├── app.py                     # Interface web principal (Streamlit)
├── policy_management.py       # Módulo de gestão de apólices
├── main.py                    # Sistema via linha de comando
├── requirements.txt           # Dependências Python
├── start_radar_sinistro.bat   # Inicializador completo (Windows)
├── run.bat                    # Inicializador rápido (Windows)
├── start_advanced.bat         # Inicializador avançado (Windows)
├── INICIALIZADORES.md         # Guia dos inicializadores
├── database/                  # Módulo de banco de dados
│   ├── radar_sinistro.db     # Banco SQLite principal
│   ├── models.py             # Modelos de dados
│   └── crud_operations.py    # Operações CRUD
├── models/                    # Modelos de Machine Learning
│   ├── radar_model.pkl       # Modelo XGBoost treinado
│   ├── scaler.pkl           # Normalizador
│   ├── feature_columns.pkl  # Colunas de features
│   ├── label_encoders.pkl   # Codificadores
│   └── model_metadata.pkl   # Metadados
├── src/                      # Código fonte modular
│   ├── api/                 # APIs e integrações
│   ├── data_processing/     # Processamento de dados
│   ├── ml/                  # Machine Learning
│   ├── weather/             # Integração climática
│   └── ...
├── config/                   # Configurações
├── data/                     # Dados do sistema
└── frontend/                 # Assets da interface web
```

##  Dados de Exemplo

O sistema inclui gerador de dados fictícios para demonstração:

- **500 apólices** de exemplo
- **100 sinistros** históricos
- Dados geograficamente distribuídos pelo Brasil


##  Solução de Problemas

### Problemas Comuns

**Interface web não abre**
```bash
# Verificar se o Streamlit está instalado
pip install streamlit

# Verificar porta disponível
netstat -ano | findstr :8501
```

**Erro de módulos não encontrados**
```bash
# Verificar diretório e reinstalar dependências
cd radar_sinistro
pip install -r requirements.txt
```

**Banco de dados não encontrado**
- O sistema criará automaticamente o banco na primeira execução
- Use a seção "Gerenciar Apólices" para adicionar dados

**Modelo não funciona**
- Os modelos pré-treinados estão incluídos na pasta `models/`
- Caso necessário, use `python main.py` opção 4 ou 5 para retreinar

##  Suporte e Documentação

### Recursos Disponíveis
- **INICIALIZADORES.md**: Guia completo dos arquivos de inicialização
- **Logs**: Verificar arquivo `logs/radar_sistema.log` para debugging
- **Status**: Interface web mostra status do sistema em tempo real

### Tecnologias Utilizadas
- **Frontend**: Streamlit 3.0+ (Interface web moderna)
- **Backend**: Python 3.8+ 
- **Database**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **ML**: XGBoost, Scikit-learn, Pandas
- **APIs**: OpenMeteo (dados climáticos gratuitos)

---

**Sistema de Radar Climático - Prevenindo sinistros através de dados inteligentes e interface web moderna**

---

## 🔒 Bloqueio de Emissão por Região (Prefixo de CEP)

O sistema suporta bloqueio de emissão de novas apólices com base em prefixos de CEP de alto risco.

### Conceito
Uma tabela `region_blocks` armazena regras de bloqueio por prefixo (recomendado 5 dígitos). Durante a emissão (individual ou em lote), o CEP informado é normalizado e comparado contra os prefixos ativos (mais específico vence). Se bloqueado, a apólice não é criada e o usuário recebe mensagem explicativa.

### Campos Principais (`region_blocks`)
- `cep_prefix`: somente dígitos (3–8, preferencial 5)
- `blocked`: 1 bloqueado / 0 liberado
- `reason`: texto explicando o motivo (ex.: "Alto risco hídrico")
- `severity`: 1=normal, 2=alto, 3=crítico
- `scope`: escopo do bloqueio (ex.: residencial, global)
- `active`: regra ativa (permite desativar sem remover)
- `created_at/created_by`, `updated_at/updated_by`: auditoria

### Feature Flag
Ativado por variável no módulo `policy_management.py`:
```python
REGION_BLOCK_FEATURE_ENABLED = True
```
Desative (False) para ignorar completamente a checagem sem remover código.

### Prioridade de Prefixos
Se existirem bloqueios para `012` e `01234`, um CEP `01234567` usará o bloqueio de `01234` (mais específico).

### CLI para Administração
Script: `scripts/manage_blocks.py`

Exemplos:
```bash
python scripts/manage_blocks.py add --prefix 01234 --reason "Alto risco hídrico" --severity 2 --scope residencial --user admin
python scripts/manage_blocks.py list --active-only
python scripts/manage_blocks.py unblock --prefix 01234 --user admin
python scripts/manage_blocks.py deactivate --prefix 01234 --user admin
```

### Integração no Fluxo
Inserida antes do cálculo de risco e persistência em `policy_management.py`.
Se bloqueado: mensagem explícita + não salva a apólice.
Em lote: cada linha é avaliada individualmente; bloqueadas entram no relatório de falhas.

### Logs Estruturados (exemplos)
```
BLOCK_CREATE prefix=01234 id=7 severity=2 scope=residencial
BLOCK_MATCH cep=01234567 prefix=01234 severity=2
BLOCK_STATUS prefix=01234 blocked=False
```

### Futuras Extensões (Planejadas)
- Expiração (valid_until)
- Origem automática (modelo de risco) `source=auto`
- Cache em memória
- Intervalos de CEP (start_cep/end_cep)
- Geoespacial (polígonos) em banco avançado

### Boas Práticas
- Usar sempre prefixos de 5 dígitos para granularidade adequada.
- Revisar periodicamente bloqueios com severidade 3 (crítico).
- Documentar motivos de negócio no campo `reason` para auditoria.

---

## 🌦️ Status da API Climática (WeatherService)

O método `WeatherService.health_check()` agora retorna duas chaves de status para garantir compatibilidade com diferentes partes do sistema:

```json
{
   "api_status": "healthy" | "unavailable",
   "status": "healthy" | "unavailable",  // alias para compatibilidade temporária
   "cache_status": "healthy" | "error",
   "service_stats": {"cache_hits": 0, ...},
   "fallback_available": true,
   "timestamp": "2025-10-09T..."
}
```

Motivação: O `main.py` consumia `api_status`, enquanto `app.py` e `web_ml_integration.py` esperavam `health.get('status')`. Isso causava exibição de "API Indisponível" mesmo quando a API estava acessível. Foi adicionado o alias `status` sincronizado com `api_status`.

### Uso recomendado
```python
from src.weather.weather_service import WeatherService
ws = WeatherService()
health = ws.health_check()
if health['api_status'] == 'healthy':
      print("API OK")
```

### Compatibilidade
```python
if health.get('status') == 'healthy':
      # Também funciona
      ...
```

### Próximo Passo (Refatoração)
Padronizar todos os consumidores para uma única chave (`api_status`) e remover o alias para simplificar.

### Diagnóstico rápido se o dashboard mostrar "API Indisponível"
1. Imprimir `print(ws.health_check())` e verificar presença de ambas as chaves.
2. Checar logs por mensagens de erro: `Health check falhou` em `openmeteo_client`.
3. Verificar conectividade externa (firewall, rede).
4. Forçar recarregamento da página para instanciar novo `WeatherService`.

---

### Compatibilidade Legada (get_weather_data)
Foi adicionado um wrapper de compatibilidade para suportar código antigo que espera `weather_service.get_weather_data(lat, lon)` retornando objeto com atributo `.current.temperature_c`, `.current.precipitation_mm`, etc.

Implementação:
- Novo método `WeatherService.get_weather_data()` retorna `LegacyWeatherPayload`.
- Este payload expõe `.current` e também o objeto original em `.raw`.

Uso:
```python
ws = WeatherService()
wd = ws.get_weather_data(-23.55, -46.63)
print(wd.current.temperature_c)
print(wd.raw.temperature_current)  # acesso ao objeto moderno
```

Plano futuro: Migrar consumidores para `get_current_weather()` diretamente e remover o wrapper.

---



