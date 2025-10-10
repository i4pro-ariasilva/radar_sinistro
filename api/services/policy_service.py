"""
Serviço para gerenciamento de apólices - reutiliza banco existente
"""

import sys
import os
import sqlite3
import pandas as pd
from typing import List, Optional, Dict, Any

# Adicionar path do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from api.models.responses import PolicyInfo


class PolicyService:
    """Serviço para consultas de apólices"""
    
    DB_PATH = 'database/radar_sinistro.db'
    
    @staticmethod
    def get_policy_by_number(numero_apolice: str) -> Optional[PolicyInfo]:
        """Busca apólice por número"""
        try:
            conn = sqlite3.connect(PolicyService.DB_PATH)
            
            query = """
            SELECT numero_apolice, segurado, cep, valor_segurado, 
                   tipo_residencia, score_risco, nivel_risco, 
                   probabilidade_sinistro, created_at
            FROM apolices 
            WHERE numero_apolice = ?
            """
            
            cursor = conn.cursor()
            cursor.execute(query, (numero_apolice,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return PolicyInfo(
                    numero_apolice=row[0],
                    segurado=row[1],
                    cep=row[2],
                    valor_segurado=row[3],
                    tipo_residencia=row[4],
                    score_risco=row[5] or 0.0,
                    nivel_risco=row[6] or 'baixo',
                    probabilidade_sinistro=row[7] or 0.0,
                    created_at=row[8] or ''
                )
            
            return None
            
        except Exception as e:
            raise Exception(f"Erro ao buscar apólice: {str(e)}")
    
    @staticmethod
    def get_policies_ranking(
        limit: int = 50,
        risk_level: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        search: Optional[str] = None
    ) -> List[PolicyInfo]:
        """
        Busca ranking de apólices com filtros
        """
        try:
            conn = sqlite3.connect(PolicyService.DB_PATH)
            
            # Query base
            query = """
            SELECT numero_apolice, segurado, cep, valor_segurado, 
                   tipo_residencia, score_risco, nivel_risco, 
                   probabilidade_sinistro, created_at
            FROM apolices 
            WHERE 1=1
            """
            
            params = []
            
            # Aplicar filtros
            if risk_level:
                query += " AND nivel_risco = ?"
                params.append(risk_level)
            
            if min_value is not None:
                query += " AND valor_segurado >= ?"
                params.append(min_value)
            
            if max_value is not None:
                query += " AND valor_segurado <= ?"
                params.append(max_value)
            
            if search:
                query += " AND numero_apolice LIKE ?"
                params.append(f"%{search}%")
            
            # Ordenar por risco e limitar
            query += " ORDER BY score_risco DESC, created_at DESC LIMIT ?"
            params.append(limit)
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            # Converter para lista de PolicyInfo
            policies = []
            for _, row in df.iterrows():
                policies.append(PolicyInfo(
                    numero_apolice=row['numero_apolice'],
                    segurado=row['segurado'],
                    cep=row['cep'],
                    valor_segurado=row['valor_segurado'],
                    tipo_residencia=row['tipo_residencia'],
                    score_risco=row['score_risco'] or 0.0,
                    nivel_risco=row['nivel_risco'] or 'baixo',
                    probabilidade_sinistro=row['probabilidade_sinistro'] or 0.0,
                    created_at=row['created_at'] or ''
                ))
            
            return policies
            
        except Exception as e:
            raise Exception(f"Erro ao buscar ranking: {str(e)}")
    
    @staticmethod
    def get_total_count(filters: Dict[str, Any] = None) -> int:
        """Conta total de apólices com filtros aplicados"""
        try:
            conn = sqlite3.connect(PolicyService.DB_PATH)
            
            query = "SELECT COUNT(*) FROM apolices WHERE 1=1"
            params = []
            
            if filters:
                if filters.get('risk_level'):
                    query += " AND nivel_risco = ?"
                    params.append(filters['risk_level'])
                
                if filters.get('min_value') is not None:
                    query += " AND valor_segurado >= ?"
                    params.append(filters['min_value'])
                
                if filters.get('max_value') is not None:
                    query += " AND valor_segurado <= ?"
                    params.append(filters['max_value'])
                
                if filters.get('search'):
                    query += " AND numero_apolice LIKE ?"
                    params.append(f"%{filters['search']}%")
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            raise Exception(f"Erro ao contar apólices: {str(e)}")
    
    @staticmethod
    def get_policies_paginated(skip: int = 0, limit: int = 100, filters: Optional[Dict] = None) -> List[PolicyInfo]:
        """Busca apólices com paginação e filtros"""
        try:
            conn = sqlite3.connect(PolicyService.DB_PATH)
            
            query = """
            SELECT numero_apolice, segurado, cep, valor_segurado, 
                   tipo_residencia, score_risco, nivel_risco, 
                   probabilidade_sinistro, created_at
            FROM apolices 
            WHERE 1=1
            """
            params = []
            
            # Aplicar filtros
            if filters:
                if filters.get('nivel_risco'):
                    query += " AND nivel_risco = ?"
                    params.append(filters['nivel_risco'])
                
                if filters.get('segurado'):
                    query += " AND segurado LIKE ?"
                    params.append(f"%{filters['segurado']}%")
                
                if filters.get('min_value') is not None:
                    query += " AND valor_segurado >= ?"
                    params.append(filters['min_value'])
                
                if filters.get('max_value') is not None:
                    query += " AND valor_segurado <= ?"
                    params.append(filters['max_value'])
            
            # Adicionar paginação
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, skip])
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            # Converter para lista de PolicyInfo
            policies = []
            for _, row in df.iterrows():
                policy = PolicyInfo(
                    numero_apolice=row['numero_apolice'],
                    segurado=row['segurado'],
                    cep=row['cep'],
                    valor_segurado=float(row['valor_segurado']),
                    tipo_residencia=row['tipo_residencia'],
                    score_risco=float(row['score_risco']) if row['score_risco'] else 0.0,
                    nivel_risco=row['nivel_risco'] if row['nivel_risco'] else 'N/A',
                    probabilidade_sinistro=float(row['probabilidade_sinistro']) if row['probabilidade_sinistro'] else 0.0,
                    created_at=str(row['created_at'])
                )
                policies.append(policy)
            
            return policies
            
        except Exception as e:
            raise Exception(f"Erro ao buscar apólices paginadas: {str(e)}")
    
    @staticmethod
    def count_policies(filters: Optional[Dict] = None) -> int:
        """Conta total de apólices com filtros aplicados"""
        try:
            conn = sqlite3.connect(PolicyService.DB_PATH)
            
            query = "SELECT COUNT(*) FROM apolices WHERE 1=1"
            params = []
            
            if filters:
                if filters.get('nivel_risco'):
                    query += " AND nivel_risco = ?"
                    params.append(filters['nivel_risco'])
                
                if filters.get('segurado'):
                    query += " AND segurado LIKE ?"
                    params.append(f"%{filters['segurado']}%")
                
                if filters.get('min_value') is not None:
                    query += " AND valor_segurado >= ?"
                    params.append(filters['min_value'])
                
                if filters.get('max_value') is not None:
                    query += " AND valor_segurado <= ?"
                    params.append(filters['max_value'])
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            raise Exception(f"Erro ao contar apólices: {str(e)}")
    
    @staticmethod
    def get_risk_rankings(order: str = "desc", limit: int = 50) -> List[PolicyInfo]:
        """Retorna ranking de apólices por score de risco"""
        try:
            conn = sqlite3.connect(PolicyService.DB_PATH)
            
            order_clause = "DESC" if order.lower() == "desc" else "ASC"
            
            query = f"""
            SELECT numero_apolice, segurado, cep, valor_segurado, 
                   tipo_residencia, score_risco, nivel_risco, 
                   probabilidade_sinistro, created_at
            FROM apolices 
            WHERE score_risco IS NOT NULL
            ORDER BY score_risco {order_clause}
            LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=[limit])
            conn.close()
            
            # Converter para lista de PolicyInfo
            policies = []
            for _, row in df.iterrows():
                policy = PolicyInfo(
                    numero_apolice=row['numero_apolice'],
                    segurado=row['segurado'],
                    cep=row['cep'],
                    valor_segurado=float(row['valor_segurado']),
                    tipo_residencia=row['tipo_residencia'],
                    score_risco=float(row['score_risco']),
                    nivel_risco=row['nivel_risco'],
                    probabilidade_sinistro=float(row['probabilidade_sinistro']),
                    created_at=str(row['created_at'])
                )
                policies.append(policy)
            
            return policies
            
        except Exception as e:
            raise Exception(f"Erro ao buscar ranking de risco: {str(e)}")
    
    @staticmethod
    def get_value_rankings(order: str = "desc", limit: int = 50) -> List[PolicyInfo]:
        """Retorna ranking de apólices por valor segurado"""
        try:
            conn = sqlite3.connect(PolicyService.DB_PATH)
            
            order_clause = "DESC" if order.lower() == "desc" else "ASC"
            
            query = f"""
            SELECT numero_apolice, segurado, cep, valor_segurado, 
                   tipo_residencia, score_risco, nivel_risco, 
                   probabilidade_sinistro, created_at
            FROM apolices 
            ORDER BY valor_segurado {order_clause}
            LIMIT ?
            """
            
            df = pd.read_sql_query(query, conn, params=[limit])
            conn.close()
            
            # Converter para lista de PolicyInfo
            policies = []
            for _, row in df.iterrows():
                policy = PolicyInfo(
                    numero_apolice=row['numero_apolice'],
                    segurado=row['segurado'],
                    cep=row['cep'],
                    valor_segurado=float(row['valor_segurado']),
                    tipo_residencia=row['tipo_residencia'],
                    score_risco=float(row['score_risco']) if row['score_risco'] else 0.0,
                    nivel_risco=row['nivel_risco'] if row['nivel_risco'] else 'N/A',
                    probabilidade_sinistro=float(row['probabilidade_sinistro']) if row['probabilidade_sinistro'] else 0.0,
                    created_at=str(row['created_at'])
                )
                policies.append(policy)
            
            return policies
            
        except Exception as e:
            raise Exception(f"Erro ao buscar ranking de valor: {str(e)}")
    
    @staticmethod
    def get_policies_statistics() -> Dict[str, Any]:
        """Retorna estatísticas das apólices"""
        try:
            conn = sqlite3.connect(PolicyService.DB_PATH)
            
            # Estatísticas gerais
            general_stats = pd.read_sql_query("""
                SELECT 
                    COUNT(*) as total_policies,
                    AVG(valor_segurado) as avg_value,
                    MIN(valor_segurado) as min_value,
                    MAX(valor_segurado) as max_value,
                    AVG(score_risco) as avg_risk_score
                FROM apolices
            """, conn)
            
            # Distribuição por nível de risco
            risk_distribution = pd.read_sql_query("""
                SELECT nivel_risco, COUNT(*) as count
                FROM apolices
                WHERE nivel_risco IS NOT NULL
                GROUP BY nivel_risco
                ORDER BY count DESC
            """, conn)
            
            # Estatísticas por tipo de residência
            residence_stats = pd.read_sql_query("""
                SELECT tipo_residencia, COUNT(*) as count, AVG(valor_segurado) as avg_value
                FROM apolices
                GROUP BY tipo_residencia
                ORDER BY count DESC
            """, conn)
            
            conn.close()
            
            return {
                "general": {
                    "total_policies": int(general_stats.iloc[0]['total_policies']),
                    "average_value": float(general_stats.iloc[0]['avg_value'] or 0),
                    "min_value": float(general_stats.iloc[0]['min_value'] or 0),
                    "max_value": float(general_stats.iloc[0]['max_value'] or 0),
                    "average_risk_score": float(general_stats.iloc[0]['avg_risk_score'] or 0)
                },
                "risk_distribution": [
                    {"level": row['nivel_risco'], "count": int(row['count'])}
                    for _, row in risk_distribution.iterrows()
                ],
                "residence_types": [
                    {
                        "type": row['tipo_residencia'], 
                        "count": int(row['count']),
                        "average_value": float(row['avg_value'] or 0)
                    }
                    for _, row in residence_stats.iterrows()
                ]
            }
            
        except Exception as e:
            raise Exception(f"Erro ao calcular estatísticas: {str(e)}")
    
    @staticmethod
    def delete_policy(numero_apolice: str) -> bool:
        """Remove uma apólice do banco de dados"""
        try:
            conn = sqlite3.connect(PolicyService.DB_PATH)
            cursor = conn.cursor()
            
            # Verificar se a apólice existe
            cursor.execute("SELECT COUNT(*) FROM apolices WHERE numero_apolice = ?", (numero_apolice,))
            if cursor.fetchone()[0] == 0:
                conn.close()
                return False
            
            # Remover a apólice
            cursor.execute("DELETE FROM apolices WHERE numero_apolice = ?", (numero_apolice,))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            raise Exception(f"Erro ao remover apólice: {str(e)}")