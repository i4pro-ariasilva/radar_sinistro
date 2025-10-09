"""
Upload e Processamento de Dados - Sistema de Radar de Risco Climático
Interface para carregar arquivos CSV e processar dados de apólices
"""

import streamlit as st
import pandas as pd
import sys
import os
from pathlib import Path
import io
from datetime import datetime
import chardet

# Configuração da página
st.set_page_config(
    page_title="Upload de Dados - Radar Climático",
    page_icon="📤",
    layout="wide"
)

# Adicionar path do projeto
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

def detect_encoding(uploaded_file):
    """Detecta automaticamente o encoding do arquivo"""
    try:
        # Ler uma amostra do arquivo
        sample = uploaded_file.read(10000)
        uploaded_file.seek(0)  # Voltar ao início
        
        # Detectar encoding
        result = chardet.detect(sample)
        return result['encoding'] or 'utf-8'
    except:
        return 'utf-8'

def validate_csv_structure(df):
    """Valida a estrutura do CSV carregado"""
    required_columns = ['numero_apolice', 'cep', 'tipo_residencia', 'valor_segurado']
    optional_columns = ['data_contratacao', 'latitude', 'longitude']
    
    # Verificar colunas obrigatórias
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    # Verificar colunas disponíveis
    available_columns = [col for col in optional_columns if col in df.columns]
    
    return {
        'valid': len(missing_columns) == 0,
        'missing_columns': missing_columns,
        'available_columns': available_columns,
        'total_rows': len(df),
        'columns': list(df.columns)
    }

def process_uploaded_data(df):
    """Processa os dados carregados usando o processador do sistema"""
    try:
        from src.data_processing import PolicyDataProcessor
        
        # Criar processador
        processor = PolicyDataProcessor()
        
        # Processar dados
        processed_df = processor.process_dataframe(df)
        
        # Obter relatório de qualidade
        quality_report = processor.get_quality_report()
        
        return processed_df, quality_report
        
    except Exception as e:
        st.error(f"Erro no processamento: {str(e)}")
        return None, None

def save_to_database(processed_df):
    """Salva os dados processados no banco de dados"""
    try:
        from database import get_database, CRUDOperations
        from database.models import Apolice
        from datetime import datetime
        
        db = get_database()
        crud = CRUDOperations(db)
        
        success_count = 0
        error_count = 0
        errors = []
        
        for _, row in processed_df.iterrows():
            try:
                # Criar objeto Apolice
                apolice = Apolice(
                    numero_apolice=str(row['numero_apolice']),
                    cep=str(row['cep']),
                    tipo_residencia=str(row['tipo_residencia']),
                    valor_segurado=float(row['valor_segurado']),
                    data_contratacao=pd.to_datetime(row.get('data_contratacao', datetime.now())),
                    latitude=float(row['latitude']) if pd.notna(row.get('latitude')) else None,
                    longitude=float(row['longitude']) if pd.notna(row.get('longitude')) else None
                )
                
                # Inserir no banco
                crud.insert_apolice(apolice)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"Linha {_+1}: {str(e)}")
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10]  # Mostrar apenas os primeiros 10 erros
        }
        
    except Exception as e:
        st.error(f"Erro ao salvar no banco: {str(e)}")
        return None

def show_sample_format():
    """Mostra o formato esperado do arquivo CSV"""
    st.markdown("### 📋 Formato Esperado do Arquivo CSV")
    
    # Criar exemplo de DataFrame
    sample_data = {
        'numero_apolice': ['POL001', 'POL002', 'POL003'],
        'cep': ['01310-100', '04038-001', '22071-900'],
        'tipo_residencia': ['casa', 'apartamento', 'sobrado'],
        'valor_segurado': [350000.00, 180000.00, 420000.00],
        'data_contratacao': ['2024-01-15', '2024-02-20', '2024-03-10'],
        'latitude': [-23.5505, -23.5729, -22.9068],
        'longitude': [-46.6333, -46.6411, -43.1729]
    }
    
    sample_df = pd.DataFrame(sample_data)
    st.dataframe(sample_df, use_container_width=True)
    
    # Explicação das colunas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ✅ Colunas Obrigatórias")
        st.markdown("""
        - **numero_apolice**: Identificador único da apólice
        - **cep**: CEP no formato XXXXX-XXX
        - **tipo_residencia**: casa, apartamento ou sobrado
        - **valor_segurado**: Valor numérico da cobertura
        """)
    
    with col2:
        st.markdown("#### 📍 Colunas Opcionais")
        st.markdown("""
        - **data_contratacao**: Data no formato YYYY-MM-DD
        - **latitude**: Coordenada geográfica (decimal)
        - **longitude**: Coordenada geográfica (decimal)
        """)

def main():
    """Função principal da página"""
    
    st.title("📤 Upload e Processamento de Dados")
    st.markdown("Carregue arquivos CSV com dados de apólices para análise")
    
    # Sidebar com instruções
    with st.sidebar:
        st.markdown("### 📋 Instruções")
        st.info("""
        **Passos para upload:**
        1. Prepare arquivo CSV
        2. Faça upload do arquivo
        3. Visualize prévia dos dados
        4. Execute processamento
        5. Salve no banco de dados
        """)
        
        st.markdown("### 📊 Formato Suportado")
        st.markdown("- **Formato**: CSV (UTF-8)")
        st.markdown("- **Separador**: Vírgula (,)")
        st.markdown("- **Tamanho máximo**: 200MB")
        
        if st.button("📋 Ver Formato Esperado"):
            st.session_state.show_format = True
    
    # Mostrar formato esperado se solicitado
    if st.session_state.get('show_format', False):
        show_sample_format()
        st.markdown("---")
    
    # Upload de arquivo
    st.markdown("## 📁 Upload de Arquivo")
    
    uploaded_file = st.file_uploader(
        "Escolha um arquivo CSV",
        type=['csv'],
        help="Arquivo CSV com dados de apólices. Tamanho máximo: 200MB"
    )
    
    if uploaded_file is not None:
        # Mostrar informações do arquivo
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📁 Nome do Arquivo", uploaded_file.name)
        
        with col2:
            file_size = uploaded_file.size / (1024 * 1024)  # MB
            st.metric("📏 Tamanho", f"{file_size:.2f} MB")
        
        with col3:
            st.metric("🕒 Upload", datetime.now().strftime("%H:%M:%S"))
        
        # Detectar encoding
        with st.spinner("Detectando encoding do arquivo..."):
            encoding = detect_encoding(uploaded_file)
            st.success(f"✅ Encoding detectado: {encoding}")
        
        # Carregar dados
        try:
            df = pd.read_csv(uploaded_file, encoding=encoding)
            
            # Validar estrutura
            validation = validate_csv_structure(df)
            
            st.markdown("## 🔍 Validação da Estrutura")
            
            if validation['valid']:
                st.success("✅ Estrutura do arquivo válida!")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("📊 Total de Linhas", validation['total_rows'])
                
                with col2:
                    st.metric("📋 Colunas Disponíveis", len(validation['columns']))
                
                # Mostrar colunas disponíveis
                with st.expander("📋 Colunas Identificadas"):
                    st.write("**Colunas no arquivo:**")
                    for col in validation['columns']:
                        st.write(f"- {col}")
                    
                    if validation['available_columns']:
                        st.write("**Colunas opcionais encontradas:**")
                        for col in validation['available_columns']:
                            st.write(f"- ✅ {col}")
                
            else:
                st.error("❌ Estrutura do arquivo inválida!")
                st.write("**Colunas obrigatórias ausentes:**")
                for col in validation['missing_columns']:
                    st.write(f"- ❌ {col}")
                
                st.stop()
            
            # Prévia dos dados
            st.markdown("## 👀 Prévia dos Dados")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Botões de ação
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Processar Dados", use_container_width=True, type="primary"):
                    st.session_state.process_data = True
            
            with col2:
                if st.button("💾 Salvar Dados Brutos", use_container_width=True):
                    # Salvar dados sem processamento
                    result = save_to_database(df)
                    if result:
                        st.success(f"✅ {result['success_count']} registros salvos!")
                        if result['error_count'] > 0:
                            st.warning(f"⚠️ {result['error_count']} erros encontrados")
            
            with col3:
                if st.button("📋 Mostrar Estatísticas", use_container_width=True):
                    st.session_state.show_stats = True
            
            # Processamento de dados
            if st.session_state.get('process_data', False):
                st.markdown("---")
                st.markdown("## ⚙️ Processamento de Dados")
                
                with st.spinner("Processando dados..."):
                    processed_df, quality_report = process_uploaded_data(df)
                
                if processed_df is not None:
                    st.success("✅ Dados processados com sucesso!")
                    
                    # Mostrar relatório de qualidade
                    if quality_report:
                        st.markdown("### 📊 Relatório de Qualidade")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                "✅ Taxa de Sucesso",
                                f"{quality_report.get('taxa_sucesso', 0):.1f}%"
                            )
                        
                        with col2:
                            st.metric(
                                "📋 Registros Válidos",
                                quality_report.get('registros_validos', 0)
                            )
                        
                        with col3:
                            st.metric(
                                "⚠️ Registros com Erro",
                                quality_report.get('registros_erro', 0)
                            )
                        
                        with col4:
                            st.metric(
                                "🔧 Registros Corrigidos",
                                quality_report.get('registros_corrigidos', 0)
                            )
                    
                    # Mostrar dados processados
                    st.markdown("### 📊 Dados Processados")
                    st.dataframe(processed_df.head(10), use_container_width=True)
                    
                    # Salvar dados processados
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("💾 Salvar Dados Processados", use_container_width=True, type="primary"):
                            with st.spinner("Salvando no banco de dados..."):
                                result = save_to_database(processed_df)
                            
                            if result:
                                st.success(f"✅ {result['success_count']} registros salvos com sucesso!")
                                st.balloons()
                                
                                if result['error_count'] > 0:
                                    st.warning(f"⚠️ {result['error_count']} registros com erro")
                                    
                                    with st.expander("Ver erros"):
                                        for error in result['errors']:
                                            st.write(f"- {error}")
                    
                    with col2:
                        if st.button("📊 Ir para Dashboard", use_container_width=True):
                            st.switch_page("pages/01_📊_Dashboard.py")
            
            # Estatísticas dos dados
            if st.session_state.get('show_stats', False):
                st.markdown("---")
                st.markdown("## 📈 Estatísticas dos Dados")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📊 Estatísticas Gerais")
                    st.write(f"**Total de registros:** {len(df)}")
                    st.write(f"**Colunas:** {len(df.columns)}")
                    st.write(f"**Memória utilizada:** {df.memory_usage(deep=True).sum() / 1024:.1f} KB")
                    
                    # Valores únicos por coluna
                    st.markdown("### 🔢 Valores Únicos")
                    for col in df.columns:
                        unique_count = df[col].nunique()
                        st.write(f"**{col}:** {unique_count} valores únicos")
                
                with col2:
                    st.markdown("### ⚠️ Dados Faltantes")
                    missing_data = df.isnull().sum()
                    missing_percent = (missing_data / len(df)) * 100
                    
                    for col in df.columns:
                        if missing_data[col] > 0:
                            st.write(f"**{col}:** {missing_data[col]} ({missing_percent[col]:.1f}%)")
                        else:
                            st.write(f"**{col}:** ✅ Completo")
                    
                    # Estatísticas numéricas
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        st.markdown("### 📊 Estatísticas Numéricas")
                        st.dataframe(df[numeric_cols].describe(), use_container_width=True)
                
                # Reset do estado
                st.session_state.show_stats = False
        
        except Exception as e:
            st.error(f"❌ Erro ao carregar arquivo: {str(e)}")
            st.info("💡 Verifique se o arquivo está no formato CSV correto e tente novamente.")
    
    else:
        # Mostrar área de drop se não há arquivo
        st.markdown("""
        <div style="border: 2px dashed #ccc; padding: 2rem; text-align: center; border-radius: 10px; margin: 2rem 0;">
            <h3>📤 Arraste e solte um arquivo CSV aqui</h3>
            <p>ou clique no botão acima para selecionar um arquivo</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Botões para dados de exemplo
        st.markdown("### 🎯 Não tem dados? Experimente:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Gerar Dados de Exemplo", use_container_width=True):
                with st.spinner("Gerando dados de exemplo..."):
                    try:
                        from database import SampleDataGenerator, get_database
                        
                        db = get_database()
                        generator = SampleDataGenerator(db)
                        generator.generate_all_sample_data()
                        
                        st.success("✅ Dados de exemplo gerados!")
                        st.info("💡 Agora vá para o Dashboard para visualizar os dados.")
                        
                    except Exception as e:
                        st.error(f"Erro ao gerar dados: {str(e)}")
        
        with col2:
            if st.button("📋 Baixar Template CSV", use_container_width=True):
                # Criar template CSV
                template_data = {
                    'numero_apolice': ['POL001', 'POL002', 'POL003'],
                    'cep': ['01310-100', '04038-001', '22071-900'],
                    'tipo_residencia': ['casa', 'apartamento', 'sobrado'],
                    'valor_segurado': [350000.00, 180000.00, 420000.00],
                    'data_contratacao': ['2024-01-15', '2024-02-20', '2024-03-10'],
                    'latitude': [-23.5505, -23.5729, -22.9068],
                    'longitude': [-46.6333, -46.6411, -43.1729]
                }
                
                template_df = pd.DataFrame(template_data)
                csv_buffer = io.StringIO()
                template_df.to_csv(csv_buffer, index=False)
                
                st.download_button(
                    label="💾 Download Template",
                    data=csv_buffer.getvalue(),
                    file_name="template_apolices.csv",
                    mime="text/csv",
                    use_container_width=True
                )

if __name__ == "__main__":
    main()