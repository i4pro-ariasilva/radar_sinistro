"""
Utilitários para manipulação segura de arquivos
Lida com diferentes encodings de forma robusta
"""

import os
import chardet
from pathlib import Path
from typing import Optional, Tuple

def detect_file_encoding(file_path: Path) -> str:
    """
    Detecta o encoding de um arquivo
    
    Args:
        file_path: Caminho para o arquivo
        
    Returns:
        String com o encoding detectado
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            
        if raw_data:
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            
            # Fallbacks comuns
            if not encoding or encoding.lower() in ['ascii']:
                encoding = 'utf-8'
            elif encoding.lower().startswith('windows'):
                encoding = 'cp1252'
                
            return encoding
        else:
            return 'utf-8'
            
    except Exception:
        return 'utf-8'

def read_file_safe(file_path: Path) -> Tuple[str, str]:
    """
    Lê arquivo de forma segura, tentando diferentes encodings
    
    Args:
        file_path: Caminho para o arquivo
        
    Returns:
        Tupla (conteúdo, encoding_usado)
    """
    encodings_to_try = ['utf-8', 'cp1252', 'iso-8859-1', 'utf-16']
    
    # Primeiro tentar detectar automaticamente
    detected_encoding = detect_file_encoding(file_path)
    if detected_encoding not in encodings_to_try:
        encodings_to_try.insert(0, detected_encoding)
    
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content, encoding
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    # Se tudo falhar, tentar ler como binário e decodificar ignorando erros
    try:
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        content = raw_content.decode('utf-8', errors='replace')
        return content, 'utf-8'
    except Exception as e:
        raise Exception(f"Não foi possível ler o arquivo: {e}")

def write_file_safe(file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
    """
    Escreve arquivo de forma segura
    
    Args:
        file_path: Caminho para o arquivo
        content: Conteúdo a ser escrito
        encoding: Encoding a ser usado
        
    Returns:
        True se sucesso, False caso contrário
    """
    try:
        # Criar diretório se não existir
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding, newline='\n') as f:
            f.write(content)
        return True
        
    except Exception as e:
        print(f"Erro ao escrever arquivo: {e}")
        return False

def update_env_variable(env_file: Path, variable_name: str, variable_value: str) -> bool:
    """
    Atualiza variável no arquivo .env de forma segura
    
    Args:
        env_file: Caminho para o arquivo .env
        variable_name: Nome da variável
        variable_value: Valor da variável
        
    Returns:
        True se sucesso, False caso contrário
    """
    try:
        # Ler arquivo atual
        if env_file.exists():
            content, current_encoding = read_file_safe(env_file)
        else:
            content = ""
            current_encoding = 'utf-8'
        
        # Processar linhas
        lines = content.split('\n')
        updated_lines = []
        variable_updated = False
        
        for line in lines:
            if line.startswith(f'{variable_name}='):
                updated_lines.append(f'{variable_name}={variable_value}')
                variable_updated = True
            else:
                updated_lines.append(line)
        
        # Se variável não foi encontrada, adicionar
        if not variable_updated:
            # Procurar seção de API Keys para inserir no local correto
            api_section_found = False
            for i, line in enumerate(updated_lines):
                if '# API Keys' in line or 'API Keys' in line:
                    # Inserir após a linha de comentário
                    updated_lines.insert(i + 1, f'{variable_name}={variable_value}')
                    api_section_found = True
                    break
            
            if not api_section_found:
                # Se não encontrou seção, adicionar no início
                updated_lines.insert(0, f'{variable_name}={variable_value}')
        
        # Escrever arquivo atualizado
        new_content = '\n'.join(updated_lines)
        
        # Usar UTF-8 para garantir compatibilidade
        return write_file_safe(env_file, new_content, 'utf-8')
        
    except Exception as e:
        print(f"Erro ao atualizar variável {variable_name}: {e}")
        return False

def get_env_variable(env_file: Path, variable_name: str) -> Optional[str]:
    """
    Obtém valor de variável do arquivo .env
    
    Args:
        env_file: Caminho para o arquivo .env
        variable_name: Nome da variável
        
    Returns:
        Valor da variável ou None se não encontrada
    """
    try:
        if not env_file.exists():
            return None
            
        content, _ = read_file_safe(env_file)
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(f'{variable_name}='):
                return line.split('=', 1)[1].strip()
        
        return None
        
    except Exception as e:
        print(f"Erro ao ler variável {variable_name}: {e}")
        return None

def create_env_template(env_file: Path) -> bool:
    """
    Cria arquivo .env template se não existir
    
    Args:
        env_file: Caminho para o arquivo .env
        
    Returns:
        True se criado com sucesso
    """
    template_content = """# Configuracoes do Sistema de Radar de Sinistro

# API Keys (configure com suas chaves reais)
WEATHERAPI_KEY=your_weatherapi_key_here
OPENWEATHER_API_KEY=your_api_key_here

# Configuracoes de desenvolvimento
FLASK_ENV=development
FLASK_DEBUG=true

# Configuracoes de banco
DATABASE_URL=sqlite:///radar_climatico.db

# Configuracoes de cache
CACHE_TIMEOUT_HOURS=1

# Configuracoes de log
LOG_LEVEL=INFO

# Configuracoes de seguranca
SECRET_KEY=your_secret_key_here

# Configuracoes de rate limiting
RATE_LIMIT_PER_MINUTE=100
"""
    
    try:
        if not env_file.exists():
            return write_file_safe(env_file, template_content.strip())
        return True
        
    except Exception as e:
        print(f"Erro ao criar template .env: {e}")
        return False