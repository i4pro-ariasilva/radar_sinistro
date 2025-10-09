"""
Script para recriar banco de dados com apólices e sinistros mais inteligentes
"""

import sys
import os

# Adicionar o diretório raiz ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from database import get_database, CRUDOperations
from database.sample_data_generator import SampleDataGenerator
from datetime import datetime

def recreate_smart_database():
    """Recria o banco com dados mais inteligentes"""
    
    print("🚀 Iniciando recriação do banco de dados com coordenadas inteligentes...")
    
    # Conectar ao banco
    db = get_database()
    crud = CRUDOperations(db)
    
    print("📍 Gerando apólices com coordenadas terrestres...")
    
    # Gerar dados mais inteligentes
    generator = SampleDataGenerator()
    
    # Gerar 50 apólices com coordenadas terrestres
    policies = generator.generate_sample_policies(50)
    
    # Inserir apólices
    policy_count = 0
    for policy_data in policies:
        try:
            policy_id = crud.create_apolice(
                numero_apolice=policy_data['numero_apolice'],
                cep=policy_data['cep'],
                latitude=policy_data['latitude'],
                longitude=policy_data['longitude'],
                tipo_residencia=policy_data['tipo_residencia'],
                valor_segurado=policy_data['valor_segurado'],
                data_contratacao=policy_data['data_contratacao'],
                ativa=policy_data['ativa']
            )
            policy_count += 1
            print(f"  ✅ Apólice {policy_data['numero_apolice']} criada - {policy_data['latitude']:.4f}, {policy_data['longitude']:.4f}")
        except Exception as e:
            print(f"  ❌ Erro ao criar apólice {policy_data['numero_apolice']}: {e}")
    
    print(f"📋 {policy_count} apólices criadas com sucesso!")
    
    # Gerar sinistros baseados nas apólices
    print("🌩️ Gerando sinistros associados às apólices...")
    
    claims = generator.generate_sample_claims(policies, 20)
    
    # Inserir sinistros
    claim_count = 0
    for claim_data in claims:
        try:
            claim_id = crud.create_sinistro(
                numero_apolice=claim_data['numero_apolice'],
                data_sinistro=claim_data['data_sinistro'],
                tipo_sinistro=claim_data['tipo_sinistro'],
                valor_prejuizo=claim_data['valor_prejuizo'],
                causa=claim_data['causa'],
                latitude=claim_data['latitude'],
                longitude=claim_data['longitude'],
                precipitacao_mm=claim_data['precipitacao_mm'],
                vento_kmh=claim_data['vento_kmh'],
                temperatura_c=claim_data['temperatura_c']
            )
            claim_count += 1
            print(f"  ✅ Sinistro {claim_data['tipo_sinistro']} criado - {claim_data['latitude']:.4f}, {claim_data['longitude']:.4f}")
        except Exception as e:
            print(f"  ❌ Erro ao criar sinistro: {e}")
    
    print(f"⚡ {claim_count} sinistros criados com sucesso!")
    
    # Verificar resultado final
    all_policies = crud.get_all_apolices()
    all_claims = crud.get_all_sinistros()
    
    print(f"""
🎯 BANCO DE DADOS ATUALIZADO COM SUCESSO!
📊 Estatísticas finais:
   • {len(all_policies)} apólices no total
   • {len(all_claims)} sinistros no total
   • Coordenadas terrestres inteligentes
   • Sinistros associados às apólices
   
💡 Melhorias implementadas:
   ✅ Coordenadas baseadas em cidades reais
   ✅ Evita casas no mar
   ✅ Sinistros próximos às apólices
   ✅ Distribuição geográfica mais realista
   
🗺️ O mapa agora mostrará:
   🏠 Apólices em locais terrestres reais
   🚨 Sinistros próximos às respectivas apólices
   📍 Melhor visualização geográfica
""")

if __name__ == "__main__":
    recreate_smart_database()