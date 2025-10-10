"""
Serviço para gerenciamento de dados de apólices
"""
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import streamlit as st


class PolicyDataService:
    """Serviço responsável pelo gerenciamento de dados de apólices"""
    
    def __init__(self, db_path: str = 'database/radar_sinistro.db'):
        """
        Inicializa o serviço
        
        Args:
            db_path: Caminho para o banco de dados
        """
        self.db_path = db_path
    
    def get_all_policies(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Busca todas as apólices com filtros opcionais
        
        Args:
            filters: Dicionário com filtros de busca
            
        Returns:
            Lista de apólices
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT numero_apolice, segurado, cep, valor_segurado, 
                       tipo_residencia, score_risco, nivel_risco, 
                       probabilidade_sinistro, data_inclusao, notificada
                FROM apolices
                WHERE 1=1
            """
            params = []
            
            # Aplicar filtros se fornecidos
            if filters:
                if 'search' in filters and filters['search']:
                    query += " AND (numero_apolice LIKE ? OR segurado LIKE ?)"
                    search_term = f"%{filters['search']}%"
                    params.extend([search_term, search_term])
                
                if 'risk_level' in filters and filters['risk_level'] != 'Todos':
                    if 'Alto' in filters['risk_level']:
                        query += " AND score_risco >= 75"
                    elif 'Médio' in filters['risk_level']:
                        query += " AND score_risco >= 50 AND score_risco < 75"
                    elif 'Baixo' in filters['risk_level']:
                        query += " AND score_risco < 50"
                
                if 'property_type' in filters and filters['property_type'] != 'Todos':
                    query += " AND tipo_residencia = ?"
                    params.append(filters['property_type'].lower())
            
            query += " ORDER BY score_risco DESC, data_inclusao DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            # Converter para lista de dicionários
            policies = []
            for row in rows:
                policy = {
                    'numero_apolice': row[0],
                    'segurado': row[1],
                    'cep': row[2],
                    'valor_segurado': float(row[3]) if row[3] else 0,
                    'tipo_residencia': row[4],
                    'score_risco': float(row[5]) if row[5] else 0,
                    'nivel_risco': row[6] or 'baixo',
                    'probabilidade_sinistro': float(row[7]) if row[7] else 0,
                    'data_inclusao': row[8],
                    'notificada': bool(row[9]) if row[9] else False
                }
                policies.append(policy)
            
            return policies
            
        except Exception as e:
            st.error(f"Erro ao buscar apólices: {str(e)}")
            return []
    
    def get_policy_by_number(self, policy_number: str) -> Optional[Dict[str, Any]]:
        """
        Busca uma apólice específica pelo número
        
        Args:
            policy_number: Número da apólice
            
        Returns:
            Dados da apólice ou None se não encontrada
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT numero_apolice, segurado, cep, valor_segurado, 
                       tipo_residencia, score_risco, nivel_risco, 
                       probabilidade_sinistro, data_inclusao, notificada,
                       latitude, longitude
                FROM apolices
                WHERE numero_apolice = ?
            """, (policy_number,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'numero_apolice': row[0],
                    'segurado': row[1],
                    'cep': row[2],
                    'valor_segurado': float(row[3]) if row[3] else 0,
                    'tipo_residencia': row[4],
                    'score_risco': float(row[5]) if row[5] else 0,
                    'nivel_risco': row[6] or 'baixo',
                    'probabilidade_sinistro': float(row[7]) if row[7] else 0,
                    'data_inclusao': row[8],
                    'notificada': bool(row[9]) if row[9] else False,
                    'latitude': float(row[10]) if row[10] else None,
                    'longitude': float(row[11]) if row[11] else None
                }
            
            return None
            
        except Exception as e:
            st.error(f"Erro ao buscar apólice: {str(e)}")
            return None
    
    def get_risk_statistics(self) -> Dict[str, Any]:
        """
        Calcula estatísticas de risco das apólices
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Contar apólices por nível de risco
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN score_risco >= 75 THEN 1 ELSE 0 END) as alto_risco,
                    SUM(CASE WHEN score_risco >= 50 AND score_risco < 75 THEN 1 ELSE 0 END) as medio_risco,
                    SUM(CASE WHEN score_risco < 50 THEN 1 ELSE 0 END) as baixo_risco,
                    AVG(score_risco) as score_medio,
                    SUM(valor_segurado) as valor_total,
                    AVG(valor_segurado) as valor_medio
                FROM apolices
            """)
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                total = row[0] or 0
                return {
                    'total_policies': total,
                    'high_risk': row[1] or 0,
                    'medium_risk': row[2] or 0,
                    'low_risk': row[3] or 0,
                    'average_score': float(row[4]) if row[4] else 0,
                    'total_value': float(row[5]) if row[5] else 0,
                    'average_value': float(row[6]) if row[6] else 0,
                    'high_risk_percentage': (row[1] or 0) / total * 100 if total > 0 else 0,
                    'medium_risk_percentage': (row[2] or 0) / total * 100 if total > 0 else 0,
                    'low_risk_percentage': (row[3] or 0) / total * 100 if total > 0 else 0
                }
            
            return {}
            
        except Exception as e:
            st.error(f"Erro ao calcular estatísticas: {str(e)}")
            return {}
    
    def update_policy_risk_score(self, policy_number: str, new_score: float, new_level: str, probability: float) -> bool:
        """
        Atualiza o score de risco de uma apólice
        
        Args:
            policy_number: Número da apólice
            new_score: Novo score de risco
            new_level: Novo nível de risco
            probability: Nova probabilidade
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE apolices 
                SET score_risco = ?, nivel_risco = ?, probabilidade_sinistro = ?
                WHERE numero_apolice = ?
            """, (new_score, new_level, probability, policy_number))
            
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            
            return affected_rows > 0
            
        except Exception as e:
            st.error(f"Erro ao atualizar apólice: {str(e)}")
            return False
    
    def mark_policy_as_notified(self, policy_number: str) -> bool:
        """
        Marca uma apólice como notificada
        
        Args:
            policy_number: Número da apólice
            
        Returns:
            True se marcada com sucesso
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE apolices 
                SET notificada = 1
                WHERE numero_apolice = ?
            """, (policy_number,))
            
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            
            return affected_rows > 0
            
        except Exception as e:
            st.error(f"Erro ao marcar apólice como notificada: {str(e)}")
            return False
    
    def get_policies_by_risk_level(self, risk_level: str) -> List[Dict[str, Any]]:
        """
        Busca apólices por nível de risco
        
        Args:
            risk_level: Nível de risco ('alto', 'medio', 'baixo')
            
        Returns:
            Lista de apólices do nível especificado
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if risk_level.lower() == 'alto':
                query = "SELECT * FROM apolices WHERE score_risco >= 75"
            elif risk_level.lower() == 'medio':
                query = "SELECT * FROM apolices WHERE score_risco >= 50 AND score_risco < 75"
            elif risk_level.lower() == 'baixo':
                query = "SELECT * FROM apolices WHERE score_risco < 50"
            else:
                return []
            
            query += " ORDER BY score_risco DESC"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            # Converter para lista de dicionários
            policies = []
            for row in rows:
                policy = {
                    'numero_apolice': row[0],
                    'segurado': row[1],
                    'cep': row[2],
                    'valor_segurado': float(row[3]) if row[3] else 0,
                    'tipo_residencia': row[4],
                    'score_risco': float(row[5]) if row[5] else 0,
                    'nivel_risco': row[6] or 'baixo',
                    'probabilidade_sinistro': float(row[7]) if row[7] else 0,
                    'data_inclusao': row[8],
                    'notificada': bool(row[9]) if row[9] else False
                }
                policies.append(policy)
            
            return policies
            
        except Exception as e:
            st.error(f"Erro ao buscar apólices por nível de risco: {str(e)}")
            return []


# Instância global do serviço
policy_data_service = PolicyDataService()
