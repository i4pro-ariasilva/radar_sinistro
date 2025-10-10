"""
Modelos de resposta para a API
"""

from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


class RiskResult(BaseModel):
    """Resultado do cálculo de risco"""
    numero_apolice: str
    score_risco: float
    nivel_risco: str
    probabilidade: float
    fatores_principais: List[Any] = []
    calculation_date: datetime


class PolicyRiskResponse(BaseModel):
    """Resposta para cálculo de risco individual"""
    success: bool
    data: Optional[RiskResult] = None
    error: Optional[str] = None
    message: str


class BatchRiskResult(BaseModel):
    """Resultado de uma apólice no lote"""
    numero_apolice: str
    success: bool
    risk_data: Optional[RiskResult] = None
    error: Optional[str] = None


class BatchRiskResponse(BaseModel):
    """Resposta para cálculo de risco em lote"""
    total_processed: int
    successful: int
    failed: int
    results: List[BatchRiskResult]
    processing_time: float


class PolicyInfo(BaseModel):
    """Informações básicas de uma apólice"""
    numero_apolice: str
    segurado: str
    cep: str
    valor_segurado: float
    tipo_residencia: str
    score_risco: float
    nivel_risco: str
    probabilidade_sinistro: float
    created_at: str


class RankingResponse(BaseModel):
    """Resposta para ranking de apólices"""
    total_count: int
    returned_count: int
    policies: List[PolicyInfo]
    filters_applied: dict


class ApiError(BaseModel):
    """Modelo padrão para erros da API"""
    error: str
    message: str
    timestamp: datetime
    path: str


class HealthResponse(BaseModel):
    """Resposta para health check"""
    status: str
    timestamp: datetime
    version: str
    database_status: str
    ml_model_status: str


class BaseResponse(BaseModel):
    """Resposta base para operações simples"""
    success: bool
    message: str
    error: Optional[str] = None


class PolicyResponse(BaseModel):
    """Resposta para consulta de apólice individual"""
    success: bool
    data: Optional[PolicyInfo] = None
    error: Optional[str] = None
    message: str


class PoliciesListResponse(BaseModel):
    """Resposta para listagem de apólices com paginação"""
    success: bool
    data: List[PolicyInfo]
    total: int
    page: int
    per_page: int
    message: str


class PolicyRankingResponse(BaseModel):
    """Resposta para ranking de apólices"""
    success: bool
    data: List[PolicyInfo]
    total_ranked: int
    order: str
    message: str