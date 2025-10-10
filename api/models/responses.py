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


# ============================================================
# MODELOS PARA COBERTURAS
# ============================================================

class CoberturaInfo(BaseModel):
    """Informações básicas de uma cobertura"""
    cd_cobertura: int
    cd_produto: int
    nm_cobertura: str
    dv_basica: bool
    created_at: Optional[str] = None


class CoberturaRiscoInfo(BaseModel):
    """Informações de risco de uma cobertura"""
    id: int
    nr_apolice: str
    cd_cobertura: int
    cd_produto: int
    nm_cobertura: str
    dv_basica: bool
    score_risco: float
    nivel_risco: str
    probabilidade: float
    modelo_usado: Optional[str] = None
    versao_modelo: Optional[str] = None
    fatores_risco: Optional[str] = None
    dados_climaticos: Optional[str] = None
    dados_propriedade: Optional[str] = None
    resultado_predicao: Optional[str] = None
    confianca_modelo: Optional[float] = None
    explicabilidade: Optional[str] = None
    data_calculo: str
    tempo_processamento_ms: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ApoliceCoberturasInfo(BaseModel):
    """Informações das coberturas de uma apólice"""
    nr_apolice: str
    segurado: str
    coberturas: List[CoberturaRiscoInfo]
    total_coberturas: int
    score_risco_medio: float
    nivel_risco_geral: str


class CoberturaResponse(BaseModel):
    """Resposta para consulta de cobertura individual"""
    success: bool
    data: Optional[CoberturaInfo] = None
    error: Optional[str] = None
    message: str


class CoberturasListResponse(BaseModel):
    """Resposta para listagem de coberturas"""
    success: bool
    data: List[CoberturaInfo]
    total: int
    message: str


class CoberturaRiscoResponse(BaseModel):
    """Resposta para dados de risco de cobertura"""
    success: bool
    data: Optional[CoberturaRiscoInfo] = None
    error: Optional[str] = None
    message: str


class ApoliceCoberturasResponse(BaseModel):
    """Resposta para coberturas de uma apólice"""
    success: bool
    data: Optional[ApoliceCoberturasInfo] = None
    error: Optional[str] = None
    message: str


class CoberturaRiscoListResponse(BaseModel):
    """Resposta para listagem de coberturas com dados de risco"""
    success: bool
    data: List[CoberturaRiscoInfo]
    total: int
    page: int
    per_page: int
    message: str


class CoberturaRankingResponse(BaseModel):
    """Resposta para ranking de coberturas por risco"""
    success: bool
    data: List[CoberturaRiscoInfo]
    total_ranked: int
    order: str
    message: str