# 📋 API de Coberturas - Radar de Sinistro

## 🚀 Novas Rotas Implementadas

A API do Radar de Sinistro foi estendida com funcionalidades completas para gestão e análise de coberturas. Todas as rotas estão disponíveis sob o prefixo `/api/v1/coverages`.

---

## 📊 Endpoints Disponíveis

### 1. **Lista Todas as Coberturas**
```
GET /api/v1/coverages/
```
**Descrição:** Lista todas as coberturas disponíveis no sistema
**Resposta:** Lista de coberturas com código, nome e tipo (básica/adicional)

---

### 2. **Busca Cobertura Específica**
```
GET /api/v1/coverages/{cd_cobertura}/{cd_produto}
```
**Parâmetros:**
- `cd_cobertura`: Código da cobertura
- `cd_produto`: Código do produto

**Exemplo:** `/api/v1/coverages/101/1`

---

### 3. **Lista Coberturas com Análise de Risco**
```
GET /api/v1/coverages/risks/list
```
**Query Parameters:**
- `skip`: Paginação (padrão: 0)
- `limit`: Máximo de resultados (padrão: 100, máx: 1000)
- `nivel_risco`: Filtrar por nível (BAIXO, MÉDIO, ALTO, CRÍTICO)
- `cd_produto`: Filtrar por produto
- `nr_apolice`: Filtrar por apólice (busca parcial)
- `score_min`: Score mínimo (0-100)
- `score_max`: Score máximo (0-100)

**Exemplo:** `/api/v1/coverages/risks/list?nivel_risco=ALTO&limit=50`

---

### 4. **Coberturas de uma Apólice**
```
GET /api/v1/coverages/policy/{nr_apolice}
```
**Descrição:** Busca todas as coberturas de uma apólice específica com dados de risco
**Retorna:** Coberturas, score médio, nível de risco geral e estatísticas

**Exemplo:** `/api/v1/coverages/policy/POL-2025-001234`

---

### 5. **Ranking de Coberturas por Risco**
```
GET /api/v1/coverages/rankings/risk
```
**Query Parameters:**
- `order`: asc ou desc (padrão: desc)
- `limit`: Número de resultados (padrão: 50, máx: 500)

**Exemplo:** `/api/v1/coverages/rankings/risk?order=desc&limit=20`

---

### 6. **Estatísticas de Coberturas**
```
GET /api/v1/coverages/stats/summary
```
**Descrição:** Estatísticas completas das coberturas incluindo:
- Total de coberturas cadastradas
- Coberturas com análise de risco
- Distribuição por nível de risco
- Estatísticas de score (média, mín, máx)
- Top coberturas com maior risco

---

### 7. **Coberturas com Alto Risco**
```
GET /api/v1/coverages/risks/high-risk
```
**Query Parameters:**
- `threshold`: Score mínimo para alto risco (padrão: 75)
- `limit`: Máximo de resultados (padrão: 100)

**Exemplo:** `/api/v1/coverages/risks/high-risk?threshold=80&limit=50`

---

### 8. **Coberturas por Produto**
```
GET /api/v1/coverages/risks/by-product/{cd_produto}
```
**Descrição:** Lista coberturas com análise de risco para um produto específico
**Exemplo:** `/api/v1/coverages/risks/by-product/1`

---

## 📋 Modelos de Dados

### CoberturaInfo
```json
{
  "cd_cobertura": 101,
  "cd_produto": 1,
  "nm_cobertura": "Vendaval",
  "dv_basica": true,
  "created_at": "2025-01-01T10:00:00"
}
```

### CoberturaRiscoInfo
```json
{
  "id": 1,
  "nr_apolice": "POL-2025-001234",
  "cd_cobertura": 101,
  "cd_produto": 1,
  "nm_cobertura": "Vendaval",
  "dv_basica": true,
  "score_risco": 75.5,
  "nivel_risco": "ALTO",
  "probabilidade": 0.755,
  "modelo_usado": "RandomForest_v2.1",
  "versao_modelo": "2.1.0",
  "fatores_risco": "{\"clima\": 0.6, \"localizacao\": 0.4}",
  "confianca_modelo": 0.89,
  "data_calculo": "2025-01-15T14:30:00",
  "tempo_processamento_ms": 150
}
```

### ApoliceCoberturasInfo
```json
{
  "nr_apolice": "POL-2025-001234",
  "segurado": "João Silva",
  "coberturas": [...],
  "total_coberturas": 5,
  "score_risco_medio": 68.5,
  "nivel_risco_geral": "MÉDIO"
}
```

---

## 🔧 Exemplos de Uso

### Buscar coberturas com alto risco
```bash
curl "http://localhost:8000/api/v1/coverages/risks/high-risk?threshold=75"
```

### Listar coberturas de uma apólice
```bash
curl "http://localhost:8000/api/v1/coverages/policy/POL-2025-001234"
```

### Ranking das 10 coberturas com maior risco
```bash
curl "http://localhost:8000/api/v1/coverages/rankings/risk?limit=10"
```

### Filtrar coberturas por produto e nível de risco
```bash
curl "http://localhost:8000/api/v1/coverages/risks/list?cd_produto=1&nivel_risco=ALTO&limit=20"
```

---

## 📈 Casos de Uso

1. **Monitoramento de Risco por Cobertura**
   - Identificar coberturas com maior exposição ao risco
   - Acompanhar evolução dos scores de risco

2. **Análise por Produto**
   - Comparar perfil de risco entre diferentes produtos
   - Identificar produtos que precisam de revisão

3. **Gestão de Portfólio**
   - Visualizar distribuição de risco por cobertura
   - Tomar decisões de subscrição baseadas em dados

4. **Relatórios Gerenciais**
   - Estatísticas agregadas por cobertura
   - Rankings para tomada de decisão

---

## 🌐 Acesso à Documentação

A documentação interativa está disponível em:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## ✅ Status da Implementação

- [x] Modelos de dados para coberturas
- [x] Serviço de coberturas (CoverageService)
- [x] Rotas completas da API
- [x] Integração com banco de dados existente
- [x] Paginação e filtros avançados
- [x] Rankings e estatísticas
- [x] Documentação da API
- [x] Testes básicos de funcionamento

**🎯 A API está pronta para uso em produção!**