# 🚀 Inicializadores do Radar de Sinistro

Este diretório contém arquivos batch para facilitar a execução do sistema.

## 📁 Arquivos Disponíveis

### 1. `start_radar_sinistro.bat` (🔧 **PRINCIPAL**)
**Inicializador completo com verificações**
- ✅ Verifica se Python está instalado
- ✅ Verifica se Streamlit está disponível  
- ✅ Instala dependências automaticamente se necessário
- ✅ Verifica estrutura do projeto
- ✅ Cria diretórios necessários
- ✅ Mensagens informativas detalhadas
- ✅ Abre navegador automaticamente

**Como usar:**
```
Duplo clique no arquivo OU
start_radar_sinistro.bat
```

### 2. `run.bat` (⚡ **RÁPIDO**)
**Execução simples e direta**
- 🎯 Execução rápida sem verificações
- 🎯 Ideal quando o ambiente já está configurado
- 🎯 Mínimo de mensagens

**Como usar:**
```
Duplo clique no arquivo OU
run.bat
```

### 3. `start_advanced.bat` (🔧 **AVANÇADO**)
**Configuração customizada**
- ⚙️ Permite configurar porta, tema, logs
- ⚙️ Ideal para desenvolvimento ou testes
- ⚙️ Configurações no início do arquivo

**Como usar:**
1. Edite as configurações no início do arquivo se necessário
2. Execute: `start_advanced.bat`

## 🌐 Acesso ao Sistema

Após inicializar, o sistema estará disponível em:
- **URL Local:** http://localhost:8501
- **URL de Rede:** http://[seu-ip]:8501

## 🛑 Como Parar o Sistema

- Pressione `Ctrl + C` no terminal
- Ou feche a janela do terminal

## ❗ Resolução de Problemas

### Python não encontrado
```
❌ ERRO: Python não encontrado!
```
**Solução:** Instale Python 3.8+ de https://www.python.org/downloads/

### Dependências em falta
```
❌ Streamlit não encontrado
```
**Solução:** O instalador principal tentará instalar automaticamente. 
Se falhar, execute manualmente:
```
pip install -r requirements.txt
```

### Arquivo app.py não encontrado
```
❌ ERRO: Arquivo app.py não encontrado!
```
**Solução:** Certifique-se de estar executando o .bat no diretório correto do projeto.

### Porta já em uso
```
OSError: [Errno 98] Address already in use
```
**Solução:** 
1. Use `start_advanced.bat` e mude a porta na configuração
2. Ou feche outras instâncias do Streamlit

## 📋 Recomendações

- **Primeira execução:** Use `start_radar_sinistro.bat`
- **Uso diário:** Use `run.bat` 
- **Desenvolvimento:** Use `start_advanced.bat`

## 🎯 Funcionalidades do Sistema

Após inicializar, você terá acesso a:
- 🏠 **Dashboard Principal** - Visão geral do sistema
- 🔮 **Análise de Risco** - Avaliação individual de imóveis
- 📋 **Apólices em Risco** - Lista de apólices com dados reais
- ➕ **Gerenciar Apólices** - Inclusão e gestão de apólices
- 📊 **Estatísticas** - Métricas e relatórios do sistema
- 🌡️ **Monitoramento Climático** - Dados meteorológicos
- ⚙️ **Configurações** - Status e configuração do sistema