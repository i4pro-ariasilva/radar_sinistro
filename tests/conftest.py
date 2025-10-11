"""
Configurações globais para testes do Radar de Sinistro
"""

import pytest
import os
import tempfile
import sqlite3
from pathlib import Path


@pytest.fixture(scope="session")
def project_root():
    """Fixture que retorna o diretório raiz do projeto"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="function")
def temp_db():
    """Fixture que cria um banco de dados temporário para testes"""
    # Criar arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = temp_file.name
    temp_file.close()
    
    # Conectar e criar estrutura básica
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Criar tabela de apólices para testes
    cursor.execute("""
        CREATE TABLE apolices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_apolice TEXT UNIQUE NOT NULL,
            segurado TEXT NOT NULL,
            cep TEXT NOT NULL,
            valor_segurado REAL NOT NULL,
            tipo_residencia TEXT NOT NULL,
            score_risco REAL,
            nivel_risco TEXT,
            probabilidade_sinistro REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Criar tabela de coberturas para testes
    cursor.execute("""
        CREATE TABLE cobertura_risco (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cd_produto INTEGER NOT NULL,
            cd_cobertura INTEGER NOT NULL,
            nome_cobertura TEXT NOT NULL,
            numero_apolice TEXT NOT NULL,
            score_risco REAL,
            nivel_risco TEXT,
            probabilidade REAL,
            fatores_risco TEXT,
            data_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(numero_apolice) REFERENCES apolices(numero_apolice)
        )
    """)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup - remover arquivo temporário
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def sample_policy_data():
    """Fixture com dados de exemplo para uma apólice"""
    return {
        "numero_apolice": "TEST-2025-001",
        "segurado": "João da Silva Teste",
        "cep": "01234567",
        "valor_segurado": 300000.0,
        "tipo_residencia": "Casa",
        "data_inicio": "2025-10-11"
    }


@pytest.fixture
def sample_batch_policies():
    """Fixture com dados de múltiplas apólices para teste em lote"""
    return [
        {
            "numero_apolice": "BATCH-001",
            "segurado": "Maria Silva",
            "cep": "01234567",
            "valor_segurado": 250000.0,
            "tipo_residencia": "Apartamento",
            "data_inicio": "2025-10-11"
        },
        {
            "numero_apolice": "BATCH-002", 
            "segurado": "Pedro Santos",
            "cep": "87654321",
            "valor_segurado": 400000.0,
            "tipo_residencia": "Casa",
            "data_inicio": "2025-10-11"
        }
    ]