"""
Utilitários para formatação de dados e valores
"""
from typing import Union


def format_currency(value: Union[int, float]) -> str:
    """
    Formata um valor numérico como moeda brasileira
    
    Args:
        value: Valor numérico para formatação
        
    Returns:
        String formatada como moeda (ex: "R$ 1.234.567,89")
    """
    try:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "R$ 0,00"


def format_percentage(value: Union[int, float], decimals: int = 1) -> str:
    """
    Formata um valor como porcentagem
    
    Args:
        value: Valor numérico (0-1 ou 0-100)
        decimals: Número de casas decimais
        
    Returns:
        String formatada como porcentagem (ex: "45.6%")
    """
    try:
        # Se o valor for entre 0-1, assumir que é decimal
        if 0 <= value <= 1:
            percentage = value * 100
        else:
            percentage = value
        
        return f"{percentage:.{decimals}f}%"
    except (ValueError, TypeError):
        return "0%"


def format_score(score: Union[int, float]) -> str:
    """
    Formata um score de risco
    
    Args:
        score: Score numérico (0-100)
        
    Returns:
        String formatada (ex: "75.3/100")
    """
    try:
        return f"{score:.1f}/100"
    except (ValueError, TypeError):
        return "0.0/100"


def format_large_number(value: Union[int, float]) -> str:
    """
    Formata números grandes com sufixos (K, M, B)
    
    Args:
        value: Valor numérico
        
    Returns:
        String formatada (ex: "1.2M", "500K")
    """
    try:
        if value >= 1_000_000_000:
            return f"{value/1_000_000_000:.1f}B"
        elif value >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value/1_000:.1f}K"
        else:
            return f"{value:.0f}"
    except (ValueError, TypeError):
        return "0"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Trunca texto se exceder o comprimento máximo
    
    Args:
        text: Texto a ser truncado
        max_length: Comprimento máximo
        suffix: Sufixo a ser adicionado quando truncado
        
    Returns:
        Texto truncado se necessário
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_cep(cep: str) -> str:
    """
    Formata CEP no padrão brasileiro
    
    Args:
        cep: CEP sem formatação
        
    Returns:
        CEP formatado (ex: "01234-567")
    """
    if not cep:
        return ""
    
    # Remove tudo que não for dígito
    clean_cep = ''.join(filter(str.isdigit, cep))
    
    # Aplica formatação se tiver 8 dígitos
    if len(clean_cep) == 8:
        return f"{clean_cep[:5]}-{clean_cep[5:]}"
    
    return cep
