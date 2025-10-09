"""
Script para atualizar o esquema do banco de dados adicionando coordenadas aos sinistros
"""

import sys
import os

# Adicionar o diretório raiz ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from database import get_database

def update_database_schema():
    """Atualiza o esquema do banco adicionando coordenadas aos sinistros"""
    
    print("🔧 Atualizando esquema do banco de dados...")
    
    db = get_database()
    
    # Adicionar colunas de coordenadas à tabela sinistros_historicos
    alter_queries = [
        "ALTER TABLE sinistros_historicos ADD COLUMN latitude REAL",
        "ALTER TABLE sinistros_historicos ADD COLUMN longitude REAL",
        "ALTER TABLE sinistros_historicos ADD COLUMN precipitacao_mm REAL",
        "ALTER TABLE sinistros_historicos ADD COLUMN vento_kmh REAL", 
        "ALTER TABLE sinistros_historicos ADD COLUMN temperatura_c REAL"
    ]
    
    for query in alter_queries:
        try:
            db.execute_command(query)
            column_name = query.split("ADD COLUMN ")[1].split(" ")[0]
            print(f"  ✅ Coluna {column_name} adicionada com sucesso")
        except Exception as e:
            column_name = query.split("ADD COLUMN ")[1].split(" ")[0]
            if "duplicate column name" in str(e).lower():
                print(f"  ℹ️ Coluna {column_name} já existe")
            else:
                print(f"  ❌ Erro ao adicionar coluna {column_name}: {e}")
    
    print("✅ Esquema do banco atualizado com sucesso!")

if __name__ == "__main__":
    update_database_schema()