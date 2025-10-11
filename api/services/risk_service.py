"""
Serviço de cálculo de risco - reutiliza funções existentes
"""

import sys
import os
from typing import Dict, List, Any
from datetime import datetime

# Adicionar path do projeto para reutilizar código existente
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from policy_management import calculate_policy_risk, save_policy_to_database
from api.models.responses import RiskResult, BatchRiskResult


class RiskService:
    """Serviço para cálculo de risco - wrapper das funções existentes"""
    
    @staticmethod
    def calculate_single_risk(policy_data: Dict[str, Any]) -> RiskResult:
        """
        Calcula risco para uma apólice individual
        Reutiliza a função calculate_policy_risk existente
        """
        try:
            # Usar função existente
            risk_data = calculate_policy_risk(policy_data)
            
            # Converter tipos numpy para tipos Python nativos
            score_risco = float(risk_data['score_risco'])
            probabilidade = float(risk_data['probabilidade'])
            
            # Converter fatores principais se existirem
            fatores_principais = []
            if 'fatores_principais' in risk_data:
                fatores_principais = [
                    float(item) if hasattr(item, 'item') else item 
                    for item in risk_data['fatores_principais']
                ]
            
            return RiskResult(
                numero_apolice=policy_data['numero_apolice'],
                score_risco=score_risco,
                nivel_risco=str(risk_data['nivel_risco']),
                probabilidade=probabilidade,
                fatores_principais=fatores_principais,
                calculation_date=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Erro no cálculo de risco: {str(e)}")
    
    @staticmethod
    def calculate_batch_risks(policies_data: List[Dict[str, Any]]) -> List[BatchRiskResult]:
        """
        Calcula risco para múltiplas apólices
        """
        results = []
        
        for policy_data in policies_data:
            try:
                risk_result = RiskService.calculate_single_risk(policy_data)
                
                results.append(BatchRiskResult(
                    numero_apolice=policy_data['numero_apolice'],
                    success=True,
                    risk_data=risk_result,
                    error=None
                ))
                
            except Exception as e:
                results.append(BatchRiskResult(
                    numero_apolice=policy_data.get('numero_apolice', 'UNKNOWN'),
                    success=False,
                    risk_data=None,
                    error=str(e)
                ))
        
        return results
    
    @staticmethod
    def save_policy_with_risk(policy_data: Dict[str, Any], risk_data: Dict[str, Any]) -> int:
        """
        Salva apólice com dados de risco
        Reutiliza a função save_policy_to_database existente
        """
        try:
            return save_policy_to_database(policy_data, risk_data)
        except Exception as e:
            raise Exception(f"Erro ao salvar apólice: {str(e)}")
