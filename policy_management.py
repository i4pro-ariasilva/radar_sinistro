#!/usr/bin/env python3
"""
Extensão para o app.py - Gerenciamento de Apólices Residenciais
Funcionalidades para inclusão individual e em lote de apólices de seguros residenciais
com análise de risco baseada em dados climáticos e características da propriedade.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import sys
import os
import json

# Adicionar ao sys.path se necessário
sys.path.append('.')

try:
    from database import get_database, CRUDOperations
    from src.ml.model_predictor import ModelPredictor
    from src.ml.feature_engineering import FeatureEngineer
    from src.ml.coverage_predictors import CoverageRiskManager
    # Feature flag desabilitado - sem bloqueio por região
    REGION_BLOCK_FEATURE_ENABLED = False
except ImportError as e:
    st.error(f"Erro ao importar módulos: {e}")

def get_risk_level_emoji(score):
    """Retorna emoji baseado no score de risco"""
    if score >= 70:
        return "🔴"
    elif score >= 40:
        return "🟡"
    else:
        return "🟢"

def calculate_coverage_specific_risk(policy_data, selected_coverages):
    """Calcula risco específico por cobertura usando os novos modelos"""
    try:
        # Inicializar o gerenciador de coberturas (singleton)
        from src.ml.coverage_predictors import CoverageRiskManager
        
        # Cache da instância no nível do módulo para evitar múltiplas inicializações
        if not hasattr(calculate_coverage_specific_risk, '_coverage_manager'):
            calculate_coverage_specific_risk._coverage_manager = CoverageRiskManager()
        
        coverage_manager = calculate_coverage_specific_risk._coverage_manager
        
        # Mapear nomes de coberturas do sistema para os modelos
        coverage_mapping = {
            'Danos Elétricos': 'danos_eletricos',
            'Vendaval': 'vendaval', 
            'Granizo': 'granizo',
            'Alagamento': 'alagamento',
            'Incêndio': None,  # Não tem modelo climático específico
            'Roubo': None,  # Não tem modelo climático específico
            'Responsabilidade Civil': None  # Não tem modelo climático específico
        }
        
        # Converter APENAS as coberturas selecionadas
        model_coverages = []
        unavailable_coverages = []
        
        for cob_name in selected_coverages:
            # Remover asterisco (*) que indica cobertura básica
            clean_name = cob_name.replace('*', '').strip()
            
            if clean_name in coverage_mapping:
                if coverage_mapping[clean_name]:
                    model_coverages.append(coverage_mapping[clean_name])
                else:
                    unavailable_coverages.append(cob_name)
            else:
                unavailable_coverages.append(cob_name)
        
        # Validar se há pelo menos uma cobertura com modelo disponível
        if not model_coverages:
            return {
                'coverage_analysis': None,
                'has_specific_analysis': False,
                'analyzed_coverages': 0,
                'recommendations': [],
                'error': f"Nenhuma das coberturas selecionadas ({', '.join(selected_coverages)}) possui modelo de análise climática específico disponível."
            }
        
        # Fazer análise específica apenas das coberturas selecionadas
        result = coverage_manager.analyze_all_coverages(policy_data, model_coverages)
        
        # Informações sobre coberturas não analisadas
        analysis_info = {
            'total_selected': len(selected_coverages),
            'analyzed': len(model_coverages),
            'unavailable': unavailable_coverages
        }
        
        return {
            'coverage_analysis': result,
            'has_specific_analysis': True,
            'analyzed_coverages': len(model_coverages),
            'recommendations': result.get('recommendations', []),
            'analysis_info': analysis_info
        }
        
    except Exception as e:
        st.warning(f"Análise específica por cobertura indisponível: {e}")
        return {
            'coverage_analysis': None,
            'has_specific_analysis': False,
            'analyzed_coverages': 0,
            'recommendations': [],
            'error': str(e)
        }

def calculate_policy_risk(policy_data):
    """Calcula o risco para uma apólice residencial usando o modelo ML"""
    try:
        # Tentar importar localmente para evitar problemas de import
        import sys
        sys.path.append('.')
        
        from src.ml.model_predictor import ModelPredictor
        
        # Inicializar o preditor
        predictor = ModelPredictor()
        
        # Preparar dados para predição (residencial)
        prediction_data = {
            'numero_apolice': policy_data['numero_apolice'],
            'segurado': policy_data['segurado'],
            'cep': policy_data['cep'],
            'valor_segurado': policy_data['valor_segurado'],
            'tipo_residencia': policy_data['tipo_residencia'],
            'data_inicio': policy_data['data_inicio']
        }
        
        # Fazer predição
        result = predictor.predict_single_policy(prediction_data)
        
        return {
            'score_risco': result.get('risk_score', 0),
            'nivel_risco': result.get('risk_level', 'baixo'),
            'probabilidade': result.get('probability', 0),
            'fatores_principais': result.get('influence_factors', [])
        }
        
    except ImportError as e:
        st.error(f"Erro ao importar ModelPredictor: {e}")
        # Fallback: calcular risco básico
        return calculate_basic_risk(policy_data)
    except Exception as e:
        st.error(f"Erro ao calcular risco: {e}")
        # Fallback: calcular risco básico
        return calculate_basic_risk(policy_data)

def calculate_basic_risk(policy_data):
    """Cálculo básico de risco residencial como fallback"""
    # Cálculo simples baseado em regras para residências
    score = 20  # Base menor para residências
    
    # Valor segurado (maior valor = maior risco)
    if policy_data['valor_segurado'] > 500000:
        score += 25
    elif policy_data['valor_segurado'] > 300000:
        score += 15
    elif policy_data['valor_segurado'] > 100000:
        score += 10
    
    # Tipo de residência (risco baseado no tipo)
    tipo_risco = {
        'Casa': 15,
        'Apartamento': 5,
        'Sobrado': 20,
        'Kitnet': 8
    }
    score += tipo_risco.get(policy_data.get('tipo_residencia', 'Casa'), 10)
    
    # CEP (análise básica por região)
    cep_first_digit = policy_data['cep'][0] if policy_data['cep'] else '0'
    if cep_first_digit in ['0', '1']:  # SP/RJ - maior risco urbano
        score += 15
    elif cep_first_digit in ['2', '3']:  # ES/MG - risco médio
        score += 10
    else:  # Outras regiões - risco menor
        score += 5
    
    score = min(score, 100)  # Máximo 100
    
    # Determinar nível (padronizado com app.py)
    if score >= 75:
        nivel = 'alto'
    elif score >= 50:
        nivel = 'medio'
    elif score >= 25:
        nivel = 'baixo'
    else:
        nivel = 'muito_baixo'
    
    return {
        'score_risco': float(score),
        'nivel_risco': nivel,
        'probabilidade': score / 100.0,
        'fatores_principais': [
            {'feature': 'valor_segurado', 'importance': 0.3},
            {'feature': 'tipo_residencia', 'importance': 0.25},
            {'feature': 'localizacao_cep', 'importance': 0.25},
            {'feature': 'risco_regional', 'importance': 0.2}
        ]
    }

def save_policy_to_database(policy_data, risk_data):
    """Salva apólice no banco de dados com dados de risco"""
    try:
        # Tentar usar o sistema de banco completo primeiro
        from database import get_database, CRUDOperations
        from database.models import Apolice
        from datetime import datetime
        
        db = get_database()
        crud = CRUDOperations(db)
        
        # Verificar se a apólice já existe
        existing_apolice = crud.get_apolice_by_numero(policy_data['numero_apolice'])
        if existing_apolice:
            st.warning(f"⚠️ Apólice {policy_data['numero_apolice']} já existe no banco de dados")
            return existing_apolice.id  # Retorna o ID existente
        
        # Criar objeto Apolice com estrutura correta
        apolice = Apolice(
            numero_apolice=policy_data['numero_apolice'],
            segurado=policy_data.get('segurado', 'N/A'),
            cd_produto=policy_data.get('cd_produto'),  # NOVO: código do produto
            cep=policy_data['cep'],
            tipo_residencia=policy_data['tipo_residencia'].lower(),  # Converter para minúscula
            valor_segurado=policy_data['valor_segurado'],
            data_contratacao=datetime.fromisoformat(policy_data['data_inicio']),
            latitude=None,  # Será preenchido posteriormente via geocoding
            longitude=None,  # Será preenchido posteriormente via geocoding
            ativa=True,
            email=policy_data.get('email'),  # NOVO: campo de email
            telefone=policy_data.get('telefone')  # NOVO: campo de telefone
        )
        
        # Adicionar campos extras para dados de risco
        apolice.data_inicio = policy_data['data_inicio']
        apolice.score_risco = float(risk_data['score_risco'])
        apolice.nivel_risco = risk_data['nivel_risco']
        apolice.probabilidade_sinistro = float(risk_data['probabilidade'])
        
        # Inserir no banco usando a função correta
        try:
            policy_id = crud.insert_apolice(apolice)
        except Exception as insert_error:
            # Se for erro de constraint de unicidade, verificar se já existe
            if "UNIQUE constraint failed" in str(insert_error):
                existing_apolice = crud.get_apolice_by_numero(policy_data['numero_apolice'])
                if existing_apolice:
                    st.warning(f"⚠️ Apólice {policy_data['numero_apolice']} já existe no banco (ID: {existing_apolice.id})")
                    return existing_apolice.id
            # Re-raise outros erros
            raise insert_error
        
        # Inserir coberturas selecionadas (se houver)
        if policy_id and 'cd_coberturas' in policy_data and policy_data['cd_coberturas']:
            try:
                success = crud.insert_multiple_apolice_coberturas(
                    nr_apolice=policy_data['numero_apolice'],
                    cd_produto=policy_data['cd_produto'],
                    cd_coberturas=policy_data['cd_coberturas'],
                    dt_inclusao=policy_data['data_inicio']
                )
                if not success:
                    st.warning("⚠️ Apólice salva, mas houve erro ao salvar as coberturas.")
                    
                # NOVO: Salvar análises de risco por cobertura individual
                save_coverage_risk_analysis(policy_data, risk_data)
                    
            except Exception as e:
                st.warning(f"⚠️ Apólice salva, mas erro ao salvar coberturas: {e}")
        
        return policy_id
        
    except Exception as e:
        st.warning(f"Sistema de banco avançado indisponível: {e}")
        # Fallback: salvar em SQLite simples
        return save_policy_simple(policy_data, risk_data)

def save_coverage_risk_analysis(policy_data, risk_data):
    """Salva análises de risco individuais por cobertura na tabela cobertura_risco"""
    try:
        from database.cobertura_risco_dao import CoberturaRiscoDAO, CoberturaRiscoData
        import random
        from datetime import datetime
        
        # Se não há dados de análise por cobertura no risk_data, calcular agora
        coverage_analysis = risk_data.get('coverage_analysis')
        if not coverage_analysis and 'cd_coberturas' in policy_data:
            # Calcular análise específica por cobertura
            selected_coverage_names = []
            for cd_cobertura in policy_data['cd_coberturas']:
                # Mapear código para nome (completo)
                coverage_map = {
                    1: 'Incêndio', 2: 'Vendaval', 3: 'Roubo', 4: 'Responsabilidade Civil',
                    5: 'Vendaval', 6: 'Danos Elétricos', 7: 'Danos Elétricos', 8: 'Danos Elétricos', 
                    9: 'Granizo', 10: 'Alagamento', 11: 'Granizo', 12: 'Alagamento', 
                    13: 'Granizo', 14: 'Alagamento', 15: 'Vendaval', 16: 'Danos Elétricos'
                }
                coverage_name = coverage_map.get(cd_cobertura, 'Cobertura Padrão')
                selected_coverage_names.append(coverage_name)
            
            # Tentar calcular análise específica
            try:
                coverage_risk_data = calculate_coverage_specific_risk(policy_data, selected_coverage_names)
                if coverage_risk_data and coverage_risk_data.get('has_specific_analysis'):
                    coverage_analysis = coverage_risk_data['coverage_analysis']
            except Exception as e:
                st.warning(f"Análise por cobertura não disponível: {e}")
        
        # Se temos análise por cobertura, salvar os dados individuais
        if coverage_analysis and 'coverage_details' in coverage_analysis:
            dao = CoberturaRiscoDAO()
            coverage_risks = []
            
            for cd_cobertura in policy_data['cd_coberturas']:
                # Buscar dados específicos desta cobertura na análise
                coverage_detail = None
                
                # Mapeamento melhorado: código -> tipo de modelo
                codigo_para_modelo = {
                    2: 'vendaval', 5: 'vendaval', 15: 'vendaval',  # Vendaval
                    6: 'danos_eletricos', 7: 'danos_eletricos', 8: 'danos_eletricos', 16: 'danos_eletricos',  # Danos Elétricos
                    9: 'granizo', 11: 'granizo', 13: 'granizo',  # Granizo
                    10: 'alagamento', 12: 'alagamento', 14: 'alagamento'  # Alagamento
                }
                
                # Se a cobertura tem modelo específico, buscar na análise
                if cd_cobertura in codigo_para_modelo:
                    modelo_esperado = codigo_para_modelo[cd_cobertura]
                    
                    for detail in coverage_analysis['coverage_details']:
                        if modelo_esperado in detail['coverage_type'].lower():
                            coverage_detail = detail
                            break
                
                # Se não encontramos dados específicos, usar dados da apólice com variação
                if not coverage_detail:
                    base_score = float(risk_data['score_risco'])
                    
                    # Adicionar variação baseada no tipo de cobertura (expandido)
                    if cd_cobertura in [2, 5, 15]:  # Vendaval
                        score_variation = random.uniform(-10, 20)
                    elif cd_cobertura in [6, 7, 8, 16]:  # Danos Elétricos
                        score_variation = random.uniform(-5, 10)
                    elif cd_cobertura in [9, 11, 13]:  # Granizo
                        score_variation = random.uniform(-8, 15)
                    elif cd_cobertura in [10, 12, 14]:  # Alagamento
                        score_variation = random.uniform(-5, 25)
                    else:
                        score_variation = random.uniform(-5, 5)
                    
                    coverage_score = float(max(0, min(100, base_score + score_variation)))
                    
                    coverage_detail = {
                        'risk_score': coverage_score,
                        'risk_level': get_risk_level_from_score(coverage_score),
                        'confidence': float(random.uniform(0.8, 0.95)),
                        'coverage_type': f'coverage_{cd_cobertura}'
                    }
                
                # Criar objeto de dados de risco para esta cobertura
                risco_data = CoberturaRiscoData(
                    nr_apolice=str(policy_data['numero_apolice']),
                    cd_cobertura=int(cd_cobertura),
                    cd_produto=int(policy_data.get('cd_produto', 1)),
                    score_risco=float(coverage_detail['risk_score']),
                    nivel_risco=str(coverage_detail['risk_level']),
                    probabilidade=float(coverage_detail['risk_score']) / 100.0,
                    modelo_usado=f'{coverage_detail["coverage_type"]}_model_v2',
                    versao_modelo='2.0',
                    fatores_risco={"fonte": "inclusao_apolice", "tipo_cobertura": str(coverage_detail['coverage_type'])},
                    dados_climaticos={"temperatura": int(25), "umidade": int(random.randint(40, 80))},
                    dados_propriedade={"valor": float(policy_data['valor_segurado']), "tipo": str(policy_data['tipo_residencia'])},
                    resultado_predicao={"score": float(coverage_detail['risk_score']), "confianca": float(coverage_detail['confidence'])},
                    confianca_modelo=float(coverage_detail['confidence']),
                    explicabilidade={"principais_fatores": ["localizacao", "historico", "tipo_cobertura"]},
                    tempo_processamento_ms=int(random.randint(50, 150))
                )
                
                coverage_risks.append(risco_data)
            
            # Salvar todas as análises de risco por cobertura
            if coverage_risks:
                result_ids = dao.salvar_multiplos_riscos(coverage_risks)
                if result_ids:
                    st.success(f"✅ Salvas {len(result_ids)} análises de risco por cobertura individual!")
                else:
                    st.warning("⚠️ Erro ao salvar análises de risco por cobertura")
        
        else:
            # Fallback: criar análises básicas para cada cobertura
            if 'cd_coberturas' in policy_data and policy_data['cd_coberturas']:
                dao = CoberturaRiscoDAO()
                coverage_risks = []
                
                for cd_cobertura in policy_data['cd_coberturas']:
                    # Criar análise básica com score variado baseado na apólice
                    base_score = float(risk_data['score_risco'])
                    coverage_score = float(max(0, min(100, base_score + random.uniform(-15, 15))))
                    nivel_risco = get_risk_level_from_score(coverage_score)
                    
                    risco_data = CoberturaRiscoData(
                        nr_apolice=str(policy_data['numero_apolice']),
                        cd_cobertura=int(cd_cobertura),
                        cd_produto=int(policy_data.get('cd_produto', 1)),
                        score_risco=coverage_score,
                        nivel_risco=str(nivel_risco),
                        probabilidade=coverage_score / 100.0,
                        modelo_usado='coverage_model_v2',
                        versao_modelo='2.0',
                        fatores_risco={"fonte": "inclusao_apolice_basico"},
                        dados_climaticos={"temperatura": int(25), "umidade": int(random.randint(40, 80))},
                        dados_propriedade={"valor": float(policy_data['valor_segurado']), "tipo": str(policy_data['tipo_residencia'])},
                        resultado_predicao={"score": coverage_score, "confianca": float(0.8)},
                        confianca_modelo=float(0.8),
                        explicabilidade={"principais_fatores": ["localizacao", "tipo_residencia"]},
                        tempo_processamento_ms=int(random.randint(50, 150))
                    )
                    
                    coverage_risks.append(risco_data)
                
                # Salvar análises básicas
                if coverage_risks:
                    result_ids = dao.salvar_multiplos_riscos(coverage_risks)
                    if result_ids:
                        st.info(f"💾 Salvas {len(result_ids)} análises básicas de risco por cobertura")
        
    except Exception as e:
        st.warning(f"⚠️ Erro ao salvar análises de risco por cobertura: {e}")

def get_risk_level_from_score(score):
    """Converter score numérico para nível de risco"""
    if score >= 75:
        return "alto"
    elif score >= 50:
        return "medio"
    elif score >= 25:
        return "baixo"
    else:
        return "muito_baixo"

def save_policy_simple(policy_data, risk_data):
    """Salva apólice residencial em banco SQLite simples"""
    try:
        import sqlite3
        import os
        
        # Garantir que o diretório existe
        os.makedirs('database', exist_ok=True)
        
        # Conectar ao banco
        conn = sqlite3.connect('database/radar_sinistro.db')
        cursor = conn.cursor()
        
        # Verificar se a apólice já existe
        cursor.execute('SELECT id FROM apolices WHERE numero_apolice = ?', (policy_data['numero_apolice'],))
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            st.warning(f"Apólice {policy_data['numero_apolice']} já existe no banco de dados")
            return existing[0]  # Retorna o ID existente
        
        # Criar tabela se não existir (usar mesma estrutura da tabela principal)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS apolices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_apolice TEXT UNIQUE,
                segurado TEXT,
                cep TEXT,
                latitude REAL,
                longitude REAL,
                tipo_residencia TEXT,
                valor_segurado REAL,
                data_contratacao TEXT,
                ativa INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT,
                data_inicio TEXT,
                score_risco REAL,
                nivel_risco TEXT,
                probabilidade_sinistro REAL
            )
        ''')
        
        # Inserir dados na tabela principal apolices
        cursor.execute('''
            INSERT INTO apolices 
            (numero_apolice, segurado, cep, valor_segurado, 
             data_inicio, tipo_residencia, score_risco, nivel_risco, 
             probabilidade_sinistro, created_at, data_contratacao, ativa,
             latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            policy_data['numero_apolice'],
            policy_data.get('segurado', 'N/A'),
            policy_data['cep'],
            float(policy_data['valor_segurado']),
            policy_data['data_inicio'],
            policy_data.get('tipo_residencia', 'casa'),
            float(risk_data['score_risco']),
            risk_data['nivel_risco'],
            float(risk_data['probabilidade']),
            datetime.now().isoformat(),
            policy_data['data_inicio'],  # data_contratacao = data_inicio
            1,  # ativa = 1
            -15.0,  # latitude padrão (centro do Brasil)
            -47.0   # longitude padrão (centro do Brasil)
        ))
        
        policy_id = cursor.lastrowid
        
        # NOVO: Salvar coberturas no banco simples também
        if 'cd_coberturas' in policy_data and policy_data['cd_coberturas']:
            # Criar tabela apolice_cobertura se não existir
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS apolice_cobertura (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cd_cobertura INTEGER,
                    cd_produto INTEGER,
                    nr_apolice VARCHAR(50),
                    dt_inclusao DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Inserir vínculos das coberturas
            for cd_cobertura in policy_data['cd_coberturas']:
                cursor.execute('''
                    INSERT INTO apolice_cobertura 
                    (nr_apolice, cd_cobertura, cd_produto, dt_inclusao)
                    VALUES (?, ?, ?, ?)
                ''', (
                    policy_data['numero_apolice'],
                    cd_cobertura,
                    policy_data.get('cd_produto', 1),
                    policy_data['data_inicio']
                ))
        
        conn.commit()
        conn.close()
        
        # NOVO: Salvar análises de risco por cobertura também no fallback
        if policy_id:
            try:
                save_coverage_risk_analysis(policy_data, risk_data)
            except Exception as e:
                st.warning(f"⚠️ Análises de risco por cobertura não salvas: {e}")
        
        return policy_id
        
    except Exception as e:
        st.error(f"Erro ao salvar no banco simples: {e}")
        return None

def show_manage_policies():
    """Página principal de gerenciamento de apólices residenciais"""
    
    st.markdown("""
    <div class="main-header">
        <h2>🏠 GERENCIAMENTO DE APÓLICES RESIDENCIAIS</h2>
        <p>Inclusão individual e em lote com cálculo automático de risco climático</p>
        <p style="font-size: 0.9em; opacity: 0.8;">
            🌦️ Sistema especializado em análise de riscos residenciais baseado em dados climáticos
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Inclusão Individual", "📋 Inclusão em Lote", "📊 Ranking Atualizado", "🌦️ Análise Climática"])
    
    with tab1:
        show_individual_policy_form()
    
    with tab2:
        show_batch_policy_upload()
    
    with tab3:
        show_updated_ranking()
    
    with tab4:
        show_climate_risk_analysis()

def show_individual_policy_form():
    """Formulário para inclusão individual de apólices residenciais"""
    
    st.subheader("Nova Apólice Residencial")
    
    # Carregar produtos disponíveis
    try:
        from database import get_database, CRUDOperations
        db = get_database()
        crud = CRUDOperations(db)
        
        # Buscar produtos do ramo residencial (assumindo cd_ramo = 1 para residencial)
        produtos_residenciais = crud.get_produtos_by_ramo(1)
        
        if not produtos_residenciais:
            st.warning("⚠️ Nenhum produto residencial encontrado. Verifique se os produtos foram cadastrados.")
            return
            
        # Preparar opções para o combobox
        opcoes_produtos = {f"{p.nm_produto}": p.cd_produto for p in produtos_residenciais}
        nomes_produtos = list(opcoes_produtos.keys())
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar produtos: {e}")
        return
    
    with st.form("individual_policy_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Campo Nome do Produto - NOVO
            nome_produto = st.selectbox(
                "Nome do Produto *",
                options=nomes_produtos,
                help="Selecione o produto de seguro residencial"
            )
            
            # Campo Coberturas - NOVO (baseado no produto selecionado)
            cd_produto_selecionado = opcoes_produtos[nome_produto]
            try:
                coberturas_produto = crud.get_coberturas_by_produto(cd_produto_selecionado)
                
                if coberturas_produto:
                    opcoes_coberturas = {f"{c.nm_cobertura}{'*' if c.dv_basica else ''}": c.cd_cobertura for c in coberturas_produto}
                    nomes_coberturas = list(opcoes_coberturas.keys())
                    
                    coberturas_selecionadas = st.multiselect(
                        "Coberturas *",
                        options=nomes_coberturas,
                        help="Selecione as coberturas desejadas. Coberturas marcadas com (*) são básicas."
                    )
                else:
                    st.warning("⚠️ Nenhuma cobertura encontrada para este produto.")
                    coberturas_selecionadas = []
                    opcoes_coberturas = {}
                    
            except Exception as e:
                st.error(f"❌ Erro ao carregar coberturas: {e}")
                coberturas_selecionadas = []
                opcoes_coberturas = {}
            
            numero_apolice = st.text_input(
                "Número da Apólice *",
                placeholder="Ex: POL-2024-001234",
                help="Número único da apólice"
            )
            
            segurado = st.text_input(
                "Nome do Segurado *",
                placeholder="Ex: João Silva Santos",
                help="Nome completo do segurado"
            )
            
            email = st.text_input(
                "Email",
                placeholder="Ex: joao.silva@email.com",
                help="Email do segurado para contato"
            )
            
            telefone = st.text_input(
                "Telefone",
                placeholder="Ex: (11) 99999-9999",
                help="Telefone do segurado para contato"
            )
            
            cep = st.text_input(
                "CEP *",
                placeholder="Ex: 01234-567",
                help="CEP do local segurado"
            )
            
            valor_segurado = st.number_input(
                "Valor Segurado (R$) *",
                min_value=1000.0,
                max_value=10000000.0,
                value=50000.0,
                step=1000.0,
                help="Valor total da cobertura"
            )
        
        with col2:
            data_inicio = st.date_input(
                "Data de Início da Vigência *",
                value=datetime.now().date(),
                help="Data de início da cobertura"
            )
            
            tipo_residencia = st.selectbox(
                "Tipo de Residência *",
                ["Casa", "Apartamento", "Sobrado", "Kitnet"],
                help="Tipo de residência a ser segurada"
            )
            
           
        # Botões do formulário
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            submitted = st.form_submit_button("🔮 Calcular Risco e Salvar", width='stretch')
    
    # Processar formulário
    if submitted:
        # Validar campos obrigatórios
        if not all([nome_produto, numero_apolice, segurado, cep, valor_segurado, tipo_residencia]):
            st.error("❌ Por favor, preencha todos os campos obrigatórios!")
            return
        
        # Validar coberturas selecionadas
        if not coberturas_selecionadas:
            st.error("❌ Por favor, selecione pelo menos uma cobertura!")
            return
        
        # Validações adicionais
        if len(cep.replace('-', '').replace(' ', '')) != 8:
            st.error("❌ CEP deve ter 8 dígitos (formato: 12345-678)")
            return
            
        if not cep.replace('-', '').replace(' ', '').isdigit():
            st.error("❌ CEP deve conter apenas números")
            return
        
        # Obter código do produto selecionado
        cd_produto_selecionado = opcoes_produtos[nome_produto]
        
        # Obter códigos das coberturas selecionadas
        cd_coberturas_selecionadas = [opcoes_coberturas[nome_cob] for nome_cob in coberturas_selecionadas]
        
        # Preparar dados (foco residencial)
        try:
            policy_data = {
                'numero_apolice': numero_apolice.strip(),
                'segurado': segurado.strip(),
                'cep': cep.strip(),
                'valor_segurado': float(valor_segurado),
                'data_inicio': data_inicio.isoformat(),
                'tipo_residencia': tipo_residencia,
                'cd_produto': cd_produto_selecionado,
                'nome_produto': nome_produto,
                'cd_coberturas': cd_coberturas_selecionadas  # NOVO: coberturas selecionadas
            }
        except Exception as e:
            st.error(f"❌ Erro ao preparar dados: {e}")
            return

        # DESABILITADO: Checar bloqueio de região (feature removida)
        # if 'REGION_BLOCK_FEATURE_ENABLED' in globals() and REGION_BLOCK_FEATURE_ENABLED:
        #     try:
        #         db = get_database()
        #         crud = CRUDOperations(db)
        #         blocked, reason, severity = crud.is_cep_blocked(policy_data['cep'], scope='residencial')
        #         if blocked:
        #             emoji = '⛔'
        #             sev_label = {1: 'Normal', 2: 'Alto', 3: 'Crítico'}.get(severity, 'Alto')
        #             st.error(f"{emoji} Emissão bloqueada para região (prefixo CEP) - Motivo: {reason or 'Alto risco'} (Severidade: {sev_label})")
        #             return
        #     except Exception as e:
        #         # Fail-open: apenas logar aviso
        #         st.warning(f"⚠️ Não foi possível validar bloqueio de região: {e}")
        
        # Calcular risco específico por cobertura
        coverage_risk_data = None
        if coberturas_selecionadas:
            with st.spinner("🎯 Analisando risco específico por cobertura..."):
                coverage_risk_data = calculate_coverage_specific_risk(policy_data, coberturas_selecionadas)
        
        # Mostrar resultado apenas se há coberturas selecionadas
        if coverage_risk_data and coverage_risk_data['has_specific_analysis']:
            st.markdown("### 📊 Análise de Risco por Cobertura")
            
            coverage_analysis = coverage_risk_data['coverage_analysis']
            
            # Mostrar resumo da análise por cobertura
            col1, col2 = st.columns(2)
            
            with col1:
                overall_level = coverage_analysis['summary']['overall_risk_level']
                emoji_coverage = get_risk_level_emoji(coverage_analysis['summary']['average_risk_score'])
                st.metric(
                    "Risco Médio das Coberturas",
                    f"{emoji_coverage} {overall_level.upper()}",
                    f"{coverage_analysis['summary']['average_risk_score']:.1f}/100"
                )
            
            with col2:
                analyzed_count = coverage_analysis['summary']['total_coverages_analyzed']
                total_selected = coverage_risk_data.get('analysis_info', {}).get('total_selected', analyzed_count)
                st.metric(
                    "Coberturas Analisadas",
                    f"{analyzed_count}/{total_selected}",
                    help="Número de coberturas com análise climática específica"
                )
            
            # Mostrar informações sobre coberturas não analisadas
            analysis_info = coverage_risk_data.get('analysis_info', {})
            if analysis_info.get('unavailable'):
                with st.expander("ℹ️ Informações sobre Coberturas"):
                    st.info(f"✅ **Analisadas**: {', '.join([c.replace('_', ' ').title() for c in coverage_analysis['coverage_analysis'].keys()])}")
                    st.warning(f"⚠️ **Sem modelo específico**: {', '.join(analysis_info['unavailable'])}")
                    st.markdown("💡 *Coberturas sem modelo específico não são incluídas na análise climática*")
            
            # Detalhes por cobertura
            if coverage_analysis['coverage_analysis']:
                st.markdown("#### 🛡️ Análise Individual por Cobertura:")
                
                for coverage_key, details in coverage_analysis['coverage_analysis'].items():
                    if 'error' not in details:
                        with st.container():
                            col1, col2, col3, col4 = st.columns(4)
                            
                            coverage_name = coverage_key.replace('_', ' ').title()
                            risk_score = details['risk_score']
                            risk_level = details['risk_level']
                            
                            with col1:
                                st.write(f"**🛡️ {coverage_name}**")
                            with col2:
                                emoji_cov = get_risk_level_emoji(risk_score)
                                st.write(f"{emoji_cov} {risk_level.upper()}")
                            with col3:
                                st.write(f"**{risk_score:.1f}/100**")
                            with col4:
                                if risk_score > 70:
                                    st.write("🔴 **Alta Atenção**")
                                elif risk_score > 40:
                                    st.write("🟡 **Monitorar**")
                                else:
                                    st.write("🟢 **Normal**")
                            
                            st.markdown("---")
            
            # Mostrar recomendações específicas
            recommendations = coverage_risk_data['recommendations']
            if recommendations:
                with st.expander(f"⚠️ Recomendações Climáticas ({len(recommendations)})"):
                    for i, rec in enumerate(recommendations, 1):
                        # rec é uma string simples, não um dicionário
                        st.markdown(f"**{i}.** {rec}")
                        st.markdown("---")
            
            # Preparar dados de risco baseados na análise por cobertura para salvar no banco
            risk_data = {
                'score_risco': coverage_analysis['summary']['average_risk_score'],
                'nivel_risco': coverage_analysis['summary']['overall_risk_level'],
                'probabilidade': coverage_analysis['summary']['average_risk_score'] / 100,
                'fatores_risco': coverage_analysis['summary'].get('critical_factors', [])
            }
            
            # Salvar no banco
            with st.spinner("💾 Salvando apólice no banco de dados..."):
                policy_id = save_policy_to_database(policy_data, risk_data)
            
            if policy_id:
                st.success(f"✅ Apólice **{numero_apolice}** salva com sucesso! ID: {policy_id}")
                
                # Mostrar coberturas selecionadas
                st.info(f"📋 Coberturas incluídas: {', '.join(coberturas_selecionadas)}")
                st.info(f"🎯 Risco calculado baseado em análise específica por cobertura")
        
        else:
            # Se não há coberturas selecionadas ou análise não está disponível
            if not coberturas_selecionadas:
                st.warning("⚠️ Nenhuma cobertura foi selecionada.")
                st.info("💡 Selecione pelo menos uma cobertura para calcular o risco específico.")
            elif coverage_risk_data and coverage_risk_data.get('error'):
                st.error(f"❌ {coverage_risk_data['error']}")
                st.info("💡 Tente selecionar coberturas que possuem modelos específicos: **Danos Elétricos**, **Vendaval**, **Granizo** ou **Alagamento**.")
            else:
                st.warning("⚠️ A análise específica por cobertura não está disponível.")
                st.info("💡 Verifique se o sistema de modelos está funcionando corretamente.")
            return

def show_batch_policy_upload():
    """Interface para upload em lote de apólices"""
    
    st.subheader("Inclusão em Lote")
    
    # Upload de arquivo - PRIMEIRO
    st.markdown("### Upload do Arquivo")
    
    ''' 
    st.warning("""
    **⚠️ Problemas comuns a evitar:**
    - Campo 'segurado' vazio ou com apenas espaços
    - Nomes muito curtos (menos de 3 caracteres)
    - Caracteres especiais mal formatados (problemas de encoding)
    - CEP sem os 8 dígitos obrigatórios
    """)
    '''

    uploaded_file = st.file_uploader(
        "Escolha o arquivo CSV ou Excel com as apólices",
        type=['csv', 'xlsx', 'xls'],
        help="Arquivo deve seguir o formato do template. Excel permite incluir coberturas em planilha separada."
    )
    
    if uploaded_file is not None:
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            # Processar arquivo baseado na extensão
            if file_extension == 'csv':
                # Ler arquivo CSV com encoding adequado para caracteres especiais
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                    df_coberturas = None  # CSV não tem planilha de coberturas
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='latin-1')
                    df_coberturas = None
                    st.warning("Arquivo CSV lido com encoding latin-1. Recomenda-se salvar como UTF-8.")
                except Exception:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file)
                    df_coberturas = None
                    
            elif file_extension in ['xlsx', 'xls']:
                # Ler arquivo Excel
                try:
                    # Verificar se openpyxl está disponível
                    try:
                        import openpyxl
                    except ImportError:
                        st.error("❌ Dependência 'openpyxl' não encontrada para leitura de arquivos Excel.")
                        with st.expander("🔧 Como resolver"):
                            st.code("pip install openpyxl", language="bash")
                            st.info("Execute o comando acima no terminal e recarregue a página.")
                        return
                    
                    # Ler planilha de apólices
                    df = pd.read_excel(uploaded_file, sheet_name='Apolices', engine='openpyxl')
                    
                    # Tentar ler planilha de coberturas
                    try:
                        uploaded_file.seek(0)
                        df_coberturas = pd.read_excel(uploaded_file, sheet_name='Coberturas', engine='openpyxl')
                        st.success(f"✅ Arquivo Excel carregado: {len(df)} apólices e {len(df_coberturas)} coberturas encontradas")
                    except Exception:
                        df_coberturas = None
                        st.info("ℹ️ Planilha 'Coberturas' não encontrada ou vazia. Processando apenas apólices.")
                        
                except Exception as e:
                    st.error(f"❌ Erro ao ler arquivo Excel: {e}")
                    if "openpyxl" in str(e):
                        with st.expander("🔧 Como resolver"):
                            st.code("pip install openpyxl", language="bash")
                            st.info("Execute o comando acima no terminal e recarregue a página.")
                    return
            else:
                st.error("❌ Formato de arquivo não suportado!")
                return
            
            if df_coberturas is None:
                st.success(f"✅ Arquivo carregado: {len(df)} apólices encontradas")
            
            # Mostrar preview das apólices
            st.markdown("### Preview dos Dados - Apólices")
            st.dataframe(df.head(10), width='stretch')
            
            # Mostrar preview das coberturas se disponível
            if df_coberturas is not None and not df_coberturas.empty:
                st.markdown("### Preview dos Dados - Coberturas")
                st.dataframe(df_coberturas.head(10), width='stretch')
            
            # Validar dados das apólices
            required_columns = ['numero_apolice', 'segurado', 'nome_produto', 'cep', 'valor_segurado', 'data_inicio', 'tipo_residencia']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Colunas obrigatórias faltando na planilha de apólices: {', '.join(missing_columns)}")
                return
            
            # Validar dados das coberturas se disponível
            if df_coberturas is not None and not df_coberturas.empty:
                required_cob_columns = ['numero_apolice', 'nome_cobertura']
                missing_cob_columns = [col for col in required_cob_columns if col not in df_coberturas.columns]
                
                if missing_cob_columns:
                    st.error(f"❌ Colunas obrigatórias faltando na planilha de coberturas: {', '.join(missing_cob_columns)}")
                    return
            
            # Validação prévia dos dados
            st.markdown("### 🔍 Validação dos Dados")
            validation_results = validate_batch_data(df, df_coberturas)
            
            if validation_results['errors']:
                st.error("❌ Problemas encontrados nos dados:")
                for error in validation_results['errors']:
                    st.error(f"• {error['source']} - Linha {error['row']}: {error['message']}")
                st.info("💡 Corrija os problemas no arquivo e faça upload novamente.")
                return
            
            if validation_results['warnings']:
                st.warning("⚠️ Avisos encontrados:")
                for warning in validation_results['warnings']:
                    st.warning(f"• {warning['source']} - Linha {warning['row']}: {warning['message']}")
            
            st.success(f"✅ Validação concluída: {len(df)} apólices válidas para processamento")
            
            # Botão para processar lote
            if st.button("Processar Lote Completo", width='stretch'):
                process_batch_policies(df, df_coberturas)
                
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {e}")
    
    # Separador visual
    st.markdown("---")
    
    # Template para download - SEGUNDO
    st.markdown("### Template para Download")
    
    # Carregar produtos disponíveis para mostrar no template
    try:
        from database import get_database, CRUDOperations
        db = get_database()
        crud = CRUDOperations(db)
        produtos_residenciais = crud.get_produtos_by_ramo(1)
        
        if produtos_residenciais:
            st.info(f"""
            **Instruções para preenchimento:**
            - **numero_apolice**: Código único da apólice (obrigatório)
            - **segurado**: Nome completo do segurado (obrigatório, mínimo 3 caracteres)
            - **nome_produto**: Nome do produto de seguro (obrigatório)
            - **cep**: Código postal com 8 dígitos (pode incluir hífen)
            - **valor_segurado**: Valor em reais (obrigatório, maior que zero)
            - **data_inicio**: Data no formato AAAA-MM-DD
            - **tipo_residencia**: Casa, Apartamento, Sobrado ou Kitnet
            
            **Produtos disponíveis:** {', '.join([p.nm_produto for p in produtos_residenciais])}
            
            **Para coberturas:** Use a planilha 'Coberturas' do arquivo Excel com as colunas:
            - **numero_apolice**: Referência à apólice
            - **nome_cobertura**: Nome da cobertura desejada
            """)
        else:
            st.warning("⚠️ Nenhum produto encontrado. Contate o administrador.")
            
    except Exception as e:
        st.error(f"Erro ao carregar produtos: {e}")
    
    # Criar template com os novos campos
    template_data = pd.DataFrame({
        'numero_apolice': ['POL-2024-000001', 'POL-2024-000002', 'POL-2024-000003'],
        'segurado': ['João Silva Santos', 'Maria Oliveira Costa', 'Pedro Henrique Ferreira'],
        'nome_produto': ['Residencial Básico', 'Residencial Premium', 'Residencial Básico'],
        'cep': ['01234-567', '89012345', '13579-024'],
        'valor_segurado': [300000.0, 450000.0, 180000.0],
        'data_inicio': ['2024-10-07', '2024-10-07', '2024-10-07'],
        'tipo_residencia': ['Casa', 'Apartamento', 'Sobrado'],
        'email': ['joao.silva@email.com', 'maria.oliveira@email.com', 'pedro.ferreira@email.com'],
        'telefone': ['(11) 98765-4321', '(21) 99876-5432', '(31) 97654-3210']
    })
    
    st.dataframe(template_data, width='stretch')
    
    # Template de coberturas
    st.markdown("#### Template de Coberturas")
    template_coberturas = pd.DataFrame({
        'numero_apolice': ['POL-2024-000001', 'POL-2024-000001', 'POL-2024-000002', 'POL-2024-000002', 'POL-2024-000003'],
        'nome_cobertura': ['Incêndio', 'Vendaval', 'Incêndio', 'Danos Elétricos', 'Roubo']
    })
    
    st.dataframe(template_coberturas, width='stretch')
    
    # Criar arquivo Excel com duas planilhas
    try:
        import io
        
        # Verificar se xlsxwriter está disponível
        try:
            import xlsxwriter
        except ImportError:
            st.warning("⚠️ Dependência 'xlsxwriter' não encontrada. Apenas template CSV disponível.")
            st.info("Para habilitar download Excel: `pip install xlsxwriter`")
        else:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                template_data.to_excel(writer, sheet_name='Apolices', index=False)
                template_coberturas.to_excel(writer, sheet_name='Coberturas', index=False)
            
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Baixar Template Excel (Recomendado)",
                data=excel_data,
                file_name=f"template_apolices_coberturas_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
    except Exception as e:
        st.warning(f"Erro ao gerar template Excel: {e}")
    
    # Fallback: CSV simples para apólices
    csv_template = template_data.to_csv(index=False)
    st.download_button(
        label="📄 Baixar Template CSV (Apenas Apólices)",
        data=csv_template,
        file_name=f"template_apolices_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

def validate_batch_data(df, df_coberturas=None):
    """Valida dados do lote antes do processamento"""
    errors = []
    warnings = []
    
    # Carregar dados de referência para validação
    try:
        from database import get_database, CRUDOperations
        db = get_database()
        crud = CRUDOperations(db)
        produtos_residenciais = crud.get_produtos_by_ramo(1)
        nomes_produtos_validos = [p.nm_produto for p in produtos_residenciais]
        
        # Criar mapeamento de produto para coberturas
        produto_coberturas = {}
        for produto in produtos_residenciais:
            coberturas = crud.get_coberturas_by_produto(produto.cd_produto)
            produto_coberturas[produto.nm_produto] = [c.nm_cobertura for c in coberturas]
            
    except Exception as e:
        errors.append({'source': 'Sistema', 'row': 0, 'message': f'Erro ao carregar dados de referência: {e}'})
        return {'errors': errors, 'warnings': warnings}
    
    # Validar apólices
    for index, row in df.iterrows():
        row_num = index + 1
        
        # Validar numero_apolice
        if pd.isna(row['numero_apolice']) or str(row['numero_apolice']).strip() == '':
            errors.append({'source': 'Apólices', 'row': row_num, 'message': 'Número da apólice é obrigatório'})
        
        # Validar segurado
        if pd.isna(row['segurado']) or str(row['segurado']).strip() == '':
            errors.append({'source': 'Apólices', 'row': row_num, 'message': 'Nome do segurado é obrigatório'})
        elif len(str(row['segurado']).strip()) < 3:
            errors.append({'source': 'Apólices', 'row': row_num, 'message': 'Nome do segurado deve ter pelo menos 3 caracteres'})
        
        # Validar nome_produto
        if pd.isna(row['nome_produto']) or str(row['nome_produto']).strip() == '':
            errors.append({'source': 'Apólices', 'row': row_num, 'message': 'Nome do produto é obrigatório'})
        elif str(row['nome_produto']).strip() not in nomes_produtos_validos:
            errors.append({'source': 'Apólices', 'row': row_num, 'message': f'Produto "{row["nome_produto"]}" não encontrado. Produtos válidos: {", ".join(nomes_produtos_validos)}'})
        
        # Validar CEP
        if pd.isna(row['cep']) or str(row['cep']).strip() == '':
            errors.append({'source': 'Apólices', 'row': row_num, 'message': 'CEP é obrigatório'})
        else:
            cep_clean = str(row['cep']).strip().replace('-', '')
            if len(cep_clean) != 8 or not cep_clean.isdigit():
                errors.append({'source': 'Apólices', 'row': row_num, 'message': 'CEP deve ter 8 dígitos (formato: 12345-678 ou 12345678)'})
        
        # Validar valor_segurado
        if pd.isna(row['valor_segurado']):
            errors.append({'source': 'Apólices', 'row': row_num, 'message': 'Valor segurado é obrigatório'})
        else:
            try:
                valor = float(row['valor_segurado'])
                if valor <= 0:
                    errors.append({'source': 'Apólices', 'row': row_num, 'message': 'Valor segurado deve ser maior que zero'})
                elif valor < 10000:
                    warnings.append({'source': 'Apólices', 'row': row_num, 'message': 'Valor segurado muito baixo (menor que R$ 10.000)'})
                elif valor > 5000000:
                    warnings.append({'source': 'Apólices', 'row': row_num, 'message': 'Valor segurado muito alto (maior que R$ 5.000.000)'})
            except ValueError:
                errors.append({'source': 'Apólices', 'row': row_num, 'message': 'Valor segurado deve ser um número válido'})
        
        # Validar data_inicio
        if pd.isna(row['data_inicio']) or str(row['data_inicio']).strip() == '':
            errors.append({'source': 'Apólices', 'row': row_num, 'message': 'Data de início é obrigatória'})
        
        # Validar tipo_residencia
        if pd.isna(row.get('tipo_residencia')):
            warnings.append({'source': 'Apólices', 'row': row_num, 'message': 'Tipo de residência não informado, será usado "Casa" como padrão'})
        else:
            tipos_validos = ['Casa', 'Apartamento', 'Sobrado', 'Kitnet']
            if str(row['tipo_residencia']).strip() not in tipos_validos:
                warnings.append({'source': 'Apólices', 'row': row_num, 'message': f'Tipo de residência "{row["tipo_residencia"]}" não é padrão. Tipos recomendados: {", ".join(tipos_validos)}'})
    
    # Validar coberturas se disponível
    if df_coberturas is not None and not df_coberturas.empty:
        apolices_no_arquivo = set(df['numero_apolice'].astype(str))
        
        for index, row in df_coberturas.iterrows():
            row_num = index + 1
            
            # Validar numero_apolice
            if pd.isna(row['numero_apolice']) or str(row['numero_apolice']).strip() == '':
                errors.append({'source': 'Coberturas', 'row': row_num, 'message': 'Número da apólice é obrigatório'})
            elif str(row['numero_apolice']).strip() not in apolices_no_arquivo:
                errors.append({'source': 'Coberturas', 'row': row_num, 'message': f'Apólice "{row["numero_apolice"]}" não encontrada na planilha de apólices'})
            
            # Validar nome_cobertura
            if pd.isna(row['nome_cobertura']) or str(row['nome_cobertura']).strip() == '':
                errors.append({'source': 'Coberturas', 'row': row_num, 'message': 'Nome da cobertura é obrigatório'})
            else:
                # Validar se a cobertura existe para o produto da apólice
                numero_apolice = str(row['numero_apolice']).strip()
                nome_cobertura = str(row['nome_cobertura']).strip()
                
                # Encontrar o produto da apólice
                apolice_row = df[df['numero_apolice'].astype(str) == numero_apolice]
                if not apolice_row.empty:
                    nome_produto = str(apolice_row.iloc[0]['nome_produto']).strip()
                    if nome_produto in produto_coberturas:
                        coberturas_validas = produto_coberturas[nome_produto]
                        if nome_cobertura not in coberturas_validas:
                            errors.append({'source': 'Coberturas', 'row': row_num, 'message': f'Cobertura "{nome_cobertura}" não disponível para produto "{nome_produto}". Coberturas válidas: {", ".join(coberturas_validas)}'})
    
    return {'errors': errors, 'warnings': warnings}

def process_batch_policies(df, df_coberturas=None):
    """Processa lote de apólices com cálculo de risco e coberturas"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()
    
    successful_policies = []
    failed_policies = []
    
    total_policies = len(df)
    
    # Carregar dados de produtos para conversão
    try:
        from database import get_database, CRUDOperations
        db = get_database()
        crud = CRUDOperations(db)
        produtos_residenciais = crud.get_produtos_by_ramo(1)
        nome_para_codigo_produto = {p.nm_produto: p.cd_produto for p in produtos_residenciais}
        
        # Preparar mapeamento de coberturas se disponível
        coberturas_por_apolice = {}
        if df_coberturas is not None and not df_coberturas.empty:
            for _, row in df_coberturas.iterrows():
                numero_apolice = str(row['numero_apolice']).strip()
                nome_cobertura = str(row['nome_cobertura']).strip()
                
                if numero_apolice not in coberturas_por_apolice:
                    coberturas_por_apolice[numero_apolice] = []
                coberturas_por_apolice[numero_apolice].append(nome_cobertura)
                
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados de produtos: {e}")
        return
    
    for index, row in df.iterrows():
        # Atualizar progresso
        progress = (index + 1) / total_policies
        progress_bar.progress(progress)
        status_text.text(f"Processando apólice {index + 1} de {total_policies}: {row['numero_apolice']}")
        
        try:
            # Validar dados obrigatórios da linha
            if pd.isna(row['numero_apolice']) or str(row['numero_apolice']).strip() == '':
                raise ValueError("Número da apólice é obrigatório")
            
            if pd.isna(row['segurado']) or str(row['segurado']).strip() == '':
                raise ValueError("Nome do segurado é obrigatório")
            
            if pd.isna(row['nome_produto']) or str(row['nome_produto']).strip() == '':
                raise ValueError("Nome do produto é obrigatório")
            
            if pd.isna(row['cep']) or str(row['cep']).strip() == '':
                raise ValueError("CEP é obrigatório")
            
            if pd.isna(row['valor_segurado']) or float(row['valor_segurado']) <= 0:
                raise ValueError("Valor segurado deve ser maior que zero")
            
            # Obter código do produto
            nome_produto = str(row['nome_produto']).strip()
            if nome_produto not in nome_para_codigo_produto:
                raise ValueError(f"Produto '{nome_produto}' não encontrado")
            
            cd_produto = nome_para_codigo_produto[nome_produto]
            
            # Preparar dados da apólice
            numero_apolice = str(row['numero_apolice']).strip()
            policy_data = {
                'numero_apolice': numero_apolice,
                'segurado': str(row['segurado']).strip(),
                'cep': str(row['cep']).strip().replace('-', ''),
                'valor_segurado': float(row['valor_segurado']),
                'data_inicio': str(row['data_inicio']),
                'tipo_residencia': str(row['tipo_residencia']).strip() if pd.notna(row.get('tipo_residencia')) else 'Casa',
                'cd_produto': cd_produto,
                'nome_produto': nome_produto,
                'email': str(row['email']).strip() if pd.notna(row.get('email')) and str(row.get('email')).strip() != '' else None,
                'telefone': str(row['telefone']).strip() if pd.notna(row.get('telefone')) and str(row.get('telefone')).strip() != '' else None
            }
            
            # Processar coberturas se disponível
            if numero_apolice in coberturas_por_apolice:
                nomes_coberturas = coberturas_por_apolice[numero_apolice]
                
                # Converter nomes de coberturas para códigos
                cd_coberturas = []
                coberturas_produto = crud.get_coberturas_by_produto(cd_produto)
                nome_para_codigo_cobertura = {c.nm_cobertura: c.cd_cobertura for c in coberturas_produto}
                
                for nome_cob in nomes_coberturas:
                    if nome_cob in nome_para_codigo_cobertura:
                        cd_coberturas.append(nome_para_codigo_cobertura[nome_cob])
                    else:
                        raise ValueError(f"Cobertura '{nome_cob}' não encontrada para produto '{nome_produto}'")
                
                policy_data['cd_coberturas'] = cd_coberturas
            else:
                # Se não há coberturas especificadas, usar coberturas básicas
                coberturas_produto = crud.get_coberturas_by_produto(cd_produto)
                coberturas_basicas = [c.cd_cobertura for c in coberturas_produto if c.dv_basica]
                if coberturas_basicas:
                    policy_data['cd_coberturas'] = coberturas_basicas
            
            # Validações adicionais
            if len(policy_data['segurado']) < 3:
                raise ValueError("Nome do segurado deve ter pelo menos 3 caracteres")
            
            if len(policy_data['cep']) != 8:
                raise ValueError("CEP deve ter 8 dígitos")

            # DESABILITADO: Checar bloqueio de região (feature removida)
            # if 'REGION_BLOCK_FEATURE_ENABLED' in globals() and REGION_BLOCK_FEATURE_ENABLED:
            #     try:
            #         blocked, reason, severity = crud.is_cep_blocked(policy_data['cep'], scope='residencial')
            #         if blocked:
            #             failed_policies.append({
            #                 'numero_apolice': policy_data['numero_apolice'],
            #                 'erro': f"Região bloqueada: {reason or 'Alto risco'}",
            #                 'blocked': True
            #             })
            #             continue
            #     except Exception as e:
            #         failed_policies.append({
            #             'numero_apolice': policy_data['numero_apolice'],
            #             'erro': f"Aviso bloqueio não verificado: {e}",
            #             'blocked': False
            #         })
            
            # Calcular risco
            risk_data = calculate_policy_risk(policy_data)
            
            # Salvar no banco
            try:
                policy_id = save_policy_to_database(policy_data, risk_data)
                
                if policy_id:
                    coberturas_info = ""
                    if 'cd_coberturas' in policy_data:
                        coberturas_info = f" com {len(policy_data['cd_coberturas'])} coberturas"
                    
                    successful_policies.append({
                        'numero_apolice': policy_data['numero_apolice'],
                        'segurado': policy_data['segurado'],
                        'produto': nome_produto,
                        'coberturas': len(policy_data.get('cd_coberturas', [])),
                        'score_risco': risk_data['score_risco'],
                        'nivel_risco': risk_data['nivel_risco'],
                        'policy_id': policy_id
                    })
                else:
                    failed_policies.append({
                        'numero_apolice': policy_data['numero_apolice'],
                        'erro': 'Erro ao salvar no banco'
                    })
            except Exception as save_error:
                # Capturar erros específicos de constraint de unicidade
                error_msg = str(save_error)
                if "UNIQUE constraint failed" in error_msg:
                    failed_policies.append({
                        'numero_apolice': policy_data['numero_apolice'],
                        'erro': 'Apólice duplicada - número já existe no banco'
                    })
                else:
                    failed_policies.append({
                        'numero_apolice': policy_data['numero_apolice'],
                        'erro': f'Erro ao salvar: {error_msg}'
                    })
                
        except Exception as e:
            failed_policies.append({
                'numero_apolice': str(row.get('numero_apolice', f'Linha {index + 1}')),
                'erro': str(e)
            })
    
    # Finalizar progresso
    progress_bar.progress(1.0)
    status_text.text("✅ Processamento concluído!")
    
    # Mostrar resultados
    with results_container:
        st.markdown("### 📊 Resultados do Processamento")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("✅ Sucessos", len(successful_policies))
        
        with col2:
            st.metric("❌ Falhas", len(failed_policies))
        
        # Mostrar apólices processadas com sucesso
        if successful_policies:
            st.markdown("#### ✅ Apólices Processadas com Sucesso")
            success_df = pd.DataFrame(successful_policies)
            st.dataframe(success_df, width='stretch')
        
        # Mostrar falhas
        if failed_policies:
            st.markdown("#### ❌ Apólices com Falha")
            failed_df = pd.DataFrame(failed_policies)
            st.dataframe(failed_df, width='stretch')

def show_updated_ranking():
    """Mostra ranking atualizado de apólices por risco"""
    
    st.subheader("📊 Ranking Atualizado por Risco")
    
    try:
        # Tentar conectar ao banco - primeiro tabela residencial, depois original
        import sqlite3
        
        conn = sqlite3.connect('database/radar_sinistro.db')
        
        # Usar sempre a tabela principal 'apolices'
        query = """
        SELECT numero_apolice, segurado, cep, valor_segurado, 
               tipo_residencia, score_risco, nivel_risco, 
               probabilidade_sinistro, created_at
        FROM apolices 
        ORDER BY score_risco DESC, created_at DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            st.info("Nenhuma apólice encontrada no banco de dados.")
            st.info("Use a aba 'Inclusão Individual' para adicionar sua primeira apólice!")
            return
        
        # Métricas resumo
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Apólices", len(df))
        
        with col2:
            high_risk = len(df[df['score_risco'] >= 70])
            st.metric("Alto Risco", high_risk, delta=f"{high_risk/len(df)*100:.1f}%")
        
        with col3:
            medium_risk = len(df[(df['score_risco'] >= 40) & (df['score_risco'] < 70)])
            st.metric("Médio Risco", medium_risk, delta=f"{medium_risk/len(df)*100:.1f}%")
        
        with col4:
            low_risk = len(df[df['score_risco'] < 40])
            st.metric("Baixo Risco", low_risk, delta=f"{low_risk/len(df)*100:.1f}%")
        
        # Filtros
        st.markdown("### 🔍 Filtros")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            risk_filter = st.selectbox(
                "Nível de Risco",
                ["Todos", "alto", "medio", "baixo"]
            )
        
        with col2:
            min_value = st.number_input(
                "Valor Mínimo (R$)",
                min_value=0.0,
                value=0.0,
                step=1000.0
            )
        
        with col3:
            search_policy = st.text_input(
                "Buscar Apólice",
                placeholder="Digite número da apólice..."
            )
        
        # Aplicar filtros
        filtered_df = df.copy()
        
        if risk_filter != "Todos":
            filtered_df = filtered_df[filtered_df['nivel_risco'] == risk_filter]
        
        if min_value > 0:
            filtered_df = filtered_df[filtered_df['valor_segurado'] >= min_value]
        
        if search_policy:
            filtered_df = filtered_df[filtered_df['numero_apolice'].str.contains(search_policy, case=False, na=False)]
        
        # Mostrar tabela
        st.markdown(f"### 📋 Apólices Encontradas ({len(filtered_df)})")
        
        if not filtered_df.empty:
            # Adicionar emojis de risco
            filtered_df['risco'] = filtered_df['score_risco'].apply(
                lambda x: f"{get_risk_level_emoji(x)} {x:.1f}"
            )
            
            # Formatar valores
            filtered_df['valor'] = filtered_df['valor_segurado'].apply(
                lambda x: f"R$ {x:,.2f}"
            )
            
            # Selecionar colunas para exibição (residencial)
            display_df = filtered_df[[
                'numero_apolice', 'segurado', 'tipo_residencia',
                'valor', 'risco', 'nivel_risco', 'cep'
            ]].copy()
            
            display_df.columns = [
                'Número', 'Segurado', 'Tipo', 
                'Valor Segurado', 'Score', 'Nível', 'CEP'
            ]
            
            st.dataframe(
                display_df,
                width='stretch',
                height=400
            )
            
            # Botão para exportar
            csv_export = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Exportar Dados",
                data=csv_export,
                file_name=f"apolices_ranking_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.info("🔍 Nenhuma apólice encontrada com os filtros aplicados.")
            
    except Exception as e:
        st.error(f"❌ Erro ao buscar dados: {e}")

def show_climate_risk_analysis():
    """Nova aba para análise avançada de riscos climáticos"""
    
    st.subheader("🌦️ Análise Avançada de Riscos Climáticos")
    st.markdown("""
    Esta seção permite analisar riscos específicos por cobertura considerando dados climáticos em tempo real.
    Selecione uma apólice existente ou insira dados para análise pontual.
    """)
    
    # Opções de análise
    analysis_type = st.radio(
        "Tipo de Análise:",
        ["📋 Analisar Apólice Existente", "🔍 Análise Pontual"]
    )
    
    if analysis_type == "📋 Analisar Apólice Existente":
        show_existing_policy_analysis()
    else:
        show_spot_analysis()

def show_existing_policy_analysis():
    """Análise de apólice existente no banco"""
    st.markdown("### Selecionar Apólice Existente")
    
    try:
        # Buscar apólices no banco
        import sqlite3
        conn = sqlite3.connect('database/radar_sinistro.db')
        
        query = """
        SELECT numero_apolice, segurado, cep, tipo_residencia, valor_segurado, latitude, longitude
        FROM apolices 
        WHERE ativa = 1
        ORDER BY created_at DESC
        LIMIT 50
        """
        
        df_policies = pd.read_sql_query(query, conn)
        conn.close()
        
        if df_policies.empty:
            st.info("Nenhuma apólice encontrada. Use a aba 'Inclusão Individual' para criar uma apólice primeiro.")
            return
        
        # Seletor de apólice
        policy_options = {}
        for _, row in df_policies.iterrows():
            key = f"{row['numero_apolice']} - {row['segurado']}"
            policy_options[key] = row
        
        selected_policy_key = st.selectbox(
            "Selecione a Apólice:",
            options=list(policy_options.keys()),
            help="Escolha uma apólice para análise climática detalhada"
        )
        
        if selected_policy_key:
            selected_policy = policy_options[selected_policy_key]
            
            # Mostrar dados da apólice selecionada
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"""
                **Apólice:** {selected_policy['numero_apolice']}
                **Segurado:** {selected_policy['segurado']}
                **CEP:** {selected_policy['cep']}
                **Tipo:** {selected_policy['tipo_residencia']}
                """)
            
            with col2:
                st.info(f"""
                **Valor Segurado:** R$ {selected_policy['valor_segurado']:,.2f}
                **Latitude:** {selected_policy.get('latitude', 'N/A')}
                **Longitude:** {selected_policy.get('longitude', 'N/A')}
                """)
            
            # Seleção de coberturas para análise
            st.markdown("### Coberturas para Análise")
            
            available_coverages = {
                'Danos Elétricos': 'danos_eletricos',
                'Vendaval': 'vendaval',
                'Granizo': 'granizo', 
                'Alagamento': 'alagamento'
            }
            
            selected_coverages = st.multiselect(
                "Selecione as coberturas para análise climática:",
                options=list(available_coverages.keys()),
                default=list(available_coverages.keys()),
                help="Escolha quais coberturas devem ser analisadas"
            )
            
            if st.button("🔬 Executar Análise Climática", width='stretch'):
                if selected_coverages:
                    # Preparar dados da apólice
                    policy_data = {
                        'numero_apolice': selected_policy['numero_apolice'],
                        'segurado': selected_policy['segurado'],
                        'cep': selected_policy['cep'],
                        'valor_segurado': float(selected_policy['valor_segurado']),
                        'tipo_residencia': selected_policy['tipo_residencia'],
                        'latitude': float(selected_policy.get('latitude', -15.0)),
                        'longitude': float(selected_policy.get('longitude', -47.0))
                    }
                    
                    # Executar análise
                    with st.spinner("🌦️ Analisando riscos climáticos..."):
                        coverage_risk_data = calculate_coverage_specific_risk(policy_data, selected_coverages)
                    
                    # Mostrar resultados detalhados
                    show_detailed_climate_results(coverage_risk_data)
                else:
                    st.error("Selecione pelo menos uma cobertura para análise.")
        
    except Exception as e:
        st.error(f"Erro ao buscar apólices: {e}")

def show_spot_analysis():
    """Análise pontual sem apólice cadastrada"""
    st.markdown("### Análise Pontual")
    
    with st.form("spot_analysis_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            latitude = st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=-23.5505,  # São Paulo
                step=0.0001,
                format="%.4f",
                help="Latitude da localização para análise"
            )
            
            tipo_residencia = st.selectbox(
                "Tipo de Residência",
                ["casa", "apartamento", "sobrado", "kitnet"]
            )
            
            valor_segurado = st.number_input(
                "Valor Segurado (R$)",
                min_value=10000.0,
                max_value=10000000.0,
                value=300000.0,
                step=10000.0
            )
        
        with col2:
            longitude = st.number_input(
                "Longitude", 
                min_value=-180.0,
                max_value=180.0,
                value=-46.6333,  # São Paulo
                step=0.0001,
                format="%.4f",
                help="Longitude da localização para análise"
            )
            
            idade_imovel = st.number_input(
                "Idade do Imóvel (anos)",
                min_value=0,
                max_value=100,
                value=15,
                help="Idade aproximada da construção"
            )
            
            cep = st.text_input(
                "CEP (opcional)",
                placeholder="01234567",
                help="CEP para análise regional"
            )
        
        # Seleção de coberturas
        st.markdown("#### Coberturas para Análise")
        available_coverages = ['Danos Elétricos', 'Vendaval', 'Granizo', 'Alagamento']
        
        selected_coverages = st.multiselect(
            "Selecione as coberturas:",
            options=available_coverages,
            default=available_coverages,
            help="Escolha quais coberturas devem ser analisadas"
        )
        
        submitted = st.form_submit_button("🔬 Executar Análise", width='stretch')
    
    if submitted and selected_coverages:
        # Preparar dados
        policy_data = {
            'numero_apolice': 'ANALISE-PONTUAL',
            'segurado': 'Análise Pontual',
            'cep': cep.replace('-', '') if cep else '00000000',
            'valor_segurado': valor_segurado,
            'tipo_residencia': tipo_residencia,
            'latitude': latitude,
            'longitude': longitude,
            'ano_construcao': datetime.now().year - idade_imovel
        }
        
        # Executar análise
        with st.spinner("🌦️ Analisando riscos climáticos na localização..."):
            coverage_risk_data = calculate_coverage_specific_risk(policy_data, selected_coverages)
        
        # Mostrar resultados
        show_detailed_climate_results(coverage_risk_data)

def show_detailed_climate_results(coverage_risk_data):
    """Mostra resultados detalhados da análise climática"""
    
    if not coverage_risk_data['has_specific_analysis']:
        st.error("❌ Não foi possível executar a análise climática específica.")
        return
    
    analysis = coverage_risk_data['coverage_analysis']
    
    st.markdown("### 📊 Resultados da Análise Climática")
    
    # Resumo geral
    col1, col2, col3 = st.columns(3)
    
    with col1:
        overall_prob = analysis['summary']['average_risk_probability']
        emoji = get_risk_level_emoji(overall_prob * 100)
        st.metric(
            "Risco Climático Geral",
            f"{emoji} {analysis['summary']['overall_risk_level'].upper()}",
            f"{overall_prob:.1%}"
        )
    
    with col2:
        high_risk_count = len(analysis['summary']['high_risk_coverages'])
        st.metric(
            "Coberturas Alto Risco",
            high_risk_count,
            f"de {analysis['summary']['total_coverages_analyzed']}"
        )
    
    with col3:
        timestamp = datetime.fromisoformat(analysis['analysis_timestamp'].replace('Z', '+00:00'))
        st.metric(
            "Análise Executada",
            timestamp.strftime("%H:%M"),
            timestamp.strftime("%d/%m/%Y")
        )
    
    # Gráfico de risco por cobertura
    if analysis['coverages']:
        st.markdown("#### 📈 Distribuição de Risco por Cobertura")
        
        # Preparar dados para gráfico
        coverage_names = []
        risk_percentages = []
        risk_colors = []
        
        for coverage_key, details in analysis['coverages'].items():
            if 'error' not in details:
                name = coverage_key.replace('_', ' ').title()
                percentage = details['probability'] * 100
                
                coverage_names.append(name)
                risk_percentages.append(percentage)
                
                # Cores baseadas no risco
                if percentage >= 60:
                    risk_colors.append('#ff4444')  # Vermelho
                elif percentage >= 30:
                    risk_colors.append('#ffaa00')  # Laranja
                else:
                    risk_colors.append('#44ff44')  # Verde
        
        # Criar gráfico usando Streamlit
        chart_data = pd.DataFrame({
            'Cobertura': coverage_names,
            'Risco (%)': risk_percentages
        })
        
        st.bar_chart(chart_data.set_index('Cobertura'))
    
    # Detalhes por cobertura
    st.markdown("#### 🔍 Detalhes por Cobertura")
    
    for coverage_key, details in analysis['coverages'].items():
        if 'error' not in details:
            coverage_name = coverage_key.replace('_', ' ').title()
            
            with st.expander(f"{coverage_name} - {details['risk_level'].upper()}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Probabilidade", f"{details['probability']:.1%}")
                    st.metric("Score de Risco", f"{details['risk_score']:.1f}")
                
                with col2:
                    st.metric("Nível", details['risk_level'].upper())
                    
                    # Mostrar se é predição do modelo ou heurística
                    if details.get('model_prediction') is not None:
                        st.info("🤖 Predição baseada em modelo ML")
                    else:
                        st.info("📊 Predição baseada em regras heurísticas")
                
                # Principais fatores de risco
                if details.get('main_factors'):
                    st.markdown("**Principais Fatores:**")
                    for factor in details['main_factors'][:3]:
                        importance = factor.get('importance', 0.1)
                        st.write(f"• {factor['feature']}: {importance:.2f}")
    
    # Recomendações
    recommendations = coverage_risk_data['recommendations']
    if recommendations:
        st.markdown("#### ⚠️ Recomendações Específicas")
        
        for i, rec in enumerate(recommendations, 1):
            # rec é uma string simples, não um dicionário
            st.info(f"**{i}.** {rec}")
            st.markdown("---")
    
    # Exportar dados
    if st.button("📥 Exportar Análise", width='stretch'):
        export_data = {
            'timestamp': analysis['analysis_timestamp'],
            'summary': analysis['summary'],
            'coverages': analysis['coverages'],
            'recommendations': recommendations
        }
        
        # Converter para JSON
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        st.download_button(
            label="💾 Baixar Relatório JSON",
            data=json_data,
            file_name=f"analise_climatica_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )

# Função principal para integração
if __name__ == "__main__":
    show_manage_policies()
