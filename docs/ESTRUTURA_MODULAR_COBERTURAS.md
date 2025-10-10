# 📋 ESTRUTURA MODULAR DE MODELOS DE COBERTURA

## 🎯 Objetivo
Reestruturação do sistema de predição de risco por cobertura, criando um arquivo específico para cada tipo de cobertura, facilitando manutenção e permitindo especialização de cada modelo.

## 📁 Nova Estrutura de Arquivos

```
src/ml/coverage_predictors/
├── __init__.py                 # Imports principais do módulo
├── base_predictor.py           # Classe base abstrata
├── danos_eletricos.py          # Modelo específico para Danos Elétricos
├── vendaval.py                 # Modelo específico para Vendaval
├── granizo.py                  # Modelo específico para Granizo
├── alagamento.py               # Modelo específico para Alagamento
└── coverage_manager.py         # Gerenciador central
```

## 🏗️ Arquitetura dos Modelos

### 1. **Base Predictor** (`base_predictor.py`)
- Classe abstrata `CoverageSpecificPredictor`
- Funcionalidades comuns:
  - Obtenção de dados climáticos
  - Extração de features da propriedade
  - Preparação de features
  - Predição com fallback heurístico
  - Salvamento/carregamento de modelos

### 2. **Modelos Específicos**
Cada modelo implementa:
- `get_climate_features()`: Features climáticas relevantes
- `get_property_features()`: Features da propriedade relevantes  
- `calculate_risk_score()`: Cálculo de risco específico
- `get_specific_recommendations()`: Recomendações específicas
- `calculate_seasonal_adjustment()`: Ajuste sazonal

#### **Danos Elétricos** (`danos_eletricos.py`)
- **Fatores principais**: Tempestades, raios, instalações antigas
- **Features climáticas**: Velocidade vento, índice UV, pressão atmosférica
- **Características**: Foco em instabilidade elétrica e idade do imóvel

#### **Vendaval** (`vendaval.py`)
- **Fatores principais**: Velocidade vento, gradientes de pressão
- **Features climáticas**: Vento, pressão atmosférica, diferencial térmico
- **Características**: Análise de sistemas meteorológicos e exposição

#### **Granizo** (`granizo.py`)
- **Fatores principais**: Instabilidade atmosférica, correntes ascendentes
- **Features climáticas**: Diferencial temperatura, umidade, horário
- **Características**: Foco em condições convectivas e sazonalidade

#### **Alagamento** (`alagamento.py`)
- **Fatores principais**: Precipitação, drenagem urbana, topografia
- **Features climáticas**: Precipitação, umidade, sistemas estacionários
- **Características**: Análise de infraestrutura urbana e CEP

### 3. **Coverage Manager** (`coverage_manager.py`)
Gerenciador central que oferece:
- Análise de múltiplas coberturas
- Comparação entre coberturas
- Alertas baseados no clima
- Análise em lote de apólices
- Resumos de portfólio

## 🔧 Funcionalidades Implementadas

### **Análise Individual**
```python
from src.ml.coverage_predictors import DanosEletricosPredictor

predictor = DanosEletricosPredictor()
result = predictor.predict_risk(policy_data)
```

### **Análise Consolidada**
```python
from src.ml.coverage_predictors import CoverageRiskManager

manager = CoverageRiskManager()
analysis = manager.analyze_all_coverages(policy_data)
```

### **Análise Seletiva**
```python
analysis = manager.analyze_all_coverages(
    policy_data, 
    selected_coverages=['vendaval', 'granizo']
)
```

### **Comparação de Coberturas**
```python
comparison = manager.get_coverage_comparison(
    policy_data, 
    ['danos_eletricos', 'alagamento']
)
```

### **Alertas Climáticos**
```python
alerts = manager.get_weather_based_alerts(
    policy_data, 
    alert_threshold=0.7
)
```

### **Análise em Lote**
```python
batch_result = manager.batch_analyze_policies(policies_list)
```

## 📊 Dados de Entrada

### **Policy Data**
```python
policy_data = {
    'numero_apolice': 'POL-2024-001',
    'cep': '01234567',
    'tipo_residencia': 'casa',
    'valor_segurado': 250000,
    'latitude': -23.5505,  # Opcional
    'longitude': -46.6333,  # Opcional
    'ano_construcao': 1995   # Opcional
}
```

## 📈 Saída dos Modelos

### **Resultado Individual**
```python
{
    'coverage': 'Danos Elétricos',
    'probability': 0.55,
    'risk_score': 55.0,
    'risk_level': 'medio',
    'model_prediction': None,  # Se não há modelo treinado
    'heuristic_score': 0.55,
    'main_factors': [
        {'feature': 'velocidade_vento', 'value': 15, 'importance': 0.25},
        {'feature': 'idade_imovel', 'value': 25, 'importance': 0.12}
    ],
    'specific_recommendations': [
        "⚡ Instalar protetor contra surtos elétricos",
        "🔌 Verificar condições da instalação elétrica"
    ]
}
```

### **Resultado Consolidado**
```python
{
    'policy_info': {...},
    'coverage_analysis': {
        'danos_eletricos': {...},
        'vendaval': {...},
        'granizo': {...},
        'alagamento': {...}
    },
    'summary': {
        'overall_risk_level': 'medio',
        'average_risk_score': 67.8,
        'highest_risk_coverage': {
            'name': 'Granizo',
            'score': 100.0,
            'level': 'alto'
        },
        'risk_distribution': {...}
    },
    'recommendations': [...]
}
```

## 🔄 Integração com Sistema

### **Policy Management**
- Import já atualizado em `policy_management.py`
- Função `calculate_coverage_specific_risk()` implementada
- Nova aba "Análise Climática Avançada" na interface

### **Uso no Streamlit**
```python
from src.ml.coverage_predictors import CoverageRiskManager

manager = CoverageRiskManager()
coverage_analysis = manager.analyze_all_coverages(policy_data, selected_coverages)
```

## ✅ Validação

- **Testes individuais**: ✅ Todos os modelos funcionando
- **Gerenciador**: ✅ Análises consolidadas funcionando
- **Análise em lote**: ✅ Processamento de múltiplas apólices
- **Integração**: ✅ Import no policy_management.py bem-sucedido
- **Sistema heurístico**: ✅ Fallback funcionando quando modelo não existe

## 🚀 Próximos Passos

1. **Treinamento de modelos reais** com dados históricos
2. **Calibração de thresholds** por região
3. **Implementação de alertas em tempo real**
4. **Dashboard específico** para análise de coberturas
5. **API endpoints** para análise remota

## 📝 Notas Técnicas

- Todos os modelos usam predição heurística como fallback
- Sistema de logging implementado para debug
- Estrutura preparada para modelos ML reais (sklearn/tensorflow)
- Ajustes sazonais implementados por cobertura
- Recomendações específicas por tipo de risco