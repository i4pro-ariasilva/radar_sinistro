"""
Serviço para gerenciamento de coberturas
"""

import sys
import os
import sqlite3
import pandas as pd
from typing import List, Optional, Dict, Any
import json

# Adicionar path do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from api.models.responses import (
    CoberturaInfo, CoberturaRiscoInfo, ApoliceCoberturasInfo
)


class CoverageService:
    """Serviço para consultas de coberturas"""
    
    DB_PATH = 'database/radar_sinistro.db'
    
    @staticmethod
    def get_all_coverages() -> List[CoberturaInfo]:
        """Lista todas as coberturas disponíveis"""
        try:
            conn = sqlite3.connect(CoverageService.DB_PATH)
            
            query = """
            SELECT cd_cobertura, cd_produto, nm_cobertura, dv_basica, created_at
            FROM coberturas
            ORDER BY cd_produto, cd_cobertura
            """
            
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            return [
                CoberturaInfo(
                    cd_cobertura=row[0],
                    cd_produto=row[1],
                    nm_cobertura=row[2],
                    dv_basica=bool(row[3]),
                    created_at=row[4]
                )
                for row in rows
            ]
            
        except Exception as e:
            print(f"Erro ao buscar coberturas: {e}")
            return []
    
    @staticmethod
    def get_coverage_by_id(cd_cobertura: int, cd_produto: int) -> Optional[CoberturaInfo]:
        """Busca cobertura por código"""
        try:
            conn = sqlite3.connect(CoverageService.DB_PATH)
            
            query = """
            SELECT cd_cobertura, cd_produto, nm_cobertura, dv_basica, created_at
            FROM coberturas
            WHERE cd_cobertura = ? AND cd_produto = ?
            """
            
            cursor = conn.cursor()
            cursor.execute(query, (cd_cobertura, cd_produto))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return CoberturaInfo(
                    cd_cobertura=row[0],
                    cd_produto=row[1],
                    nm_cobertura=row[2],
                    dv_basica=bool(row[3]),
                    created_at=row[4]
                )
            return None
            
        except Exception as e:
            print(f"Erro ao buscar cobertura: {e}")
            return None
    
    @staticmethod
    def get_coverage_risks_paginated(
        skip: int = 0, 
        limit: int = 100, 
        filters: Dict[str, Any] = None
    ) -> List[CoberturaRiscoInfo]:
        """Lista coberturas com dados de risco com paginação"""
        try:
            conn = sqlite3.connect(CoverageService.DB_PATH)
            
            # Query base
            query = """
            SELECT 
                cr.id, cr.nr_apolice, cr.cd_cobertura, cr.cd_produto,
                c.nm_cobertura, c.dv_basica,
                cr.score_risco, cr.nivel_risco, cr.probabilidade,
                cr.modelo_usado, cr.versao_modelo, cr.fatores_risco,
                cr.dados_climaticos, cr.dados_propriedade, cr.resultado_predicao,
                cr.confianca_modelo, cr.explicabilidade, cr.data_calculo,
                cr.tempo_processamento_ms, cr.created_at, cr.updated_at
            FROM cobertura_risco cr
            JOIN coberturas c ON cr.cd_cobertura = c.cd_cobertura 
                              AND cr.cd_produto = c.cd_produto
            """
            
            where_conditions = []
            params = []
            
            if filters:
                if 'nivel_risco' in filters:
                    where_conditions.append("cr.nivel_risco = ?")
                    params.append(filters['nivel_risco'])
                
                if 'cd_produto' in filters:
                    where_conditions.append("cr.cd_produto = ?")
                    params.append(filters['cd_produto'])
                
                if 'nr_apolice' in filters:
                    where_conditions.append("cr.nr_apolice LIKE ?")
                    params.append(f"%{filters['nr_apolice']}%")
                
                if 'score_min' in filters:
                    where_conditions.append("cr.score_risco >= ?")
                    params.append(filters['score_min'])
                
                if 'score_max' in filters:
                    where_conditions.append("cr.score_risco <= ?")
                    params.append(filters['score_max'])
            
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            query += " ORDER BY cr.score_risco DESC, cr.data_calculo DESC"
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, skip])
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            return [
                CoberturaRiscoInfo(
                    id=row[0],
                    nr_apolice=row[1],
                    cd_cobertura=row[2],
                    cd_produto=row[3],
                    nm_cobertura=row[4],
                    dv_basica=bool(row[5]),
                    score_risco=float(row[6]),
                    nivel_risco=row[7],
                    probabilidade=float(row[8]),
                    modelo_usado=row[9],
                    versao_modelo=row[10],
                    fatores_risco=row[11],
                    dados_climaticos=row[12],
                    dados_propriedade=row[13],
                    resultado_predicao=row[14],
                    confianca_modelo=float(row[15]) if row[15] else None,
                    explicabilidade=row[16],
                    data_calculo=row[17],
                    tempo_processamento_ms=row[18],
                    created_at=row[19],
                    updated_at=row[20]
                )
                for row in rows
            ]
            
        except Exception as e:
            print(f"Erro ao buscar coberturas com risco: {e}")
            return []
    
    @staticmethod
    def count_coverage_risks(filters: Dict[str, Any] = None) -> int:
        """Conta total de coberturas com dados de risco"""
        try:
            conn = sqlite3.connect(CoverageService.DB_PATH)
            
            query = "SELECT COUNT(*) FROM cobertura_risco cr"
            where_conditions = []
            params = []
            
            if filters:
                if 'nivel_risco' in filters:
                    where_conditions.append("cr.nivel_risco = ?")
                    params.append(filters['nivel_risco'])
                
                if 'cd_produto' in filters:
                    where_conditions.append("cr.cd_produto = ?")
                    params.append(filters['cd_produto'])
                
                if 'nr_apolice' in filters:
                    where_conditions.append("cr.nr_apolice LIKE ?")
                    params.append(f"%{filters['nr_apolice']}%")
                
                if 'score_min' in filters:
                    where_conditions.append("cr.score_risco >= ?")
                    params.append(filters['score_min'])
                
                if 'score_max' in filters:
                    where_conditions.append("cr.score_risco <= ?")
                    params.append(filters['score_max'])
            
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            print(f"Erro ao contar coberturas: {e}")
            return 0
    
    @staticmethod
    def get_policy_coverages(nr_apolice: str) -> Optional[ApoliceCoberturasInfo]:
        """Busca todas as coberturas de uma apólice com dados de risco"""
        try:
            conn = sqlite3.connect(CoverageService.DB_PATH)
            
            # Buscar dados da apólice
            policy_query = """
            SELECT segurado FROM apolices WHERE numero_apolice = ?
            """
            cursor = conn.cursor()
            cursor.execute(policy_query, (nr_apolice,))
            policy_row = cursor.fetchone()
            
            if not policy_row:
                conn.close()
                return None
            
            segurado = policy_row[0]
            
            # Buscar coberturas com dados de risco
            coverages_query = """
            SELECT 
                cr.id, cr.nr_apolice, cr.cd_cobertura, cr.cd_produto,
                c.nm_cobertura, c.dv_basica,
                cr.score_risco, cr.nivel_risco, cr.probabilidade,
                cr.modelo_usado, cr.versao_modelo, cr.fatores_risco,
                cr.dados_climaticos, cr.dados_propriedade, cr.resultado_predicao,
                cr.confianca_modelo, cr.explicabilidade, cr.data_calculo,
                cr.tempo_processamento_ms, cr.created_at, cr.updated_at
            FROM cobertura_risco cr
            JOIN coberturas c ON cr.cd_cobertura = c.cd_cobertura 
                              AND cr.cd_produto = c.cd_produto
            WHERE cr.nr_apolice = ?
            ORDER BY cr.score_risco DESC
            """
            
            cursor.execute(coverages_query, (nr_apolice,))
            coverage_rows = cursor.fetchall()
            conn.close()
            
            # Processar coberturas
            coberturas = [
                CoberturaRiscoInfo(
                    id=row[0],
                    nr_apolice=row[1],
                    cd_cobertura=row[2],
                    cd_produto=row[3],
                    nm_cobertura=row[4],
                    dv_basica=bool(row[5]),
                    score_risco=float(row[6]),
                    nivel_risco=row[7],
                    probabilidade=float(row[8]),
                    modelo_usado=row[9],
                    versao_modelo=row[10],
                    fatores_risco=row[11],
                    dados_climaticos=row[12],
                    dados_propriedade=row[13],
                    resultado_predicao=row[14],
                    confianca_modelo=float(row[15]) if row[15] else None,
                    explicabilidade=row[16],
                    data_calculo=row[17],
                    tempo_processamento_ms=row[18],
                    created_at=row[19],
                    updated_at=row[20]
                )
                for row in coverage_rows
            ]
            
            # Calcular métricas
            if coberturas:
                score_medio = sum(c.score_risco for c in coberturas) / len(coberturas)
                
                # Determinar nível de risco geral
                scores_altos = sum(1 for c in coberturas if c.score_risco >= 75)
                if scores_altos > len(coberturas) / 2:
                    nivel_geral = "ALTO"
                elif any(c.score_risco >= 60 for c in coberturas):
                    nivel_geral = "MÉDIO"
                else:
                    nivel_geral = "BAIXO"
            else:
                score_medio = 0.0
                nivel_geral = "SEM_DADOS"
            
            return ApoliceCoberturasInfo(
                nr_apolice=nr_apolice,
                segurado=segurado,
                coberturas=coberturas,
                total_coberturas=len(coberturas),
                score_risco_medio=score_medio,
                nivel_risco_geral=nivel_geral
            )
            
        except Exception as e:
            print(f"Erro ao buscar coberturas da apólice: {e}")
            return None
    
    @staticmethod
    def get_coverage_risk_rankings(
        order: str = "desc", 
        limit: int = 50
    ) -> List[CoberturaRiscoInfo]:
        """Retorna ranking de coberturas por score de risco"""
        try:
            conn = sqlite3.connect(CoverageService.DB_PATH)
            
            order_clause = "DESC" if order.lower() == "desc" else "ASC"
            
            query = f"""
            SELECT 
                cr.id, cr.nr_apolice, cr.cd_cobertura, cr.cd_produto,
                c.nm_cobertura, c.dv_basica,
                cr.score_risco, cr.nivel_risco, cr.probabilidade,
                cr.modelo_usado, cr.versao_modelo, cr.fatores_risco,
                cr.dados_climaticos, cr.dados_propriedade, cr.resultado_predicao,
                cr.confianca_modelo, cr.explicabilidade, cr.data_calculo,
                cr.tempo_processamento_ms, cr.created_at, cr.updated_at
            FROM cobertura_risco cr
            JOIN coberturas c ON cr.cd_cobertura = c.cd_cobertura 
                              AND cr.cd_produto = c.cd_produto
            ORDER BY cr.score_risco {order_clause}
            LIMIT ?
            """
            
            cursor = conn.cursor()
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            conn.close()
            
            return [
                CoberturaRiscoInfo(
                    id=row[0],
                    nr_apolice=row[1],
                    cd_cobertura=row[2],
                    cd_produto=row[3],
                    nm_cobertura=row[4],
                    dv_basica=bool(row[5]),
                    score_risco=float(row[6]),
                    nivel_risco=row[7],
                    probabilidade=float(row[8]),
                    modelo_usado=row[9],
                    versao_modelo=row[10],
                    fatores_risco=row[11],
                    dados_climaticos=row[12],
                    dados_propriedade=row[13],
                    resultado_predicao=row[14],
                    confianca_modelo=float(row[15]) if row[15] else None,
                    explicabilidade=row[16],
                    data_calculo=row[17],
                    tempo_processamento_ms=row[18],
                    created_at=row[19],
                    updated_at=row[20]
                )
                for row in rows
            ]
            
        except Exception as e:
            print(f"Erro ao buscar ranking de coberturas: {e}")
            return []
    
    @staticmethod
    def get_coverage_statistics() -> Dict[str, Any]:
        """Retorna estatísticas das coberturas"""
        try:
            conn = sqlite3.connect(CoverageService.DB_PATH)
            cursor = conn.cursor()
            
            # Estatísticas básicas
            cursor.execute("SELECT COUNT(*) FROM coberturas")
            total_coberturas = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cobertura_risco")
            total_com_risco = cursor.fetchone()[0]
            
            # Distribuição por nível de risco
            cursor.execute("""
                SELECT nivel_risco, COUNT(*) 
                FROM cobertura_risco 
                GROUP BY nivel_risco
            """)
            distribuicao_risco = dict(cursor.fetchall())
            
            # Estatísticas de score
            cursor.execute("""
                SELECT 
                    AVG(score_risco) as media,
                    MIN(score_risco) as minimo,
                    MAX(score_risco) as maximo,
                    COUNT(CASE WHEN score_risco >= 75 THEN 1 END) as alto_risco
                FROM cobertura_risco
            """)
            stats_score = cursor.fetchone()
            
            # Top coberturas com maior risco
            cursor.execute("""
                SELECT c.nm_cobertura, AVG(cr.score_risco) as media_risco
                FROM cobertura_risco cr
                JOIN coberturas c ON cr.cd_cobertura = c.cd_cobertura 
                                  AND cr.cd_produto = c.cd_produto
                GROUP BY c.nm_cobertura
                ORDER BY media_risco DESC
                LIMIT 5
            """)
            top_risco = cursor.fetchall()
            
            conn.close()
            
            return {
                "resumo": {
                    "total_coberturas": total_coberturas,
                    "coberturas_com_analise_risco": total_com_risco,
                    "cobertura_analise_pct": round((total_com_risco / total_coberturas * 100) if total_coberturas > 0 else 0, 2)
                },
                "distribuicao_risco": distribuicao_risco,
                "estatisticas_score": {
                    "media": round(stats_score[0], 2) if stats_score[0] else 0,
                    "minimo": round(stats_score[1], 2) if stats_score[1] else 0,
                    "maximo": round(stats_score[2], 2) if stats_score[2] else 0,
                    "alto_risco_count": stats_score[3] or 0
                },
                "top_coberturas_risco": [
                    {"nome": nome, "score_medio": round(score, 2)}
                    for nome, score in top_risco
                ]
            }
            
        except Exception as e:
            print(f"Erro ao calcular estatísticas: {e}")
            return {}