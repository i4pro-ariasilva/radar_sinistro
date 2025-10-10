"""
Rotas para gestão de apólices
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from api.models.responses import (
    PolicyResponse, PoliciesListResponse, PolicyRankingResponse,
    BaseResponse
)
from api.services.policy_service import PolicyService

router = APIRouter(prefix="/policies", tags=["Policies Management"])


@router.get("/", response_model=PoliciesListResponse)
async def list_policies(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    nivel_risco: Optional[str] = Query(None, description="Filtrar por nível de risco"),
    segurado: Optional[str] = Query(None, description="Filtrar por nome do segurado")
):
    """
    Lista todas as apólices com paginação e filtros opcionais
    
    - **skip**: Número de registros para pular (para paginação)
    - **limit**: Número máximo de registros a retornar
    - **nivel_risco**: Filtrar por nível de risco (BAIXO, MÉDIO, ALTO, CRÍTICO)
    - **segurado**: Filtrar por nome do segurado (busca parcial)
    """
    try:
        filters = {}
        if nivel_risco:
            filters['nivel_risco'] = nivel_risco
        if segurado:
            filters['segurado'] = segurado
            
        policies = PolicyService.get_policies_paginated(
            skip=skip, 
            limit=limit, 
            filters=filters
        )
        
        # Contar total
        total = PolicyService.count_policies(filters)
        
        return PoliciesListResponse(
            success=True,
            data=policies,
            total=total,
            page=skip // limit + 1,
            per_page=limit,
            message=f"Encontradas {len(policies)} apólices"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{numero_apolice}", response_model=PolicyResponse)
async def get_policy_by_number(numero_apolice: str):
    """
    Busca uma apólice específica pelo número
    
    - **numero_apolice**: Número único da apólice
    """
    try:
        policy = PolicyService.get_policy_by_number(numero_apolice)
        
        if not policy:
            return PolicyResponse(
                success=False,
                error="Apólice não encontrada",
                message=f"Apólice {numero_apolice} não encontrada"
            )
            
        return PolicyResponse(
            success=True,
            data=policy,
            message=f"Apólice {numero_apolice} encontrada"
        )
        
    except Exception as e:
        return PolicyResponse(
            success=False,
            error=str(e),
            message="Erro na busca da apólice"
        )


@router.get("/rankings/risk", response_model=PolicyRankingResponse)
async def get_risk_rankings(
    order: str = Query("desc", regex="^(asc|desc)$", description="Ordem: asc ou desc"),
    limit: int = Query(50, ge=1, le=500, description="Número de resultados")
):
    """
    Retorna ranking de apólices por score de risco
    
    - **order**: Ordem do ranking (asc = menor risco primeiro, desc = maior risco primeiro)
    - **limit**: Número de apólices no ranking (máximo 500)
    """
    try:
        rankings = PolicyService.get_risk_rankings(order=order, limit=limit)
        
        return PolicyRankingResponse(
            success=True,
            data=rankings,
            total_ranked=len(rankings),
            order=order,
            message=f"Ranking com {len(rankings)} apólices"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings/value", response_model=PolicyRankingResponse)
async def get_value_rankings(
    order: str = Query("desc", regex="^(asc|desc)$", description="Ordem: asc ou desc"),
    limit: int = Query(50, ge=1, le=500, description="Número de resultados")
):
    """
    Retorna ranking de apólices por valor segurado
    
    - **order**: Ordem do ranking (asc = menor valor primeiro, desc = maior valor primeiro)
    - **limit**: Número de apólices no ranking (máximo 500)
    """
    try:
        rankings = PolicyService.get_value_rankings(order=order, limit=limit)
        
        return PolicyRankingResponse(
            success=True,
            data=rankings,
            total_ranked=len(rankings),
            order=order,
            message=f"Ranking por valor com {len(rankings)} apólices"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_policies_summary():
    """
    Retorna estatísticas resumidas das apólices
    """
    try:
        stats = PolicyService.get_policies_statistics()
        
        return {
            "success": True,
            "data": stats,
            "message": "Estatísticas calculadas com sucesso"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{numero_apolice}", response_model=BaseResponse)
async def delete_policy(numero_apolice: str):
    """
    Remove uma apólice do sistema
    
    - **numero_apolice**: Número único da apólice a ser removida
    """
    try:
        success = PolicyService.delete_policy(numero_apolice)
        
        if success:
            return BaseResponse(
                success=True,
                message=f"Apólice {numero_apolice} removida com sucesso"
            )
        else:
            return BaseResponse(
                success=False,
                error="Apólice não encontrada",
                message=f"Apólice {numero_apolice} não encontrada para remoção"
            )
            
    except Exception as e:
        return BaseResponse(
            success=False,
            error=str(e),
            message="Erro na remoção da apólice"
        )