"""
Script para configuração inicial do ambiente
"""

import os
import sys
import subprocess
from pathlib import Path

def install_requirements():
    """Instala dependências do requirements.txt"""
    print("Instalando dependências...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✓ Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Erro ao instalar dependências: {e}")
        return False

def create_env_file():
    """Cria arquivo .env com configurações"""
    env_content = """# Configurações do Sistema de Radar de Sinistro

# API Keys (configure com suas chaves reais)
OPENWEATHER_API_KEY=your_api_key_here

# Configurações de desenvolvimento
FLASK_ENV=development
FLASK_DEBUG=true

# Configurações de banco
DATABASE_URL=sqlite:///radar_climatico.db

# Configurações de cache
CACHE_TIMEOUT_HOURS=1

# Configurações de log
LOG_LEVEL=INFO
"""
    
    env_path = Path(".env")
    if not env_path.exists():
        with open(env_path, 'w') as f:
            f.write(env_content)
        print("✓ Arquivo .env criado")
    else:
        print("! Arquivo .env já existe")

def setup_directories():
    """Cria estrutura de diretórios"""
    from config import create_directories
    
    try:
        create_directories()
        print("✓ Diretórios criados")
        return True
    except Exception as e:
        print(f"✗ Erro ao criar diretórios: {e}")
        return False

def initialize_database():
    """Inicializa banco de dados"""
    try:
        from database import get_database
        
        db = get_database()
        stats = db.get_database_stats()
        print(f"✓ Banco inicializado com {len(stats['tables'])} tabelas")
        return True
    except Exception as e:
        print(f"✗ Erro ao inicializar banco: {e}")
        return False

def generate_sample_data():
    """Gera dados de exemplo"""
    try:
        from database import SampleDataGenerator
        
        generator = SampleDataGenerator()
        
        # Gerar dados
        policies = generator.generate_sample_policies(100)
        claims = generator.generate_sample_claims(policies, 20)
        climate = generator.generate_climate_data(50)
        
        # Salvar
        generator.save_to_csv(policies, 'data/sample/sample_policies.csv')
        generator.save_to_csv(claims, 'data/sample/sample_claims.csv')
        generator.save_to_csv(climate, 'data/sample/sample_climate_data.csv')
        
        print("✓ Dados de exemplo gerados")
        return True
    except Exception as e:
        print(f"✗ Erro ao gerar dados: {e}")
        return False

def main():
    """Setup completo do ambiente"""
    print("=== SETUP DO SISTEMA DE RADAR DE SINISTRO ===\n")
    
    steps = [
        ("Instalando dependências", install_requirements),
        ("Criando arquivo .env", create_env_file),
        ("Configurando diretórios", setup_directories),
        ("Inicializando banco de dados", initialize_database),
        ("Gerando dados de exemplo", generate_sample_data)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"{step_name}...")
        try:
            if step_func():
                success_count += 1
            print()
        except Exception as e:
            print(f"✗ Erro em '{step_name}': {e}\n")
    
    print("=== RESULTADO DO SETUP ===")
    print(f"Concluído: {success_count}/{len(steps)} etapas")
    
    if success_count == len(steps):
        print("\n🎉 Setup concluído com sucesso!")
        print("\nPróximos passos:")
        print("1. Configure sua chave da API OpenWeather no arquivo .env")
        print("2. Execute: python main.py")
    else:
        print("\n⚠️  Setup incompleto. Verifique os erros acima.")

if __name__ == "__main__":
    main()
