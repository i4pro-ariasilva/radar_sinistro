# Testes Automatizados - Radar de Sinistro

Este diretório contém a suite completa de testes automatizados para o projeto Radar de Sinistro.

## 📁 Estrutura dos Testes

### Arquivos de Teste

1. **`test_api.py`** - Testes para as APIs REST
   - Endpoints de cálculo de risco (`/api/v1/risk/*`)
   - Endpoints de gestão de apólices (`/api/v1/policies/*`)
   - Endpoints de coberturas (`/api/v1/coverages/*`)
   - Health checks e validações

2. **`test_web_modules.py`** - Testes para módulos da interface web
   - Funções do `policy_management.py`
   - Navegação e roteamento do `app.py`
   - Módulos de processamento de dados
   - Utilitários e formatadores

3. **`test_services.py`** - Testes para serviços da API
   - `PolicyService` - Gestão de apólices
   - `RiskService` - Cálculo de riscos
   - `CoverageService` - Gestão de coberturas
   - Integração entre serviços

4. **`test_ml_modules.py`** - Testes para Machine Learning
   - `ModelPredictor` - Predição de riscos
   - `FeatureEngineer` - Engenharia de features
   - `ModelEvaluator` - Avaliação de modelos
   - Pipeline completo de ML
   - Modelos específicos por cobertura

5. **`test_database.py`** - Testes para banco de dados
   - Conexões e schema
   - Operações CRUD
   - Integridade referencial
   - Consultas específicas de coberturas

### Arquivos de Configuração

- **`conftest.py`** - Configurações globais e fixtures
- **`__init__.py`** - Inicialização do pacote de testes
- **`run_all_tests.py`** - Script para execução completa

## 🚀 Como Executar os Testes

### Executar Todos os Testes
```bash
cd tests
python run_all_tests.py
```

### Executar Testes Específicos
```bash
# Testes de API
python -m unittest test_api.py -v

# Testes de módulos web
python -m unittest test_web_modules.py -v

# Testes de serviços
python -m unittest test_services.py -v

# Testes de ML
python -m unittest test_ml_modules.py -v

# Testes de banco de dados
python -m unittest test_database.py -v
```

### Executar Teste Individual
```bash
python -m unittest test_api.TestRiskAPI.test_calculate_risk_success -v
```

## 📊 Tipos de Teste

### 1. Testes Unitários
- Testam funções e métodos individuais
- Usam mocks para isolar dependências
- Validam lógica de negócio específica

### 2. Testes de Integração
- Testam interação entre módulos
- Verificam fluxos completos
- Validam integridade de dados

### 3. Testes de API
- Validam endpoints REST
- Testam diferentes cenários de entrada
- Verificam estrutura de respostas

### 4. Testes de Banco
- Operações CRUD
- Integridade referencial
- Performance de consultas

## 🛠️ Tecnologias Utilizadas

- **unittest** - Framework de testes padrão do Python
- **unittest.mock** - Mocking para isolamento de dependências
- **tempfile** - Bancos temporários para testes
- **sqlite3** - Testes de banco de dados
- **pandas/numpy** - Testes de processamento de dados

## 📝 Convenções de Nomenclatura

### Classes de Teste
- `TestNomeDoModulo` - Para testes de módulos específicos
- `TestNomeDoServico` - Para testes de serviços
- `TestIntegracaoXY` - Para testes de integração

### Métodos de Teste
- `test_funcionalidade_cenario` - Descrição clara do que está sendo testado
- `test_erro_handling` - Testes de tratamento de erro
- `test_validacao_dados` - Testes de validação

## 🔧 Configuração de Ambiente

### Dependências Necessárias
```bash
# Instalar dependências de teste (se necessário)
pip install pytest coverage

# Para relatórios de cobertura
coverage run -m unittest discover tests/
coverage report
coverage html
```

### Variáveis de Ambiente
```bash
# Para testes de API
export TESTING=true
export DATABASE_URL=sqlite:///test.db
```

## 📈 Cobertura de Testes

Os testes cobrem:
- ✅ APIs REST (endpoints principais)
- ✅ Lógica de negócio (cálculo de risco)
- ✅ Operações de banco (CRUD)
- ✅ Processamento de dados (ML pipeline)
- ✅ Interface web (funções principais)
- ✅ Utilitários e validadores

## 🐛 Debugging de Testes

### Executar com Verbose
```bash
python -m unittest test_api.py -v
```

### Usar pdb para Debug
```python
import pdb; pdb.set_trace()
```

### Logs de Teste
Os testes geram logs detalhados que podem ser analisados para debugging.

## 📋 Checklist de Teste

Antes de fazer commit, execute:
- [ ] `python run_all_tests.py` - Todos os testes passam
- [ ] Novos recursos têm testes correspondentes
- [ ] Testes cobrem casos de erro
- [ ] Documentação de testes atualizada
- [ ] Performance dos testes é aceitável

## 🤝 Contribuindo com Testes

### Adicionando Novos Testes
1. Identifique o módulo correto (`test_*.py`)
2. Crie classe de teste se necessário
3. Implemente métodos de teste
4. Use mocks para dependências externas
5. Documente comportamento esperado

### Boas Práticas
- Testes devem ser independentes
- Use fixtures para dados de teste
- Limpe recursos após testes
- Nomeação clara e descritiva
- Teste tanto sucesso quanto falha

## 📞 Suporte

Para dúvidas sobre os testes:
1. Verifique a documentação dos módulos
2. Execute testes individuais com verbose
3. Analise logs de erro detalhados
4. Consulte exemplos em testes existentes