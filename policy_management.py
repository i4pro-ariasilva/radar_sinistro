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

# Adicionar ao sys.path se necessário
sys.path.append('.')

try:
    from database import get_database, CRUDOperations
    from src.ml.model_predictor import ModelPredictor
    from src.ml.feature_engineering import FeatureEngineer
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
        
        # Criar objeto Apolice com estrutura correta
        apolice = Apolice(
            numero_apolice=policy_data['numero_apolice'],
            segurado=policy_data.get('segurado', 'N/A'),
            cep=policy_data['cep'],
            tipo_residencia=policy_data['tipo_residencia'].lower(),  # Converter para minúscula
            valor_segurado=policy_data['valor_segurado'],
            data_contratacao=datetime.fromisoformat(policy_data['data_inicio']),
            email=policy_data.get('email', ''),
            telefone=policy_data.get('telefone', ''),
            latitude=None,  # Será preenchido posteriormente via geocoding
            longitude=None,  # Será preenchido posteriormente via geocoding
            ativa=True
        )
        
        # Adicionar campos extras para dados de risco
        apolice.data_inicio = policy_data['data_inicio']
        apolice.score_risco = float(risk_data['score_risco'])
        apolice.nivel_risco = risk_data['nivel_risco']
        apolice.probabilidade_sinistro = float(risk_data['probabilidade'])
        
        # Inserir no banco usando a função correta
        policy_id = crud.insert_apolice(apolice)
        
        return policy_id
        
    except Exception as e:
        st.warning(f"Sistema de banco avançado indisponível: {e}")
        # Fallback: salvar em SQLite simples
        return save_policy_simple(policy_data, risk_data)

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
                email TEXT,              -- NOVO
                telefone TEXT,           -- NOVO
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
            (numero_apolice, segurado, email, telefone, cep, valor_segurado,
             data_inicio, tipo_residencia, score_risco, nivel_risco,
             probabilidade_sinistro, created_at, data_contratacao, ativa,
             latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            policy_data['numero_apolice'],
            policy_data.get('segurado', 'N/A'),
            policy_data.get('email',''),
            policy_data.get('telefone',''),
            policy_data['cep'],
            float(policy_data['valor_segurado']),
            policy_data['data_inicio'],
            policy_data.get('tipo_residencia', 'casa'),
            float(risk_data['score_risco']),
            risk_data['nivel_risco'],
            float(risk_data['probabilidade']),
            datetime.now().isoformat(),
            policy_data['data_inicio'],
            1,
            -15.0,
            -47.0
        ))
        
        policy_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
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
    tab1, tab2, tab3 = st.tabs(["📝 Inclusão Individual", "📋 Inclusão em Lote", "📊 Ranking Atualizado"])
    
    with tab1:
        show_individual_policy_form()
    
    with tab2:
        show_batch_policy_upload()
    
    with tab3:
        show_updated_ranking()

def show_individual_policy_form():
    """Formulário para inclusão individual de apólices residenciais"""
    
    st.subheader("Nova Apólice Residencial")
    
    
    with st.form("individual_policy_form"):
        col1, col2 = st.columns(2)
        
        with col1:
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
                "E-mail do Segurado",
                placeholder="Ex: joao@email.com",
                help="E-mail para contato do segurado"
            )

            telefone = st.text_input(
                "Telefone do Segurado",
                placeholder="Ex: (11) 91234-5678",
                help="Telefone para contato do segurado"
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
            submitted = st.form_submit_button("🔮 Calcular Risco e Salvar", use_container_width=True)
    
    # Processar formulário
    if submitted:
        # Validar campos obrigatórios
        if not all([numero_apolice, segurado, cep, valor_segurado, tipo_residencia]):
            st.error("❌ Por favor, preencha todos os campos obrigatórios!")
            return
        
        # Validações adicionais
        if len(cep.replace('-', '').replace(' ', '')) != 8:
            st.error("❌ CEP deve ter 8 dígitos (formato: 12345-678)")
            return
            
        if not cep.replace('-', '').replace(' ', '').isdigit():
            st.error("❌ CEP deve conter apenas números")
            return
        
        # Preparar dados (foco residencial)
        try:
            policy_data = {
                'numero_apolice': numero_apolice.strip(),
                'segurado': segurado.strip(),
                'email': email.strip() if email else '',
                'telefone': telefone.strip() if telefone else '',
                'cep': cep.strip(),
                'valor_segurado': float(valor_segurado),
                'data_inicio': data_inicio.isoformat(),
                'tipo_residencia': tipo_residencia
            }
        except Exception as e:
            st.error(f"❌ Erro ao preparar dados: {e}")
            return
        
        # Calcular risco
        with st.spinner("🔮 Calculando risco da apólice..."):
            risk_data = calculate_policy_risk(policy_data)
        
        # Mostrar resultado do cálculo
        if risk_data['score_risco'] > 0:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                emoji = get_risk_level_emoji(risk_data['score_risco'])
                st.metric(
                    "Score de Risco",
                    f"{emoji} {risk_data['score_risco']:.1f}",
                    help="Score de 0-100, maior = mais risco"
                )
            
            with col2:
                st.metric(
                    "Nível de Risco",
                    risk_data['nivel_risco'].upper(),
                    help="Classificação qualitativa do risco"
                )
            
            with col3:
                st.metric(
                    "Probabilidade",
                    f"{risk_data['probabilidade']:.1%}",
                    help="Probabilidade de sinistro"
                )
            
            # Salvar no banco
            with st.spinner("💾 Salvando apólice no banco de dados..."):
                policy_id = save_policy_to_database(policy_data, risk_data)
            
            if policy_id:
                st.success(f"✅ Apólice **{numero_apolice}** salva com sucesso! ID: {policy_id}")
                st.balloons()
                
                # Mostrar fatores de risco
                if risk_data.get('fatores_principais'):
                    with st.expander("📊 Principais Fatores de Risco"):
                        for i, fator in enumerate(risk_data['fatores_principais'][:5]):
                            st.write(f"{i+1}. **{fator['feature']}**: {fator['importance']:.3f}")
            else:
                st.error("❌ Erro ao salvar apólice no banco de dados!")

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
        "Escolha o arquivo CSV com as apólices",
        type=['csv'],
        help="Arquivo deve seguir o formato do template abaixo"
    )
    
    if uploaded_file is not None:
        try:
            # Ler arquivo com encoding adequado para caracteres especiais
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                # Fallback para encoding latin-1 se UTF-8 falhar
                uploaded_file.seek(0)  # Voltar ao início do arquivo
                df = pd.read_csv(uploaded_file, encoding='latin-1')
                st.warning("Arquivo lido com encoding latin-1. Recomenda-se salvar como UTF-8.")
            except Exception:
                # Fallback final para encoding padrão
                uploaded_file.seek(0)  # Voltar ao início do arquivo
                df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ Arquivo carregado: {len(df)} apólices encontradas")
            
            # Mostrar preview
            st.markdown("### Preview dos Dados")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Validar dados
            required_columns = ['numero_apolice', 'segurado', 'cep', 'valor_segurado', 'data_inicio', 'tipo_residencia']
            optional_columns = ['email', 'telefone']
            missing_columns = [col for col in required_columns if col not in df.columns]
            # Adicionar colunas opcionais se não existirem
            for col in optional_columns:
                if col not in df.columns:
                    df[col] = ''
            if missing_columns:
                st.error(f"❌ Colunas obrigatórias faltando: {', '.join(missing_columns)}")
                return
            
            # Validação prévia dos dados
            st.markdown("### 🔍 Validação dos Dados")
            validation_results = validate_batch_data(df)
            
            if validation_results['errors']:
                st.error("❌ Problemas encontrados nos dados:")
                for error in validation_results['errors']:
                    st.error(f"• Linha {error['row']}: {error['message']}")
                st.info("💡 Corrija os problemas no arquivo e faça upload novamente.")
                return
            
            if validation_results['warnings']:
                st.warning("⚠️ Avisos encontrados:")
                for warning in validation_results['warnings']:
                    st.warning(f"• Linha {warning['row']}: {warning['message']}")
            
            st.success(f"✅ Validação concluída: {len(df)} apólices válidas para processamento")
            
            # Botão para processar lote
            if st.button("Processar Lote Completo", use_container_width=True):
                process_batch_policies(df)
                
        except Exception as e:
            st.error(f"❌ Erro ao processar arquivo: {e}")
    
    # Separador visual
    st.markdown("---")
    
    # Template para download - SEGUNDO
    st.markdown("### Template para Download")
    '''
    st.info("""
    **Instruções para preenchimento:**
    - **numero_apolice**: Código único da apólice (obrigatório)
    - **segurado**: Nome completo do segurado (obrigatório, mínimo 3 caracteres)
    - **cep**: Código postal com 8 dígitos (pode incluir hífen)
    - **valor_segurado**: Valor em reais (obrigatório, maior que zero)
    - **data_inicio**: Data no formato AAAA-MM-DD
    - **tipo_residencia**: Casa, Apartamento, Sobrado ou Kitnet
    """)
    '''
    template_data = pd.DataFrame({
        'numero_apolice': ['POL-2024-000001', 'POL-2024-000002', 'POL-2024-000003'],
        'segurado': ['João Silva Santos', 'Maria Oliveira Costa', 'Pedro Henrique Ferreira'],
        'email': ['joao@email.com', 'maria@email.com', 'pedro@email.com'],
        'telefone': ['(11) 91234-5678', '(21) 99876-5432', '(31) 98765-4321'],
        'cep': ['01234-567', '89012345', '13579-024'],
        'valor_segurado': [300000.0, 450000.0, 180000.0],
        'data_inicio': ['2024-10-07', '2024-10-07', '2024-10-07'],
        'tipo_residencia': ['Casa', 'Apartamento', 'Sobrado']
    })
    
    st.dataframe(template_data, use_container_width=True)
    
    # Botão para download do template
    csv_template = template_data.to_csv(index=False)
    st.download_button(
        label="Baixar Template CSV",
        data=csv_template,
        file_name=f"template_apolices_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

def validate_batch_data(df):
    """Valida dados do lote antes do processamento"""
    errors = []
    warnings = []
    
    for index, row in df.iterrows():
        row_num = index + 1
        
        # Validar numero_apolice
        if pd.isna(row['numero_apolice']) or str(row['numero_apolice']).strip() == '':
            errors.append({'row': row_num, 'message': 'Número da apólice é obrigatório'})
        
        # Validar segurado
        if pd.isna(row['segurado']) or str(row['segurado']).strip() == '':
            errors.append({'row': row_num, 'message': 'Nome do segurado é obrigatório'})
        elif len(str(row['segurado']).strip()) < 3:
            errors.append({'row': row_num, 'message': 'Nome do segurado deve ter pelo menos 3 caracteres'})
        
        # Validar CEP
        if pd.isna(row['cep']) or str(row['cep']).strip() == '':
            errors.append({'row': row_num, 'message': 'CEP é obrigatório'})
        else:
            cep_clean = str(row['cep']).strip().replace('-', '')
            if len(cep_clean) != 8 or not cep_clean.isdigit():
                errors.append({'row': row_num, 'message': 'CEP deve ter 8 dígitos (formato: 12345-678 ou 12345678)'})
        
        # Validar valor_segurado
        if pd.isna(row['valor_segurado']):
            errors.append({'row': row_num, 'message': 'Valor segurado é obrigatório'})
        else:
            try:
                valor = float(row['valor_segurado'])
                if valor <= 0:
                    errors.append({'row': row_num, 'message': 'Valor segurado deve ser maior que zero'})
                elif valor < 10000:
                    warnings.append({'row': row_num, 'message': 'Valor segurado muito baixo (menor que R$ 10.000)'})
                elif valor > 5000000:
                    warnings.append({'row': row_num, 'message': 'Valor segurado muito alto (maior que R$ 5.000.000)'})
            except ValueError:
                errors.append({'row': row_num, 'message': 'Valor segurado deve ser um número válido'})
        
        # Validar data_inicio
        if pd.isna(row['data_inicio']) or str(row['data_inicio']).strip() == '':
            errors.append({'row': row_num, 'message': 'Data de início é obrigatória'})
        
        # Validar tipo_residencia
        if pd.isna(row.get('tipo_residencia')):
            warnings.append({'row': row_num, 'message': 'Tipo de residência não informado, será usado "Casa" como padrão'})
        else:
            tipos_validos = ['Casa', 'Apartamento', 'Sobrado', 'Kitnet']
            if str(row['tipo_residencia']).strip() not in tipos_validos:
                warnings.append({'row': row_num, 'message': f'Tipo de residência "{row["tipo_residencia"]}" não é padrão. Tipos recomendados: {", ".join(tipos_validos)}'})
    
    return {'errors': errors, 'warnings': warnings}

def process_batch_policies(df):
    """Processa lote de apólices com cálculo de risco"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()
    
    successful_policies = []
    failed_policies = []
    
    total_policies = len(df)
    
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
            
            if pd.isna(row['cep']) or str(row['cep']).strip() == '':
                raise ValueError("CEP é obrigatório")
            
            if pd.isna(row['valor_segurado']) or float(row['valor_segurado']) <= 0:
                raise ValueError("Valor segurado deve ser maior que zero")
            
            # Preparar dados da apólice (residencial)
            policy_data = {
                'numero_apolice': str(row['numero_apolice']).strip(),
                'segurado': str(row['segurado']).strip(),
                'email': str(row.get('email','')).strip(),
                'telefone': str(row.get('telefone','')).strip(),
                'cep': str(row['cep']).strip().replace('-', ''),
                'valor_segurado': float(row['valor_segurado']),
                'data_inicio': str(row['data_inicio']),
                'tipo_residencia': str(row['tipo_residencia']).strip() if pd.notna(row.get('tipo_residencia')) else 'Casa'
            }
            
            # Validações adicionais
            if len(policy_data['segurado']) < 3:
                raise ValueError("Nome do segurado deve ter pelo menos 3 caracteres")
            
            if len(policy_data['cep']) != 8:
                raise ValueError("CEP deve ter 8 dígitos")
            
            # Calcular risco
            risk_data = calculate_policy_risk(policy_data)
            
            # Salvar no banco
            policy_id = save_policy_to_database(policy_data, risk_data)
            
            if policy_id:
                successful_policies.append({
                    'numero_apolice': policy_data['numero_apolice'],
                    'segurado': policy_data['segurado'],
                    'score_risco': risk_data['score_risco'],
                    'nivel_risco': risk_data['nivel_risco'],
                    'policy_id': policy_id
                })
            else:
                failed_policies.append({
                    'numero_apolice': policy_data['numero_apolice'],
                    'erro': 'Erro ao salvar no banco'
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
            st.dataframe(success_df, use_container_width=True)
        
        # Mostrar falhas
        if failed_policies:
            st.markdown("#### ❌ Apólices com Falha")
            failed_df = pd.DataFrame(failed_policies)
            st.dataframe(failed_df, use_container_width=True)

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
                use_container_width=True,
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

# Função principal para integração
if __name__ == "__main__":
    show_manage_policies()