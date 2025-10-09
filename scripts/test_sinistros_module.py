"""
Script para testar e demonstrar o novo módulo de Sinistros Históricos
"""

import sys
import os

# Adicionar o diretório raiz ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from database import get_database, CRUDOperations
from src.sinistros import SinistrosHistoricosGenerator, SinistrosAnalyzer, TiposSinistro

def test_sinistros_module():
    """Testa o módulo de sinistros históricos"""
    
    print("🔥 TESTANDO MÓDULO DE SINISTROS HISTÓRICOS")
    print("="*50)
    
    # Conectar ao banco
    db = get_database()
    crud = CRUDOperations(db)
    
    # Buscar apólices existentes
    all_policies = crud.get_all_apolices()
    print(f"📋 Encontradas {len(all_policies)} apólices")
    
    if not all_policies:
        print("❌ Nenhuma apólice encontrada. Execute primeiro o script de criação de apólices.")
        return
    
    # Converter para formato dict
    policies_dict = []
    for apolice in all_policies[:20]:  # Usar apenas 20 para teste
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
    
    print(f"🎯 Testando com {len(policies_dict)} apólices")
    
    # 1. Testar geração de sinistros
    print("\n1. 🌩️ TESTANDO GERAÇÃO DE SINISTROS")
    print("-" * 30)
    
    generator = SinistrosHistoricosGenerator()
    
    # Gerar sinistros inteligentes
    sinistros = generator.generate_sinistros_for_policies(policies_dict, num_sinistros=15)
    
    print(f"✅ {len(sinistros)} sinistros gerados com sucesso!")
    
    # Mostrar exemplos
    print("\n📋 Exemplos de sinistros gerados:")
    for i, sinistro in enumerate(sinistros[:3]):
        print(f"\n  Sinistro {i+1}:")
        print(f"    Tipo: {sinistro['tipo_sinistro']}")
        print(f"    Causa: {sinistro['causa']}")
        print(f"    Valor: R$ {sinistro['valor_prejuizo']:,.2f}")
        print(f"    Data: {sinistro['data_sinistro']}")
        print(f"    Coordenadas: {sinistro['latitude']:.4f}, {sinistro['longitude']:.4f}")
        print(f"    Condições: Temp {sinistro['temperatura_c']}°C, Chuva {sinistro['precipitacao_mm']}mm")
    
    # 2. Testar estatísticas
    print("\n2. 📊 TESTANDO ESTATÍSTICAS")
    print("-" * 30)
    
    stats = generator.get_estatisticas_geradas(sinistros)
    print(f"Total de sinistros: {stats['total']}")
    print(f"Valor total: R$ {stats['valor_total']:,.2f}")
    print(f"Valor médio: R$ {stats['valor_medio']:,.2f}")
    
    print("\nDistribuição por tipo:")
    for tipo, count in stats['distribuicao_tipos'].items():
        print(f"  {tipo}: {count} sinistros")
    
    # 3. Testar análise
    print("\n3. 🔍 TESTANDO ANÁLISE DE SINISTROS")
    print("-" * 30)
    
    analyzer = SinistrosAnalyzer()
    df = analyzer.load_sinistros(sinistros)
    patterns = analyzer.analyze_patterns()
    
    print(f"DataFrame carregado com {len(df)} registros")
    
    if 'temporal' in patterns:
        print(f"Mês com mais sinistros: {patterns['temporal'].get('meses_pico', 'N/A')}")
    
    if 'por_tipo' in patterns:
        print(f"Tipo mais frequente: {patterns['por_tipo'].get('tipo_mais_frequente', 'N/A')}")
        print(f"Tipo mais custoso: {patterns['por_tipo'].get('tipo_mais_custoso', 'N/A')}")
    
    # 4. Testar insights
    print("\n4. 💡 TESTANDO INSIGHTS")
    print("-" * 30)
    
    insights = analyzer.generate_risk_insights()
    
    if insights.get('alertas'):
        print("Alertas:")
        for alerta in insights['alertas']:
            print(f"  ⚠️ {alerta}")
    
    if insights.get('recomendacoes'):
        print("\nRecomendações:")
        for rec in insights['recomendacoes'][:3]:
            print(f"  💡 {rec}")
    
    # 5. Testar inserção no banco
    print("\n5. 💾 TESTANDO INSERÇÃO NO BANCO")
    print("-" * 30)
    
    inserted_count = 0
    for sinistro_data in sinistros[:5]:  # Inserir apenas 5 para teste
        try:
            sinistro_id = crud.create_sinistro(
                numero_apolice=sinistro_data['numero_apolice'],
                data_sinistro=sinistro_data['data_sinistro'],
                tipo_sinistro=sinistro_data['tipo_sinistro'],
                valor_prejuizo=sinistro_data['valor_prejuizo'],
                causa=sinistro_data['causa'],
                latitude=sinistro_data['latitude'],
                longitude=sinistro_data['longitude'],
                precipitacao_mm=sinistro_data['precipitacao_mm'],
                vento_kmh=sinistro_data['vento_kmh'],
                temperatura_c=sinistro_data['temperatura_c']
            )
            inserted_count += 1
            print(f"  ✅ Sinistro {sinistro_data['tipo_sinistro']} inserido com ID {sinistro_id}")
        except Exception as e:
            print(f"  ❌ Erro ao inserir sinistro: {e}")
    
    print(f"\n✅ {inserted_count} sinistros inseridos no banco com sucesso!")
    
    # 6. Verificar total no banco
    all_claims = crud.get_all_sinistros()
    print(f"📊 Total de sinistros no banco: {len(all_claims)}")
    
    print(f"\n🎉 TESTE DO MÓDULO DE SINISTROS CONCLUÍDO COM SUCESSO!")
    print("="*60)
    
    return {
        'sinistros_gerados': len(sinistros),
        'sinistros_inseridos': inserted_count,
        'total_banco': len(all_claims),
        'estatisticas': stats,
        'insights': insights
    }

if __name__ == "__main__":
    result = test_sinistros_module()