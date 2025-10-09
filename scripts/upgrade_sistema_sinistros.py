"""
Script para integrar o novo módulo de Sinistros Históricos ao sistema principal
"""

import sys
import os

# Adicionar o diretório raiz ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from database import get_database, CRUDOperations
from src.sinistros import SinistrosHistoricosGenerator, SinistrosAnalyzer

def upgrade_sistema_sinistros():
    """Atualiza o sistema com o novo módulo de sinistros"""
    
    print("🚀 ATUALIZANDO SISTEMA COM MÓDULO DE SINISTROS HISTÓRICOS")
    print("="*60)
    
    # Conectar ao banco
    db = get_database()
    crud = CRUDOperations(db)
    
    # Buscar apólices existentes
    all_policies = crud.get_all_apolices()
    print(f"📋 Encontradas {len(all_policies)} apólices")
    
    if not all_policies:
        print("❌ Nenhuma apólice encontrada.")
        return
    
    # Converter para formato dict
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
    
    print(f"🎯 Processando {len(policies_dict)} apólices")
    
    # Gerar sinistros inteligentes
    print("\n🌩️ Gerando sinistros históricos inteligentes...")
    generator = SinistrosHistoricosGenerator()
    
    # Gerar 30% das apólices com sinistros (mais realista)
    num_sinistros = int(len(policies_dict) * 0.3)
    sinistros = generator.generate_sinistros_for_policies(policies_dict, num_sinistros)
    
    print(f"✅ {len(sinistros)} sinistros gerados!")
    
    # Inserir sinistros no banco
    print("\n💾 Inserindo sinistros no banco...")
    inserted_count = 0
    
    for sinistro_data in sinistros:
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
            
            if inserted_count % 10 == 0:
                print(f"  ✅ {inserted_count} sinistros inseridos...")
                
        except Exception as e:
            print(f"  ❌ Erro ao inserir sinistro: {e}")
    
    print(f"✅ {inserted_count} sinistros inseridos com sucesso!")
    
    # Gerar análise e estatísticas
    print("\n📊 Gerando análise e estatísticas...")
    analyzer = SinistrosAnalyzer()
    df = analyzer.load_sinistros(sinistros)
    
    # Obter estatísticas
    stats = generator.get_estatisticas_geradas(sinistros)
    patterns = analyzer.analyze_patterns()
    insights = analyzer.generate_risk_insights()
    
    # Relatório final
    print("\n📈 RELATÓRIO DE ATUALIZAÇÃO")
    print("-" * 40)
    print(f"💾 Apólices processadas: {len(policies_dict)}")
    print(f"🌩️ Sinistros gerados: {len(sinistros)}")
    print(f"💼 Sinistros inseridos: {inserted_count}")
    print(f"💰 Valor total dos sinistros: R$ {stats['valor_total']:,.2f}")
    print(f"📊 Valor médio por sinistro: R$ {stats['valor_medio']:,.2f}")
    
    print(f"\n🏆 TIPOS DE SINISTROS MAIS FREQUENTES:")
    for tipo, count in list(stats['distribuicao_tipos'].items())[:5]:
        print(f"  • {tipo}: {count} ocorrências")
    
    if 'temporal' in patterns:
        print(f"\n📅 Mês com mais sinistros: {patterns['temporal'].get('meses_pico', 'N/A')}")
    
    # Verificar total final no banco
    all_claims = crud.get_all_sinistros()
    print(f"\n🎯 Total final de sinistros no banco: {len(all_claims)}")
    
    # Exportar relatório
    print("\n📄 Exportando relatório de análise...")
    try:
        report_file = analyzer.export_analysis_report()
        print(f"✅ Relatório exportado: {report_file}")
    except Exception as e:
        print(f"⚠️ Erro ao exportar relatório: {e}")
    
    print(f"\n🎉 SISTEMA ATUALIZADO COM SUCESSO!")
    print("="*60)
    print("🌟 NOVAS FUNCIONALIDADES DISPONÍVEIS:")
    print("  • Sinistros com tipos expandidos (Queimadas, Tornado, Raio, etc.)")
    print("  • Geração baseada em sazonalidade")
    print("  • Condições climáticas realistas por tipo")
    print("  • Análise de padrões temporais e geográficos")
    print("  • Insights automáticos de risco")
    print("  • Relatórios exportáveis")
    
    return {
        'apolices_processadas': len(policies_dict),
        'sinistros_gerados': len(sinistros),
        'sinistros_inseridos': inserted_count,
        'total_banco': len(all_claims),
        'valor_total': stats['valor_total'],
        'estatisticas': stats,
        'insights': insights
    }

if __name__ == "__main__":
    result = upgrade_sistema_sinistros()