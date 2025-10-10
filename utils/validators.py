"""
Utilitários para validação de dados
"""
import re
from typing import Any, List, Dict, Optional


def validate_cep(cep: str) -> bool:
    """
    Valida se um CEP está no formato correto
    
    Args:
        cep: CEP para validação
        
    Returns:
        True se válido, False caso contrário
    """
    if not cep:
        return False
    
    # Remove tudo que não for dígito
    clean_cep = ''.join(filter(str.isdigit, cep))
    
    # Verifica se tem exatamente 8 dígitos
    return len(clean_cep) == 8


def validate_email(email: str) -> bool:
    """
    Valida formato de email
    
    Args:
        email: Email para validação
        
    Returns:
        True se válido, False caso contrário
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """
    Valida formato de telefone brasileiro
    
    Args:
        phone: Telefone para validação
        
    Returns:
        True se válido, False caso contrário
    """
    if not phone:
        return False
    
    # Remove tudo que não for dígito
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    # Verifica se tem 10 ou 11 dígitos (com ou sem 9 no celular)
    return len(clean_phone) in [10, 11]


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Valida se todos os campos obrigatórios estão presentes
    
    Args:
        data: Dicionário com os dados
        required_fields: Lista de campos obrigatórios
        
    Returns:
        Lista de campos faltantes
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    return missing_fields


def validate_numeric_range(value: Any, min_val: Optional[float] = None, max_val: Optional[float] = None) -> bool:
    """
    Valida se um valor numérico está dentro de um range
    
    Args:
        value: Valor para validação
        min_val: Valor mínimo (opcional)
        max_val: Valor máximo (opcional)
        
    Returns:
        True se válido, False caso contrário
    """
    try:
        num_value = float(value)
        
        if min_val is not None and num_value < min_val:
            return False
        
        if max_val is not None and num_value > max_val:
            return False
        
        return True
    except (ValueError, TypeError):
        return False


def validate_policy_number(policy_number: str) -> bool:
    """
    Valida formato de número de apólice
    
    Args:
        policy_number: Número da apólice
        
    Returns:
        True se válido, False caso contrário
    """
    if not policy_number:
        return False
    
    # Padrão esperado: POL-YYYY-NNNNNN
    pattern = r'^POL-\d{4}-\d{6}$'
    return re.match(pattern, policy_number) is not None


def sanitize_input(input_str: str) -> str:
    """
    Sanitiza string de entrada removendo caracteres perigosos
    
    Args:
        input_str: String para sanitização
        
    Returns:
        String sanitizada
    """
    if not input_str:
        return ""
    
    # Remove caracteres potencialmente perigosos
    dangerous_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
    
    sanitized = input_str
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()


def validate_property_type(property_type: str) -> bool:
    """
    Valida se o tipo de propriedade é válido
    
    Args:
        property_type: Tipo de propriedade
        
    Returns:
        True se válido, False caso contrário
    """
    valid_types = ['casa', 'apartamento', 'sobrado', 'cobertura', 'kitnet']
    return property_type.lower() in valid_types
