"""
Modelos de dados para o Sistema de Radar de Sinistro
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TipoResidencia(Enum):
    CASA = "casa"
    APARTAMENTO = "apartamento"
    SOBRADO = "sobrado"


class NivelRisco(Enum):
    BAIXO = "baixo"
    MEDIO = "medio"
    ALTO = "alto"
    CRITICO = "critico"


@dataclass
class Apolice:
    """Modelo para dados de apólices de seguro"""
    numero_apolice: str
    segurado: str
    cep: str
    tipo_residencia: str
    valor_segurado: float
    data_contratacao: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ativa: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = field(default_factory=datetime.now)
    # Campos estendidos (podem ser preenchidos após cálculo de risco)
    data_inicio: Optional[datetime] = None
    score_risco: Optional[float] = 0.0
    nivel_risco: Optional[str] = 'baixo'
    probabilidade_sinistro: Optional[float] = 0.0
    
    def __post_init__(self):
        # Validações básicas
        if not self.segurado or len(self.segurado.strip()) < 3:
            raise ValueError("Nome do segurado é obrigatório e deve ter pelo menos 3 caracteres")
        
        if self.valor_segurado <= 0:
            raise ValueError("Valor segurado deve ser maior que zero")
        
        if self.tipo_residencia not in [t.value for t in TipoResidencia]:
            raise ValueError(f"Tipo de residência deve ser um dos: {[t.value for t in TipoResidencia]}")
        
        # Validação básica de CEP (formato XXXXX-XXX)
        if len(self.cep.replace('-', '')) != 8:
            raise ValueError("CEP deve ter 8 dígitos")

        # Validar nível de risco se já preenchido (flexível, ignora se None)
        if self.nivel_risco and self.nivel_risco not in [n.value for n in NivelRisco]:
            raise ValueError(f"Nível de risco inválido: {self.nivel_risco}")


@dataclass
class SinistroHistorico:
    """Modelo para dados históricos de sinistros"""
    apolice_id: int
    data_sinistro: datetime
    tipo_sinistro: str
    valor_prejuizo: float
    causa: Optional[str] = None
    condicoes_climaticas: Optional[str] = None
    precipitacao_mm: Optional[float] = None
    vento_kmh: Optional[float] = None
    temperatura_c: Optional[float] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if self.valor_prejuizo < 0:
            raise ValueError("Valor do prejuízo não pode ser negativo")


@dataclass
class PrevisaoRisco:
    """Modelo para previsões de risco"""
    apolice_id: int
    data_previsao: datetime
    score_risco: float
    nivel_risco: str
    fatores_risco: Optional[str] = None
    dados_climaticos: Optional[str] = None
    modelo_versao: Optional[str] = "1.0"
    id: Optional[int] = None
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not (0 <= self.score_risco <= 100):
            raise ValueError("Score de risco deve estar entre 0 e 100")
        
        if self.nivel_risco not in [n.value for n in NivelRisco]:
            raise ValueError(f"Nível de risco deve ser um dos: {[n.value for n in NivelRisco]}")


@dataclass
class DadoClimatico:
    """Modelo para dados climáticos coletados"""
    latitude: float
    longitude: float
    data_coleta: datetime
    fonte: str
    temperatura_c: Optional[float] = None
    precipitacao_mm: Optional[float] = None
    vento_kmh: Optional[float] = None
    umidade_percent: Optional[float] = None
    pressao_hpa: Optional[float] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = field(default_factory=datetime.now)


@dataclass
class ApoliceAtiva:
    """Modelo para view de apólices ativas com estatísticas"""
    id: int
    numero_apolice: str
    cep: str
    latitude: Optional[float]
    longitude: Optional[float]
    tipo_residencia: str
    valor_segurado: float
    data_contratacao: datetime
    total_sinistros: int
    valor_total_sinistros: float


@dataclass
class PrevisaoRecente:
    """Modelo para view de previsões recentes"""
    id: int
    apolice_id: int
    data_previsao: datetime
    score_risco: float
    nivel_risco: str
    numero_apolice: str
    cep: str
    tipo_residencia: str
    valor_segurado: float


@dataclass
class RegionBlock:
    """Modelo para bloqueio por prefixo de CEP."""
    cep_prefix: str
    blocked: bool = True
    reason: str = ""
    severity: int = 1  # 1=normal,2=alto,3=critico
    scope: str = "residencial"  # pode ser 'global' ou outro produto futuramente
    active: bool = True
    created_at: Optional[datetime] = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = field(default_factory=datetime.now)
    updated_by: Optional[str] = None
    id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cep_prefix": self.cep_prefix,
            "blocked": self.blocked,
            "reason": self.reason,
            "severity": self.severity,
            "scope": self.scope,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updated_by": self.updated_by,
        }

    def is_effective(self) -> bool:
        """Retorna True se o bloqueio deve ser aplicado (ativo e marcado como bloqueado)."""
        return self.active and self.blocked



# Funções utilitárias para conversão
def determinar_nivel_risco(score: float) -> str:
    """Determina o nível de risco baseado no score"""
    if score < 25:
        return NivelRisco.BAIXO.value
    elif score < 50:
        return NivelRisco.MEDIO.value
    elif score < 75:
        return NivelRisco.ALTO.value
    else:
        return NivelRisco.CRITICO.value


def validar_cep(cep: str) -> bool:
    """Valida formato de CEP brasileiro"""
    import re
    pattern = r'^\d{5}-?\d{3}$'
    return bool(re.match(pattern, cep))


def normalizar_cep(cep: str) -> str:
    """Normaliza CEP para formato XXXXX-XXX"""
    cep_limpo = ''.join(filter(str.isdigit, cep))
    if len(cep_limpo) == 8:
        return f"{cep_limpo[:5]}-{cep_limpo[5:]}"
    raise ValueError("CEP inválido")