"""
Rotas para gestão de coberturas e análise de risco por cobertura
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from api.models.responses import (
    CoberturaResponse, CoberturasListResponse, CoberturaRiscoResponse,
    ApoliceCoberturasResponse, CoberturaRiscoListResponse, 
    CoberturaRankingResponse, BaseResponse
)
from api.services.coverage_service import CoverageService

router = APIRouter(prefix="/coverages", tags=["Coverage Management"])


@router.get("/", response_model=CoberturasListResponse)
async def list_all_coverages():
    """
    Lista todas as coberturas disponíveis no sistema
    
    Retorna todas as coberturas cadastradas com suas informações básicas:
    - Código da cobertura e produto
    - Nome da cobertura
    - Se é cobertura básica ou adicional
    """
    try:
        coverages = CoverageService.get_all_coverages()
        
        return CoberturasListResponse(
            success=True,
            data=coverages,
            total=len(coverages),
            message=f"Encontradas {len(coverages)} coberturas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cd_cobertura}/{cd_produto}", response_model=CoberturaResponse)
async def get_coverage_by_id(cd_cobertura: int, cd_produto: int):
    """
    Busca uma cobertura específica pelos códigos
    
    - **cd_cobertura**: Código único da cobertura
    - **cd_produto**: Código do produto ao qual a cobertura pertence
    """
    try:
        coverage = CoverageService.get_coverage_by_id(cd_cobertura, cd_produto)
        
        if not coverage:
            return CoberturaResponse(
                success=False,
                error="Cobertura não encontrada",
                message=f"Cobertura {cd_cobertura}/{cd_produto} não encontrada"
            )
            
        return CoberturaResponse(
            success=True,
            data=coverage,
            message=f"Cobertura {cd_cobertura}/{cd_produto} encontrada"
        )
        
    except Exception as e:
        return CoberturaResponse(
            success=False,
            error=str(e),
            message="Erro na busca da cobertura"
        )


@router.get("/risks/list", response_model=CoberturaRiscoListResponse)
async def list_coverage_risks(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    nivel_risco: Optional[str] = Query(None, description="Filtrar por nível de risco"),
    cd_produto: Optional[int] = Query(None, description="Filtrar por código do produto"),
    nr_apolice: Optional[str] = Query(None, description="Filtrar por número da apólice"),
    score_min: Optional[float] = Query(None, ge=0, le=100, description="Score mínimo de risco"),
    score_max: Optional[float] = Query(None, ge=0, le=100, description="Score máximo de risco")
):
    """
    Lista coberturas com dados de análise de risco com paginação e filtros
    
    - **skip**: Número de registros para pular (para paginação)
    - **limit**: Número máximo de registros a retornar
    - **nivel_risco**: Filtrar por nível de risco (BAIXO, MÉDIO, ALTO, CRÍTICO)
    - **cd_produto**: Filtrar por código do produto
    - **nr_apolice**: Filtrar por número da apólice (busca parcial)
    - **score_min**: Score mínimo de risco (0-100)
    - **score_max**: Score máximo de risco (0-100)
    """
    try:
        filters = {}
        if nivel_risco:
            filters['nivel_risco'] = nivel_risco
        if cd_produto:
            filters['cd_produto'] = cd_produto
        if nr_apolice:
            filters['nr_apolice'] = nr_apolice
        if score_min is not None:
            filters['score_min'] = score_min
        if score_max is not None:
            filters['score_max'] = score_max
            
        coverage_risks = CoverageService.get_coverage_risks_paginated(
            skip=skip, 
            limit=limit, 
            filters=filters
        )
        
        # Contar total
        total = CoverageService.count_coverage_risks(filters)
        
        return CoberturaRiscoListResponse(
            success=True,
            data=coverage_risks,
            total=total,
            page=skip // limit + 1,
            per_page=limit,
            message=f"Encontradas {len(coverage_risks)} análises de risco de coberturas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policy/{nr_apolice}", response_model=ApoliceCoberturasResponse)
async def get_policy_coverages(nr_apolice: str):
    """
    Busca todas as coberturas de uma apólice específica com dados de risco
    
    - **nr_apolice**: Número único da apólice
    
    Retorna informações completas das coberturas da apólice incluindo:
    - Dados de risco de cada cobertura
    - Score médio de risco da apólice
    - Nível de risco geral
    - Estatísticas agregadas
    """
    try:
        policy_coverages = CoverageService.get_policy_coverages(nr_apolice)
        
        if not policy_coverages:
            return ApoliceCoberturasResponse(
                success=False,
                error="Apólice não encontrada ou sem coberturas",
                message=f"Apólice {nr_apolice} não encontrada ou não possui coberturas analisadas"
            )
            
        return ApoliceCoberturasResponse(
            success=True,
            data=policy_coverages,
            message=f"Encontradas {policy_coverages.total_coberturas} coberturas para a apólice {nr_apolice}"
        )
        
    except Exception as e:
        return ApoliceCoberturasResponse(
            success=False,
            error=str(e),
            message="Erro na busca das coberturas da apólice"
        )


@router.get("/rankings/risk", response_model=CoberturaRankingResponse)
async def get_coverage_risk_rankings(
    order: str = Query("desc", regex="^(asc|desc)$", description="Ordem: asc ou desc"),
    limit: int = Query(50, ge=1, le=500, description="Número de resultados")
):
    """
    Retorna ranking de coberturas por score de risco
    
    - **order**: Ordem do ranking (asc = menor risco primeiro, desc = maior risco primeiro)
    - **limit**: Número de coberturas no ranking (máximo 500)
    
    Útil para identificar:
    - Coberturas com maior risco no portfólio
    - Padrões de risco por tipo de cobertura
    - Coberturas que precisam de atenção especial
    """
    try:
        rankings = CoverageService.get_coverage_risk_rankings(order=order, limit=limit)
        
        return CoberturaRankingResponse(
            success=True,
            data=rankings,
            total_ranked=len(rankings),
            order=order,
            message=f"Ranking com {len(rankings)} coberturas"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_coverage_statistics():
    """
    Retorna estatísticas resumidas das coberturas e análises de risco
    
    Inclui:
    - Total de coberturas cadastradas
    - Coberturas com análise de risco
    - Distribuição por nível de risco
    - Estatísticas de score (média, mín, máx)
    - Top coberturas com maior risco médio
    """
    try:
        stats = CoverageService.get_coverage_statistics()
        
        return {
            "success": True,
            "data": stats,
            "message": "Estatísticas de coberturas calculadas com sucesso"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risks/high-risk")
async def get_high_risk_coverages(
    threshold: float = Query(75.0, ge=50, le=100, description="Threshold de score para alto risco"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de resultados")
):
    """
    Lista coberturas com alto risco (score acima do threshold)
    
    - **threshold**: Score mínimo para considerar alto risco (padrão: 75)
    - **limit**: Número máximo de resultados
    
    Endpoint especializado para identificar coberturas que precisam de atenção imediata
    """
    try:
        filters = {'score_min': threshold}
        
        high_risk_coverages = CoverageService.get_coverage_risks_paginated(
            skip=0,
            limit=limit,
            filters=filters
        )
        
        total_high_risk = CoverageService.count_coverage_risks(filters)
        
        return {
            "success": True,
            "data": high_risk_coverages,
            "total_high_risk": total_high_risk,
            "threshold_used": threshold,
            "message": f"Encontradas {len(high_risk_coverages)} coberturas com alto risco (>= {threshold})"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risks/by-product/{cd_produto}")
async def get_coverage_risks_by_product(
    cd_produto: int,
    limit: int = Query(100, ge=1, le=1000, description="Máximo de resultados")
):
    """
    Lista coberturas com análise de risco para um produto específico
    
    - **cd_produto**: Código do produto
    - **limit**: Número máximo de resultados
    
    Útil para análise de risco por linha de produto
    """
    try:
        filters = {'cd_produto': cd_produto}
        
        product_coverages = CoverageService.get_coverage_risks_paginated(
            skip=0,
            limit=limit,
            filters=filters
        )
        
        total_product = CoverageService.count_coverage_risks(filters)
        
        return {
            "success": True,
            "data": product_coverages,
            "total_for_product": total_product,
            "cd_produto": cd_produto,
            "message": f"Encontradas {len(product_coverages)} coberturas para o produto {cd_produto}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))