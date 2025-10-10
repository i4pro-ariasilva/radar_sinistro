# 🚀 Como Executar a Radar Sinistro API

## ✅ STATUS: API FUNCIONANDO!

**Última atualização:** API testada e funcionando perfeitamente!

## 📋 Pré-requisitos

1. **Python 3.8+** instalado
2. **Dependências do projeto** já instaladas (pandas, numpy, streamlit, etc.)

## ⚡ Execução Rápida

### Opção 1: Script Completo (Recomendado)
Executa verificações e inicia a API:
```powershell
.\start_api.bat
```

### Opção 2: Script Simples
Para início rápido sem verificações:
```powershell
.\start_api_simple.bat
```

### Opção 3: Comando Manual
```bash
# 1. Instalar dependências da API (apenas na primeira vez)
pip install fastapi uvicorn[standard]

# 2. Navegar para o diretório do projeto
cd c:\Users\ariasilva\Documents\COPILOT\hackathon\radar_sinistro

# 3. Executar a API
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## 🌐 URLs de Acesso

Após iniciar a API, você terá acesso a:

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Documentação Swagger** | http://localhost:8000/docs | Interface interativa da API |
| **ReDoc** | http://localhost:8000/redoc | Documentação alternativa |
| **Health Check** | http://localhost:8000/health | Status da API |
| **Base URL** | http://localhost:8000/api/v1 | URL base para endpoints |

## 🧪 Teste Rápido

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Listar Apólices
```bash
curl "http://localhost:8000/api/v1/policies/?limit=5"
```

### 3. Calcular Risco
```bash
curl -X POST "http://localhost:8000/api/v1/risk/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "numero_apolice": "TEST-001",
    "segurado": "Teste User",
    "cep": "01234567",
    "valor_segurado": 250000.00,
    "tipo_residencia": "Casa",
    "data_inicio": "2025-01-15"
  }'
```

### 4. Listar Coberturas
```bash
curl "http://localhost:8000/api/v1/coverages/"
```

## 🔧 Parâmetros de Configuração

### Uvicorn Options
```bash
python -m uvicorn api.main:app \
  --reload          # Auto-reload em mudanças
  --host 0.0.0.0    # Aceitar conexões de qualquer IP
  --port 8000       # Porta da API
  --log-level info  # Nível de log
  --workers 1       # Número de workers (desenvolvimento)
```

### Para Produção
```bash
python -m uvicorn api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level warning
```

## 📊 Endpoints Disponíveis

### 🏠 Base
- `GET /` - Informações da API
- `GET /health` - Health check

### 🔄 Cálculo de Risco
- `POST /api/v1/risk/calculate` - Cálculo individual
- `POST /api/v1/risk/calculate-batch` - Cálculo em lote
- `POST /api/v1/risk/calculate-and-save` - Calcular e salvar

### 📋 Apólices
- `GET /api/v1/policies/` - Listar apólices
- `GET /api/v1/policies/{numero}` - Buscar apólice
- `GET /api/v1/policies/rankings/risk` - Ranking por risco
- `GET /api/v1/policies/rankings/value` - Ranking por valor
- `GET /api/v1/policies/stats/summary` - Estatísticas
- `DELETE /api/v1/policies/{numero}` - Deletar apólice

### 🛡️ Coberturas
- `GET /api/v1/coverages/` - Listar coberturas
- `GET /api/v1/coverages/{cd_cobertura}/{cd_produto}` - Buscar cobertura
- `GET /api/v1/coverages/risks/list` - Coberturas com risco
- `GET /api/v1/coverages/policy/{numero}` - Coberturas de apólice
- `GET /api/v1/coverages/rankings/risk` - Ranking de coberturas
- `GET /api/v1/coverages/risks/high-risk` - Alto risco
- `GET /api/v1/coverages/risks/by-product/{produto}` - Por produto
- `GET /api/v1/coverages/stats/summary` - Estatísticas

## 🐛 Solução de Problemas

### Erro: "Module not found"
```bash
# Instalar dependências
pip install fastapi uvicorn[standard]
```

### Erro: "Port already in use"
```bash
# Usar porta diferente
python -m uvicorn api.main:app --port 8001
```

### Erro: "Database locked"
```bash
# Verificar se o Streamlit está rodando na mesma base
# Parar outros processos que usam o banco
```

### Verificar processos rodando
```powershell
# Windows PowerShell
Get-Process | Where-Object { $_.ProcessName -like "python*" }

# Parar processo específico
Stop-Process -Id [PID] -Force
```

## 📱 Usando no Streamlit

A API integra perfeitamente com o sistema Streamlit:

1. **Execute o Streamlit**: `streamlit run app.py`
2. **Execute a API**: `start_api.bat` (em outro terminal)
3. **Acesse**: "📚 Documentação da API" no menu do Streamlit
4. **Teste**: Use a seção "🧪 Teste Interativo"

## 🔄 Desenvolvimento

### Hot Reload
O parâmetro `--reload` faz a API reiniciar automaticamente quando você modifica o código.

### Logs
```bash
# Ver logs detalhados
python -m uvicorn api.main:app --log-level debug

# Logs em arquivo
python -m uvicorn api.main:app --log-config logging.conf
```

### Debug
```python
# Adicionar breakpoints no código
import pdb; pdb.set_trace()

# Ou usar VS Code debugger
```

## 🎯 Exemplos Práticos

### Python Client
```python
import requests

base_url = "http://localhost:8000/api/v1"

# Listar apólices
response = requests.get(f"{base_url}/policies/?limit=10")
apolices = response.json()

# Calcular risco
data = {
    "numero_apolice": "POL-001",
    "segurado": "Test User",
    "cep": "01234567",
    "valor_segurado": 300000.0,
    "tipo_residencia": "Casa",
    "data_inicio": "2025-01-15"
}
response = requests.post(f"{base_url}/risk/calculate", json=data)
resultado = response.json()
```

### JavaScript/Node.js
```javascript
const baseUrl = 'http://localhost:8000/api/v1';

// Fetch apólices
const response = await fetch(`${baseUrl}/policies/?limit=10`);
const apolices = await response.json();

// Calcular risco
const data = {
    numero_apolice: "POL-001",
    segurado: "Test User",
    cep: "01234567",
    valor_segurado: 300000.0,
    tipo_residencia: "Casa",
    data_inicio: "2025-01-15"
};

const response = await fetch(`${baseUrl}/risk/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
});
const resultado = await response.json();
```

## 🎉 Pronto!

Agora você tem a **Radar Sinistro API** rodando e pode:

✅ Acessar a documentação interativa  
✅ Testar todos os endpoints  
✅ Integrar com outros sistemas  
✅ Calcular riscos via API  
✅ Gerenciar apólices e coberturas  

**🚀 Happy coding!**