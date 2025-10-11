import sqlite3

def execute_migration():
    """Executa a migração para criar a tabela cobertura_risco"""
    
    # Conectar ao banco
    conn = sqlite3.connect('database/radar_sinistro.db')
    cursor = conn.cursor()
    
    try:
        # Ler o arquivo de migração
        with open('database/migration_cobertura_risco.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Executar a migração
        cursor.executescript(migration_sql)
        conn.commit()
        
        print("✅ Migração executada com sucesso!")
        
        # Verificar se a tabela foi criada
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cobertura_risco'")
        if cursor.fetchone():
            print("✅ Tabela 'cobertura_risco' criada com sucesso!")
        else:
            print("❌ Erro: Tabela 'cobertura_risco' não foi criada")
            
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    execute_migration()
