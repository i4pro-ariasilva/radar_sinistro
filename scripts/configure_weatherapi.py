"""
Script para configurar a chave da API do WeatherAPI.com
Execute este script para inserir sua chave de API de forma segura
"""

import os
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

def configure_weatherapi_key():
    """Configurar chave da API do WeatherAPI"""
    
    print("🌦️ Configuração da API do WeatherAPI.com")
    print("=" * 50)
    
    env_file = ROOT_DIR / '.env'
    
    # Verificar se arquivo .env existe
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado!")
        print("💡 Criando arquivo .env...")
        
        # Usar função segura para criar template
        try:
            from src.utils.file_utils import create_env_template
            if create_env_template(env_file):
                print("✅ Arquivo .env criado com sucesso!")
            else:
                print("❌ Erro ao criar arquivo .env")
                return False
        except Exception as e:
            print(f"❌ Erro ao importar utilitários: {e}")
            return False
    
    # Solicitar chave da API
    print("\n📋 Para obter sua chave da API:")
    print("1. Acesse: https://www.weatherapi.com")
    print("2. Crie uma conta gratuita")
    print("3. Acesse o painel e copie sua API Key")
    print()
    
    api_key = input("🔑 Cole sua chave da API do WeatherAPI aqui: ").strip()
    
    if not api_key or api_key == "your_weatherapi_key_here":
        print("❌ Chave inválida! Por favor, insira uma chave válida.")
        return False
    
    # Atualizar arquivo usando função segura
    try:
        from src.utils.file_utils import update_env_variable
        
        if update_env_variable(env_file, 'WEATHERAPI_KEY', api_key):
            print("✅ Chave da API configurada com sucesso!")
            print(f"📁 Salva em: {env_file}")
        else:
            print("❌ Erro ao salvar chave no arquivo .env")
            return False
        
    except Exception as e:
        print(f"❌ Erro ao atualizar arquivo: {e}")
        print("\n🔧 Configuração manual necessária:")
        print(f"1. Abra o arquivo: {env_file}")
        print(f"2. Adicione ou atualize: WEATHERAPI_KEY={api_key}")
        print("3. Salve o arquivo")
        return False
    
    # Testar conexão
    print("\n🔍 Testando conexão com a API...")
    
    try:
        from src.weather import WeatherClient
        
        # Criar cliente com a nova chave
        client = WeatherClient(api_key)
        
        # Testar conexão
        if client.test_connection():
            print("✅ Conexão com WeatherAPI funcionando!")
            
            # Fazer teste com dados brasileiros
            print("\n🇧🇷 Testando com dados do Brasil...")
            weather_data = client.get_current_weather("São Paulo, Brazil")
            
            if weather_data:
                print(f"🌡️ Temperatura em São Paulo: {weather_data.temperature_c}°C")
                print(f"🌤️ Condição: {weather_data.condition}")
                print(f"💧 Umidade: {weather_data.humidity_percent}%")
                print(f"⚠️ Nível de risco: {weather_data.get_risk_level()}")
            else:
                print("⚠️ Não foi possível obter dados de teste")
        else:
            print("❌ Erro na conexão com WeatherAPI!")
            print("💡 Verifique se a chave está correta e tente novamente")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar API: {e}")
        print("💡 A chave foi salva, mas houve erro no teste")
        return False
    
    print("\n🎉 Configuração concluída com sucesso!")
    print("\n💡 Próximos passos:")
    print("1. Execute: python main.py")
    print("2. Ou execute: streamlit run streamlit_app/app.py")
    print("3. Use a funcionalidade de análise climática")
    
    return True

def show_current_config():
    """Mostrar configuração atual"""
    
    print("🔧 Configuração Atual")
    print("=" * 30)
    
    env_file = ROOT_DIR / '.env'
    
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado")
        return
    
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Procurar chave da API
    for line in content.split('\n'):
        if line.startswith('WEATHERAPI_KEY='):
            key = line.split('=', 1)[1]
            if key and key != 'your_weatherapi_key_here':
                masked_key = f"{key[:8]}{'*' * (len(key) - 12)}{key[-4:]}" if len(key) > 12 else "***"
                print(f"🔑 Chave WeatherAPI: {masked_key}")
            else:
                print("❌ Chave WeatherAPI não configurada")
            break
    else:
        print("❌ Chave WeatherAPI não encontrada no arquivo")

def main():
    """Função principal"""
    
    print("🌦️ Configurador da API WeatherAPI")
    print("=" * 40)
    
    while True:
        print("\nEscolha uma opção:")
        print("1. Configurar nova chave da API")
        print("2. Ver configuração atual")
        print("3. Testar conexão")
        print("4. Sair")
        
        choice = input("\nDigite sua escolha (1-4): ").strip()
        
        if choice == '1':
            configure_weatherapi_key()
            break
        
        elif choice == '2':
            show_current_config()
        
        elif choice == '3':
            print("\n🔍 Testando conexão...")
            
            try:
                # Ler chave do .env
                env_file = ROOT_DIR / '.env'
                if not env_file.exists():
                    print("❌ Arquivo .env não encontrado")
                    continue
                
                with open(env_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                api_key = None
                for line in content.split('\n'):
                    if line.startswith('WEATHERAPI_KEY='):
                        api_key = line.split('=', 1)[1]
                        break
                
                if not api_key or api_key == 'your_weatherapi_key_here':
                    print("❌ Chave da API não configurada")
                    continue
                
                from src.weather import WeatherClient
                
                client = WeatherClient(api_key)
                
                if client.test_connection():
                    print("✅ Conexão funcionando!")
                else:
                    print("❌ Erro na conexão")
                    
            except Exception as e:
                print(f"❌ Erro: {e}")
        
        elif choice == '4':
            print("👋 Até logo!")
            break
        
        else:
            print("❌ Opção inválida! Tente novamente.")

if __name__ == "__main__":
    main()