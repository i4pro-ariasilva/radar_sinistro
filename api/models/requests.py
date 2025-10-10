"""
Modelos de requisição para a API
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class PolicyRequest(BaseModel):
    """Modelo para requisição de apólice individual"""
    numero_apolice: str = Field(..., description="Número único da apólice")
    segurado: str = Field(..., min_length=3, description="Nome completo do segurado")
    cep: str = Field(..., min_length=8, max_length=9, description="CEP (8 dígitos)")
    valor_segurado: float = Field(..., gt=0, description="Valor segurado em reais")
    tipo_residencia: str = Field(..., description="Tipo de residência")
    data_inicio: str = Field(..., description="Data de início da apólice (YYYY-MM-DD)")

    class Config:
        json_schema_extra = {
            "example": {
                "numero_apolice": "POL-2024-001",
                "segurado": "João Silva Santos",
                "cep": "01234567",
                "valor_segurado": 300000.0,
                "tipo_residencia": "Casa",
                "data_inicio": "2024-10-07"
            }
        }


class BatchPolicyRequest(BaseModel):
    """Modelo para requisição de lote de apólices"""
    policies: List[PolicyRequest] = Field(..., min_items=1, max_items=100)

    class Config:
        json_schema_extra = {
            "example": {
                "policies": [
                    {
                        "numero_apolice": "POL-2024-001",
                        "segurado": "João Silva Santos",
                        "cep": "01234567",
                        "valor_segurado": 300000.0,
                        "tipo_residencia": "Casa",
                        "data_inicio": "2024-10-07"
                    },
                    {
                        "numero_apolice": "POL-2024-002",
                        "segurado": "Maria Oliveira",
                        "cep": "89012345",
                        "valor_segurado": 450000.0,
                        "tipo_residencia": "Apartamento",
                        "data_inicio": "2024-10-07"
                    }
                ]
            }
        }


class RankingFilters(BaseModel):
    """Filtros para ranking de apólices"""
    limit: Optional[int] = Field(50, ge=1, le=1000, description="Número máximo de resultados")
    risk_level: Optional[str] = Field(None, description="Filtrar por nível de risco")
    min_value: Optional[float] = Field(None, ge=0, description="Valor mínimo segurado")
    max_value: Optional[float] = Field(None, ge=0, description="Valor máximo segurado")
    search: Optional[str] = Field(None, description="Buscar por número da apólice")