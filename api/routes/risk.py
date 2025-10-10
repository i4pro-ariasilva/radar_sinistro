"""
Rotas para cálculo de risco
"""

from fastapi import APIRouter, HTTPException
from typing import List
import time

from api.models.requests import PolicyRequest, BatchPolicyRequest
from api.models.responses import PolicyRiskResponse, BatchRiskResponse, RiskResult
from api.services.risk_service import RiskService

router = APIRouter(prefix="/risk", tags=["Risk Calculation"])


@router.post("/calculate", response_model=PolicyRiskResponse)
async def calculate_risk(policy: PolicyRequest):
    """
    Calcula o risco de sinistro para uma apólice individual
    
    - **numero_apolice**: Número único da apólice
    - **segurado**: Nome completo do segurado
    - **cep**: CEP com 8 dígitos
    - **valor_segurado**: Valor segurado em reais
    - **tipo_residencia**: Tipo de residência (Casa, Apartamento, etc.)
    - **data_inicio**: Data de início da apólice
    """
    try:
        # Converter para dict
        policy_dict = policy.model_dump()
        
        # Calcular risco
        risk_result = RiskService.calculate_single_risk(policy_dict)
        
        return PolicyRiskResponse(
            success=True,
            data=risk_result,
            message=f"Risco calculado com sucesso para apólice {policy.numero_apolice}"
        )
        
    except Exception as e:
        return PolicyRiskResponse(
            success=False,
            error=str(e),
            message="Erro no cálculo de risco"
        )


@router.post("/calculate-batch", response_model=BatchRiskResponse)
async def calculate_batch_risk(batch: BatchPolicyRequest):
    """
    Calcula o risco de sinistro para múltiplas apólices em lote
    
    - **policies**: Lista de apólices para calcular risco
    - Máximo de 100 apólices por requisição
    """
    start_time = time.time()
    
    try:
        # Converter políticas para dict
        policies_dict = [policy.model_dump() for policy in batch.policies]
        
        # Calcular riscos em lote
        results = RiskService.calculate_batch_risks(policies_dict)
        
        # Contar sucessos e falhas
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        processing_time = time.time() - start_time
        
        return BatchRiskResponse(
            total_processed=len(results),
            successful=successful,
            failed=failed,
            results=results,
            processing_time=round(processing_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-and-save", response_model=PolicyRiskResponse)
async def calculate_and_save_risk(policy: PolicyRequest):
    """
    Calcula o risco e salva a apólice no banco de dados
    
    Similar ao endpoint /calculate, mas também persiste os dados
    """
    try:
        # Converter para dict
        policy_dict = policy.model_dump()
        
        # Calcular risco
        risk_result = RiskService.calculate_single_risk(policy_dict)
        
        # Preparar dados para salvar
        risk_dict = {
            'score_risco': risk_result.score_risco,
            'nivel_risco': risk_result.nivel_risco,
            'probabilidade': risk_result.probabilidade,
            'fatores_principais': risk_result.fatores_principais
        }
        
        # Salvar no banco
        policy_id = RiskService.save_policy_with_risk(policy_dict, risk_dict)
        
        return PolicyRiskResponse(
            success=True,
            data=risk_result,
            message=f"Risco calculado e apólice salva com ID {policy_id}"
        )
        
    except Exception as e:
        return PolicyRiskResponse(
            success=False,
            error=str(e),
            message="Erro no cálculo ou salvamento"
        )