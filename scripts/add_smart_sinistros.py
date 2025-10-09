"""
Script para adicionar sinistros com coordenadas ao banco atualizado
"""

import sys
import os

# Adicionar o diretório raiz ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from database import get_database, CRUDOperations
from database.sample_data_generator import SampleDataGenerator

def add_smart_sinistros():
    """Adiciona sinistros com coordenadas inteligentes"""
    
    print("🌩️ Adicionando sinistros com coordenadas inteligentes...")
    
    db = get_database()
    crud = CRUDOperations(db)
    
    # Buscar apólices existentes
    all_policies = crud.get_all_apolices()
    print(f"📋 Encontradas {len(all_policies)} apólices")
    
    # Converter para formato dict para o gerador
    policies_dict = []
    for apolice in all_policies:
        policies_dict.append({
            'numero_apolice': apolice.numero_apolice,
            'cep': apolice.cep,
            'latitude': apolice.latitude,
            'longitude': apolice.longitude,
            'tipo_residencia': apolice.tipo_residencia,
            'valor_segurado': apolice.valor_segurado,
            'data_contratacao': apolice.data_contratacao.strftime('%Y-%m-%d') if hasattr(apolice.data_contratacao, 'strftime') else str(apolice.data_contratacao),
            'ativa': apolice.ativa
        })
    
    # Gerar sinistros
    generator = SampleDataGenerator()
    claims = generator.generate_sample_claims(policies_dict, 25)
    
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
    
    # Verificar resultado
    all_claims = crud.get_all_sinistros()
    print(f"📊 Total final: {len(all_claims)} sinistros no banco")

if __name__ == "__main__":
    add_smart_sinistros()