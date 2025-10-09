"""
Demonstração das funcionalidades da API climática
Exemplos de uso da integração com WeatherAPI.com
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

def demo_weather_basic():
    """Demonstração básica da API climática"""
    
    print("🌦️ Demo: Funcionalidades Básicas da API Climática")
    print("=" * 60)
    
    try:
        from src.weather import WeatherClient
        from config.settings import API_CONFIG
        
        # Obter chave da API
        api_key = API_CONFIG['weather']['weatherapi_key']
        
        if not api_key or api_key == 'your_weatherapi_key_here':
            print("❌ Chave da API não configurada!")
            print("💡 Execute: python scripts/configure_weatherapi.py")
            return False
        
        # Criar cliente
        client = WeatherClient(api_key, use_cache=True)
        print(f"✅ Cliente criado: {client}")
        
        # Teste 1: Dados por cidade
        print("\n📍 Teste 1: Dados por cidade")
        print("-" * 30)
        
        weather_sp = client.get_current_weather("São Paulo, Brazil")
        if weather_sp:
            print(f"🏙️ {weather_sp}")
            print(f"   🌡️ Temperatura: {weather_sp.temperature_c}°C (sensação: {weather_sp.feels_like_c}°C)")
            print(f"   💧 Umidade: {weather_sp.humidity_percent}%")
            print(f"   💨 Vento: {weather_sp.wind_speed_kph} km/h ({weather_sp.wind_direction})")
            print(f"   🌧️ Precipitação: {weather_sp.precipitation_mm} mm")
            print(f"   ⚠️ Risco climático: {weather_sp.get_risk_level()} ({weather_sp.get_risk_score():.2f})")
        
        # Teste 2: Dados por CEP
        print("\n📮 Teste 2: Dados por CEP")
        print("-" * 30)
        
        ceps_teste = ["01310-100", "04038-001", "22071-900"]  # São Paulo, São Paulo, Rio de Janeiro
        
        for cep in ceps_teste:
            weather_cep = client.get_weather_by_cep(cep)
            if weather_cep:
                print(f"📮 CEP {cep}: {weather_cep.temperature_c}°C, {weather_cep.condition}")
            else:
                print(f"❌ Erro ao obter dados para CEP {cep}")
        
        # Teste 3: Dados por coordenadas
        print("\n🗺️ Teste 3: Dados por coordenadas")
        print("-" * 30)
        
        # Coordenadas de Brasília
        weather_coords = client.get_weather_by_coordinates(-15.7942, -47.8822)
        if weather_coords:
            print(f"🏛️ Brasília: {weather_coords}")
        
        # Teste 4: Múltiplas localizações
        print("\n🌍 Teste 4: Múltiplas localizações")
        print("-" * 30)
        
        locations = [
            "Rio de Janeiro, Brazil",
            "Belo Horizonte, Brazil", 
            "Salvador, Brazil"
        ]
        
        weather_multiple = client.get_weather_for_multiple_locations(locations)
        
        for location, weather in weather_multiple.items():
            if weather:
                risk_emoji = "🟢" if weather.get_risk_score() < 0.3 else "🟡" if weather.get_risk_score() < 0.6 else "🔴"
                print(f"{risk_emoji} {location}: {weather.temperature_c}°C, {weather.condition}")
            else:
                print(f"❌ {location}: Erro ao obter dados")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na demonstração: {e}")
        return False

def demo_weather_with_apolices():
    """Demonstração usando dados de apólices do banco"""
    
    print("\n🏠 Demo: Integração com Dados de Apólices")
    print("=" * 50)
    
    try:
        from src.weather import WeatherClient
        from config.settings import API_CONFIG
        from database import get_database, CRUDOperations
        
        # Verificar se há dados no banco
        db = get_database()
        crud = CRUDOperations(db)
        
        apolices = crud.get_all_apolices()
        
        if not apolices:
            print("⚠️ Nenhuma apólice encontrada no banco de dados")
            print("💡 Execute: python main.py -> Opção 2 (Gerar dados de exemplo)")
            return False
        
        print(f"📋 Encontradas {len(apolices)} apólices no banco")
        
        # Criar cliente de clima
        api_key = API_CONFIG['weather']['weatherapi_key']
        client = WeatherClient(api_key, use_cache=True)
        
        # Pegar amostra de apólices (máximo 5 para não sobrecarregar API)
        sample_apolices = apolices[:5]
        
        print(f"\n🧪 Analisando clima para {len(sample_apolices)} apólices...")
        
        weather_data = client.get_weather_for_apolices(sample_apolices)
        
        print("\n📊 Resultados da Análise Climática:")
        print("-" * 50)
        
        for apolice in sample_apolices:
            cep = apolice.cep
            weather = weather_data.get(cep)
            
            if weather:
                risk_score = weather.get_risk_score()
                risk_level = weather.get_risk_level()
                risk_emoji = weather.get_condition_emoji()
                
                print(f"\n🏠 Apólice: {apolice.numero_apolice}")
                print(f"   📮 CEP: {cep}")
                print(f"   🏠 Tipo: {apolice.tipo_residencia}")
                print(f"   💰 Valor: R$ {float(apolice.valor_segurado or 0):,.2f}")
                print(f"   {risk_emoji} Clima: {weather.temperature_c}°C, {weather.condition}")
                print(f"   ⚠️ Risco: {risk_level} ({risk_score:.2f})")
                
                # Alerta se risco alto
                if risk_score > 0.6:
                    print(f"   🚨 ALERTA: Condições climáticas de alto risco!")
            else:
                print(f"\n❌ Apólice {apolice.numero_apolice} (CEP {cep}): Erro ao obter dados climáticos")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na demonstração: {e}")
        return False

def demo_weather_cache():
    """Demonstração do sistema de cache"""
    
    print("\n💾 Demo: Sistema de Cache Inteligente")
    print("=" * 40)
    
    try:
        from src.weather import WeatherClient, WeatherCache
        from config.settings import API_CONFIG
        import time
        
        api_key = API_CONFIG['weather']['weatherapi_key']
        client = WeatherClient(api_key, use_cache=True)
        
        location = "São Paulo, Brazil"
        
        # Primeira consulta (vai para API)
        print(f"🌐 Primeira consulta para {location}...")
        start_time = time.time()
        weather1 = client.get_current_weather(location)
        time1 = time.time() - start_time
        
        if weather1:
            print(f"✅ Dados obtidos em {time1:.2f}s")
            print(f"   🌡️ Temperatura: {weather1.temperature_c}°C")
        
        # Segunda consulta (deve usar cache)
        print(f"\n💾 Segunda consulta para {location} (deve usar cache)...")
        start_time = time.time()
        weather2 = client.get_current_weather(location)
        time2 = time.time() - start_time
        
        if weather2:
            print(f"✅ Dados obtidos em {time2:.2f}s")
            print(f"   🌡️ Temperatura: {weather2.temperature_c}°C")
            
            if time2 < time1 * 0.5:  # Se foi significativamente mais rápido
                print("   💾 Cache funcionando! Consulta muito mais rápida.")
            else:
                print("   🌐 Dados vieram da API (cache pode ter expirado)")
        
        # Informações do cache
        cache_info = client.get_cache_info()
        print(f"\n📊 Informações do Cache:")
        print(f"   📁 Arquivos: {cache_info.get('total_files', 0)}")
        print(f"   💿 Tamanho: {cache_info.get('total_size_mb', 0)} MB")
        print(f"   ⏰ Duração: {cache_info.get('cache_duration_hours', 0)} horas")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na demonstração: {e}")
        return False

def demo_weather_analysis():
    """Demonstração de análise avançada de dados climáticos"""
    
    print("\n📈 Demo: Análise Avançada de Dados Climáticos")
    print("=" * 50)
    
    try:
        from src.weather import WeatherClient
        from config.settings import API_CONFIG
        
        api_key = API_CONFIG['weather']['weatherapi_key']
        client = WeatherClient(api_key, use_cache=True)
        
        # Cidades para análise comparativa
        cities = [
            "São Paulo, Brazil",
            "Rio de Janeiro, Brazil", 
            "Belo Horizonte, Brazil",
            "Salvador, Brazil",
            "Recife, Brazil"
        ]
        
        print(f"🔍 Analisando {len(cities)} cidades brasileiras...")
        
        weather_data = []
        
        for city in cities:
            weather = client.get_current_weather(city)
            if weather:
                weather_data.append(weather)
        
        if not weather_data:
            print("❌ Não foi possível obter dados para análise")
            return False
        
        # Análise estatística
        temps = [w.temperature_c for w in weather_data]
        humidity = [w.humidity_percent for w in weather_data]
        wind_speeds = [w.wind_speed_kph for w in weather_data]
        risk_scores = [w.get_risk_score() for w in weather_data]
        
        print(f"\n📊 Análise Estatística ({len(weather_data)} cidades):")
        print("-" * 40)
        print(f"🌡️ Temperatura:")
        print(f"   📈 Máxima: {max(temps):.1f}°C")
        print(f"   📉 Mínima: {min(temps):.1f}°C")
        print(f"   📊 Média: {sum(temps)/len(temps):.1f}°C")
        
        print(f"\n💧 Umidade:")
        print(f"   📈 Máxima: {max(humidity)}%")
        print(f"   📉 Mínima: {min(humidity)}%")
        print(f"   📊 Média: {sum(humidity)/len(humidity):.1f}%")
        
        print(f"\n💨 Velocidade do Vento:")
        print(f"   📈 Máxima: {max(wind_speeds):.1f} km/h")
        print(f"   📉 Mínima: {min(wind_speeds):.1f} km/h")
        print(f"   📊 Média: {sum(wind_speeds)/len(wind_speeds):.1f} km/h")
        
        print(f"\n⚠️ Score de Risco:")
        print(f"   📈 Máximo: {max(risk_scores):.2f}")
        print(f"   📉 Mínimo: {min(risk_scores):.2f}")
        print(f"   📊 Médio: {sum(risk_scores)/len(risk_scores):.2f}")
        
        # Ranking por risco
        weather_data.sort(key=lambda x: x.get_risk_score(), reverse=True)
        
        print(f"\n🏆 Ranking por Risco Climático:")
        print("-" * 40)
        
        for i, weather in enumerate(weather_data, 1):
            risk_emoji = "🔴" if weather.get_risk_score() > 0.6 else "🟡" if weather.get_risk_score() > 0.3 else "🟢"
            print(f"{i}. {risk_emoji} {weather.location}: {weather.get_risk_level()} ({weather.get_risk_score():.2f})")
            print(f"   {weather.get_condition_emoji()} {weather.condition}, {weather.temperature_c}°C")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na demonstração: {e}")
        return False

def main():
    """Função principal - executar todas as demonstrações"""
    
    print("🌦️ DEMONSTRAÇÃO COMPLETA - API CLIMÁTICA")
    print("=" * 60)
    print(f"⏰ Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    demos = [
        ("Funcionalidades Básicas", demo_weather_basic),
        ("Integração com Apólices", demo_weather_with_apolices),
        ("Sistema de Cache", demo_weather_cache),
        ("Análise Avançada", demo_weather_analysis)
    ]
    
    success_count = 0
    
    for demo_name, demo_func in demos:
        print(f"\n🎯 Executando: {demo_name}")
        try:
            if demo_func():
                success_count += 1
                print(f"✅ {demo_name}: SUCESSO")
            else:
                print(f"❌ {demo_name}: FALHOU")
        except Exception as e:
            print(f"❌ {demo_name}: ERRO - {e}")
        
        print("-" * 60)
    
    print(f"\n📊 RESUMO DA DEMONSTRAÇÃO")
    print(f"✅ Sucessos: {success_count}/{len(demos)}")
    print(f"⏰ Fim: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    if success_count == len(demos):
        print("\n🎉 Todas as demonstrações foram executadas com sucesso!")
        print("💡 A integração com WeatherAPI está funcionando perfeitamente!")
    else:
        print(f"\n⚠️ {len(demos) - success_count} demonstração(ões) falharam.")
        print("💡 Verifique a configuração da API e tente novamente.")

if __name__ == "__main__":
    main()