# 🌦️ Sistema de Radar de Risco Climático - Interface Streamlit

Interface web moderna e interativa para o Sistema de Radar de Risco Climático, construída com Streamlit.

## 🚀 Como Executar a Interface

### 1. Instalar Dependências

```bash
# Instalar as novas dependências do Streamlit
pip install -r requirements.txt
```

### 2. Executar a Aplicação

```bash
# A partir do diretório raiz do projeto
cd radar_sinistro
streamlit run streamlit_app/app.py
```

### 3. Acessar no Navegador

A aplicação será aberta automaticamente em: `http://localhost:8501`

## 📱 Funcionalidades da Interface

### 🏠 Página Principal
- **Visão geral do sistema** com navegação intuitiva
- **Inicialização automática** do banco de dados
- **Geração de dados de exemplo** para demonstração
- **Status do sistema** em tempo real

### 📊 Dashboard
- **Métricas principais** com indicadores visuais
- **Gráficos interativos** de distribuição de apólices
- **Análise temporal** de contratações e sinistros
- **Mapas geográficos** com localização das apólices
- **Estatísticas do banco** de dados

### 📤 Upload de Dados
- **Upload de arquivos CSV** com drag & drop
- **Detecção automática** de encoding
- **Validação de estrutura** de dados
- **Processamento inteligente** com relatórios de qualidade
- **Prévia dos dados** antes do processamento
- **Template CSV** para download

### ⚠️ Análise de Risco
- **Mapas interativos** com marcadores de risco
- **Heatmap regional** por CEP
- **Filtros avançados** por tipo, valor e risco
- **Simulação climática** interativa
- **Análise de correlações** entre variáveis
- **Top regiões** de maior risco

### 📈 Relatórios
- **Relatórios completos** com estatísticas detalhadas
- **Análise financeira** por tipo de residência
- **Análise temporal** de tendências
- **Análise geográfica** por região
- **Exportação** em múltiplos formatos (CSV, PDF, Excel)
- **Recomendações** baseadas nos dados

## 🎨 Design e Usabilidade

### Interface Responsiva
- **Layout adaptativo** para desktop e mobile
- **Sidebar de navegação** sempre visível
- **Cards informativos** com métricas importantes
- **Cores temáticas** para diferentes níveis de risco

### Interatividade
- **Gráficos Plotly** totalmente interativos
- **Mapas Folium** com zoom e marcadores clicáveis
- **Filtros dinâmicos** que atualizam em tempo real
- **Feedback visual** para todas as ações do usuário

### Experiência do Usuário
- **Loading spinners** para operações demoradas
- **Mensagens informativas** e de erro claras
- **Tooltips explicativos** em elementos complexos
- **Navegação intuitiva** entre páginas

## 🔧 Configuração Avançada

### Variáveis de Ambiente
Crie um arquivo `.streamlit/config.toml` para configurações personalizadas:

```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[browser]
gatherUsageStats = false
```

### Customização de Tema
A interface usa CSS customizado para:
- **Cards com bordas coloridas** por nível de risco
- **Métricas destacadas** com ícones temáticos
- **Alertas visuais** para situações críticas
- **Sidebar estilizada** com informações do sistema

## 📊 Dados e Visualizações

### Tipos de Gráficos Suportados
- **Gráficos de linha** para análise temporal
- **Gráficos de barras** para comparações
- **Gráficos de pizza** para distribuições
- **Scatter plots** para correlações
- **Mapas de calor** para densidade de dados
- **Mapas geográficos** com marcadores interativos

### Métricas Calculadas
- **Taxa de sinistralidade** por região/tipo
- **Score de risco** baseado em múltiplas variáveis
- **Distribuições estatísticas** de valores
- **Tendências temporais** de contratação
- **Correlações** entre variáveis

## 🚨 Solução de Problemas

### Erro de Importação
```bash
# Se houver erro com folium ou streamlit-folium
pip install folium streamlit-folium
```

### Erro de Codificação
```bash
# Para problemas com encoding em Windows
set PYTHONIOENCODING=utf-8
streamlit run streamlit_app/app.py
```

### Banco de Dados Não Encontrado
1. Execute a **inicialização do sistema** na página principal
2. Ou gere **dados de exemplo** para testar
3. Verifique se o arquivo `radar_climatico.db` foi criado

### Performance Lenta
- Use **filtros** para reduzir o volume de dados
- **Limite o período** de análise temporal
- **Carregue dados em lotes** menores

## 🔄 Fluxo de Trabalho Recomendado

### Para Novos Usuários
1. **Acesse a página principal** e inicialize o sistema
2. **Gere dados de exemplo** para explorar funcionalidades
3. **Explore o dashboard** para entender as métricas
4. **Teste o upload** com template CSV
5. **Analise riscos** nos mapas interativos

### Para Uso em Produção
1. **Carregue dados reais** via upload CSV
2. **Configure integrações** com APIs climáticas
3. **Analise relatórios** periódicos
4. **Monitore mapas de risco** regionalmente
5. **Exporte dados** para outros sistemas

## 🛠️ Desenvolvimento e Extensões

### Estrutura de Arquivos
```
streamlit_app/
├── app.py                    # Aplicação principal
├── pages/                    # Páginas da aplicação
│   ├── 01_📊_Dashboard.py    # Dashboard principal
│   ├── 02_📤_Upload_de_Dados.py  # Upload e processamento
│   ├── 03_⚠️_Análise_de_Risco.py  # Mapas e análise
│   └── 04_📈_Relatórios.py   # Relatórios e estatísticas
└── README.md                 # Esta documentação
```

### Adicionando Novas Páginas
1. Crie arquivo na pasta `pages/` com prefixo numérico
2. Use emoji no nome para melhor navegação
3. Importe módulos do sistema conforme necessário
4. Mantenha consistência visual com outras páginas

### Integrações Futuras
- **APIs de clima** em tempo real
- **Alertas automáticos** por email/SMS
- **Machine Learning** para previsão de riscos
- **Banco de dados** em nuvem (PostgreSQL, MongoDB)
- **Autenticação** e controle de acesso

## 📚 Documentação Adicional

- **Streamlit Docs**: https://docs.streamlit.io/
- **Plotly Python**: https://plotly.com/python/
- **Folium**: https://python-visualization.github.io/folium/
- **Pandas**: https://pandas.pydata.org/docs/

---

**Desenvolvido com ❤️ para o Hackathon da i4pro**

*Interface Streamlit - Visualização moderna e interativa de dados climáticos*