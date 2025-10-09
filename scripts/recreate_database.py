"""
Script para recriar o banco de dados e gerar dados de exemplo
"""

import os
import sys
from pathlib import Path

# Adicionar path do projeto
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

def recreate_database():
    """Recriar banco de dados do zero"""
    
    print("🔄 Recriando banco de dados...")
    
    try:
        # Remover banco existente se houver
        db_path = ROOT_DIR / 'radar_climatico.db'
        if db_path.exists():
            db_path.unlink()
            print("✅ Banco antigo removido")
        
        # Criar novo banco
        from database import Database
        db = Database(str(db_path))
        print("✅ Novo banco criado")
        
        # Testar conexão
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"✅ Tabelas criadas: {[t[0] for t in tables]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao recriar banco: {e}")
        return False

def generate_sample_data():
    """Gerar dados de exemplo"""
    
    print("\n📊 Gerando dados de exemplo...")
    
    try:
        from database.sample_data_generator import SampleDataGenerator
        from database import get_database, CRUDOperations
        
        # Conectar ao banco
        db = get_database()
        crud = CRUDOperations(db)
        
        # Gerar dados
        generator = SampleDataGenerator()
        
        # Gerar apólices
        print("📋 Gerando apólices...")
        policies = generator.generate_sample_policies(50)  # 50 apólices
        
        for policy in policies:
            try:
                crud.create_apolice(
                    numero_apolice=policy['numero_apolice'],
                    cep=policy['cep'],
                    tipo_residencia=policy['tipo_residencia'],
                    valor_segurado=policy['valor_segurado'],
                    data_contratacao=policy['data_contratacao'],
                    latitude=policy.get('latitude'),
                    longitude=policy.get('longitude')
                )
            except Exception as e:
                print(f"⚠️ Erro ao inserir apólice {policy['numero_apolice']}: {e}")
        
        print(f"✅ {len(policies)} apólices criadas")
        
        # Gerar alguns sinistros
        print("⚠️ Gerando sinistros...")
        claims = generator.generate_sample_claims(policies, 15)  # Usar apólices geradas
        
        for claim in claims:
            try:
                crud.create_sinistro(
                    numero_apolice=claim['numero_apolice'],
                    data_sinistro=claim['data_sinistro'],
                    tipo_sinistro=claim['tipo_sinistro'],
                    valor_prejuizo=claim['valor_prejuizo'],
                    causa=claim.get('causa'),
                    condicoes_climaticas=claim.get('condicoes_climaticas')
                )
            except Exception as e:
                print(f"⚠️ Erro ao inserir sinistro: {e}")
        
        print(f"✅ {len(claims)} sinistros criados")
        
        # Verificar dados criados
        all_policies = crud.get_all_apolices()
        all_claims = crud.get_all_sinistros()
        
        print(f"\n📊 Resumo final:")
        print(f"   📋 Apólices no banco: {len(all_policies)}")
        print(f"   ⚠️ Sinistros no banco: {len(all_claims)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao gerar dados: {e}")
        return False

def main():
    """Função principal"""
    
    print("🚀 Iniciando recreação do banco de dados...")
    print("=" * 50)
    
    # Etapa 1: Recriar banco
    if not recreate_database():
        print("❌ Falha na criação do banco. Parando.")
        return
    
    # Etapa 2: Gerar dados
    if not generate_sample_data():
        print("❌ Falha na geração de dados. Banco criado mas vazio.")
        return
    
    print("\n🎉 Processo concluído com sucesso!")
    print("\n📝 Próximos passos:")
    print("1. Execute: streamlit run streamlit_app/app.py")
    print("2. Vá para '📈 Relatórios' para ver os dados")
    print("3. Teste todas as funcionalidades")

if __name__ == "__main__":
    main()