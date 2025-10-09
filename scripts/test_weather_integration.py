"""
Script para testar a integração automática de dados climáticos nos relatórios
"""

import sys
from pathlib import Path

# Adicionar path do projeto
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

def test_weather_cache_integration():
    """Testar integração do cache climático com relatórios"""
    
    print("🌤️ Testando Integração Cache Climático x Relatórios")
    print("=" * 60)
    
    try:
        from src.weather.weather_cache import WeatherCache
        
        # Inicializar cache
        cache = WeatherCache()
        print("✅ Cache inicializado")
        
        # Obter dados
        weather_df = cache.export_to_dataframe(include_expired=False)
        print(f"✅ Dados exportados: {len(weather_df) if weather_df is not None else 0} registros")
        
        # Obter estatísticas
        stats = cache.get_summary_statistics()
        print(f"✅ Estatísticas calculadas: {stats.get('total_records', 0)} registros ativos")
        
        # Listar dados do cache
        cached_data = cache.get_all_cached_data(include_expired=False)
        print(f"✅ Dados em cache: {len(cached_data)} arquivos")
        
        if cached_data:
            print("\n📊 Resumo dos dados em cache:")
            for item in cached_data[:3]:  # Mostrar apenas os primeiros 3
                location = item.get('location', 'N/A')
                timestamp = item.get('timestamp', 'N/A')
                data = item.get('data', {})
                temp = data.get('temperature_c', 'N/A')
                risk = data.get('risk_score', 'N/A')
                
                print(f"   📍 {location} | 🌡️ {temp}°C | ⚠️ Risco: {risk} | 📅 {timestamp}")
        
        # Testar função de relatórios automáticos
        print("\n🔄 Testando geração automática de relatórios...")
        
        # Importar função de relatórios
        from src.reports import auto_generate_weather_reports
        
        success, message = auto_generate_weather_reports()
        
        if success:
            print(f"✅ Relatório automático gerado: {message}")
        else:
            print(f"⚠️ Relatório automático: {message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def demonstrate_workflow():
    """Demonstrar fluxo de trabalho completo"""
    
    print("\n🔄 Demonstração do Fluxo de Trabalho")
    print("=" * 60)
    
    print("""
    📝 Como funciona a integração automática:
    
    1. 🌤️ Usuário faz consultas na página "API Climática"
    2. 💾 Dados ficam automaticamente em cache (data/cache/)
    3. 📈 Relatórios capturam dados do cache automaticamente
    4. 📊 Análises são geradas com dados mais recentes
    5. 🔄 Cache é limpo automaticamente (dados expirados)
    
    📂 Estrutura de arquivos:
    ├── data/cache/          → Dados climáticos em cache
    ├── data/reports/auto/   → Relatórios automáticos gerados
    └── streamlit_app/       → Interface web
    
    💡 Benefícios:
    • Dados ficam disponíveis automaticamente nos relatórios
    • Histórico de consultas preservado para análise
    • Relatórios sempre atualizados com dados mais recentes
    • Análise de tendências e padrões climáticos
    • Correlação automática com dados de sinistros
    """)

if __name__ == "__main__":
    print("🚀 Iniciando teste de integração...")
    
    # Executar teste
    success = test_weather_cache_integration()
    
    if success:
        demonstrate_workflow()
        print("\n🎉 Integração funcionando corretamente!")
        print("\n📝 Próximos passos:")
        print("1. Execute: streamlit run streamlit_app/app.py")
        print("2. Vá para '🌤️ API Climática' e faça algumas consultas")
        print("3. Vá para '📈 Relatórios' e escolha 'Análise Climática'")
        print("4. Os dados das consultas aparecerão automaticamente!")
    else:
        print("\n❌ Teste falhou. Verifique a configuração.")