"""
DAO para gerenciar riscos por cobertura
Responsável por todas as operações de persistência relacionadas aos riscos detalhados por cobertura
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CoberturaRiscoData:
    """Modelo de dados para risco por cobertura"""
    nr_apolice: str
    cd_cobertura: int
    cd_produto: int
    score_risco: float
    nivel_risco: str
    probabilidade: float
    modelo_usado: str = None
    versao_modelo: str = None
    fatores_risco: Dict = None
    dados_climaticos: Dict = None
    dados_propriedade: Dict = None
    resultado_predicao: Dict = None
    confianca_modelo: float = None
    explicabilidade: Dict = None
    tempo_processamento_ms: int = None
    data_calculo: datetime = None
    
    def __post_init__(self):
        if self.data_calculo is None:
            self.data_calculo = datetime.now()


class CoberturaRiscoDAO:
    """DAO para operações de risco por cobertura"""
    
    def __init__(self, db_path: str = 'database/radar_sinistro.db'):
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obter conexão com o banco de dados"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
        return conn
    
    def salvar_risco_cobertura(self, risco_data: CoberturaRiscoData) -> int:
        """
        Salvar análise de risco de uma cobertura específica
        
        Args:
            risco_data: Dados do risco calculado
            
        Returns:
            ID do registro inserido
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Converter objetos para JSON
            fatores_json = json.dumps(risco_data.fatores_risco) if risco_data.fatores_risco else None
            climaticos_json = json.dumps(risco_data.dados_climaticos) if risco_data.dados_climaticos else None
            propriedade_json = json.dumps(risco_data.dados_propriedade) if risco_data.dados_propriedade else None
            resultado_json = json.dumps(risco_data.resultado_predicao) if risco_data.resultado_predicao else None
            explicabilidade_json = json.dumps(risco_data.explicabilidade) if risco_data.explicabilidade else None
            
            # SQL de inserção
            sql = """
            INSERT INTO cobertura_risco (
                nr_apolice, cd_cobertura, cd_produto, score_risco, nivel_risco, probabilidade,
                modelo_usado, versao_modelo, fatores_risco, dados_climaticos, dados_propriedade,
                resultado_predicao, confianca_modelo, explicabilidade, tempo_processamento_ms,
                data_calculo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(sql, (
                risco_data.nr_apolice,
                risco_data.cd_cobertura,
                risco_data.cd_produto,
                risco_data.score_risco,
                risco_data.nivel_risco,
                risco_data.probabilidade,
                risco_data.modelo_usado,
                risco_data.versao_modelo,
                fatores_json,
                climaticos_json,
                propriedade_json,
                resultado_json,
                risco_data.confianca_modelo,
                explicabilidade_json,
                risco_data.tempo_processamento_ms,
                risco_data.data_calculo.isoformat()
            ))
            
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Risco salvo para apólice {risco_data.nr_apolice}, cobertura {risco_data.cd_cobertura}, ID: {record_id}")
            return record_id
            
        except sqlite3.IntegrityError as e:
            logger.error(f"Erro de integridade ao salvar risco: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao salvar risco por cobertura: {e}")
            raise
    
    def salvar_multiplos_riscos(self, riscos_list: List[CoberturaRiscoData]) -> List[int]:
        """
        Salvar múltiplas análises de risco em uma transação
        
        Args:
            riscos_list: Lista de dados de risco
            
        Returns:
            Lista de IDs dos registros inseridos
        """
        if not riscos_list:
            return []
        
        conn = self._get_connection()
        cursor = conn.cursor()
        record_ids = []
        
        try:
            for risco_data in riscos_list:
                # Converter objetos para JSON
                fatores_json = json.dumps(risco_data.fatores_risco) if risco_data.fatores_risco else None
                climaticos_json = json.dumps(risco_data.dados_climaticos) if risco_data.dados_climaticos else None
                propriedade_json = json.dumps(risco_data.dados_propriedade) if risco_data.dados_propriedade else None
                resultado_json = json.dumps(risco_data.resultado_predicao) if risco_data.resultado_predicao else None
                explicabilidade_json = json.dumps(risco_data.explicabilidade) if risco_data.explicabilidade else None
                
                # SQL de inserção
                sql = """
                INSERT INTO cobertura_risco (
                    nr_apolice, cd_cobertura, cd_produto, score_risco, nivel_risco, probabilidade,
                    modelo_usado, versao_modelo, fatores_risco, dados_climaticos, dados_propriedade,
                    resultado_predicao, confianca_modelo, explicabilidade, tempo_processamento_ms,
                    data_calculo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(sql, (
                    risco_data.nr_apolice,
                    risco_data.cd_cobertura,
                    risco_data.cd_produto,
                    risco_data.score_risco,
                    risco_data.nivel_risco,
                    risco_data.probabilidade,
                    risco_data.modelo_usado,
                    risco_data.versao_modelo,
                    fatores_json,
                    climaticos_json,
                    propriedade_json,
                    resultado_json,
                    risco_data.confianca_modelo,
                    explicabilidade_json,
                    risco_data.tempo_processamento_ms,
                    risco_data.data_calculo.isoformat()
                ))
                
                record_ids.append(cursor.lastrowid)
            
            conn.commit()
            logger.info(f"Salvos {len(record_ids)} riscos por cobertura em batch")
            return record_ids
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao salvar múltiplos riscos: {e}")
            raise
        finally:
            conn.close()
    
    def buscar_riscos_por_apolice(self, nr_apolice: str, ultima_analise: bool = True) -> List[Dict]:
        """
        Buscar riscos de todas as coberturas de uma apólice
        
        Args:
            nr_apolice: Número da apólice
            ultima_analise: Se True, retorna apenas as análises mais recentes
            
        Returns:
            Lista de dicionários com dados dos riscos
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if ultima_analise:
                # Usar view para últimas análises
                sql = """
                SELECT * FROM vw_ultima_analise_cobertura 
                WHERE nr_apolice = ?
                ORDER BY score_risco DESC
                """
            else:
                # Buscar todos os históricos
                sql = """
                SELECT cr.*, c.nm_cobertura, c.dv_basica
                FROM cobertura_risco cr
                JOIN coberturas c ON cr.cd_cobertura = c.cd_cobertura
                WHERE cr.nr_apolice = ?
                ORDER BY cr.data_calculo DESC, cr.score_risco DESC
                """
            
            cursor.execute(sql, (nr_apolice,))
            rows = cursor.fetchall()
            
            # Converter para lista de dicionários e deserializar JSON
            result = []
            for row in rows:
                row_dict = dict(row)
                
                # Deserializar campos JSON
                if row_dict.get('fatores_risco'):
                    try:
                        row_dict['fatores_risco'] = json.loads(row_dict['fatores_risco'])
                    except json.JSONDecodeError:
                        row_dict['fatores_risco'] = None
                
                if row_dict.get('dados_climaticos'):
                    try:
                        row_dict['dados_climaticos'] = json.loads(row_dict['dados_climaticos'])
                    except json.JSONDecodeError:
                        row_dict['dados_climaticos'] = None
                
                if row_dict.get('dados_propriedade'):
                    try:
                        row_dict['dados_propriedade'] = json.loads(row_dict['dados_propriedade'])
                    except json.JSONDecodeError:
                        row_dict['dados_propriedade'] = None
                
                if row_dict.get('resultado_predicao'):
                    try:
                        row_dict['resultado_predicao'] = json.loads(row_dict['resultado_predicao'])
                    except json.JSONDecodeError:
                        row_dict['resultado_predicao'] = None
                
                if row_dict.get('explicabilidade'):
                    try:
                        row_dict['explicabilidade'] = json.loads(row_dict['explicabilidade'])
                    except json.JSONDecodeError:
                        row_dict['explicabilidade'] = None
                
                result.append(row_dict)
            
            conn.close()
            return result
            
        except Exception as e:
            logger.error(f"Erro ao buscar riscos da apólice {nr_apolice}: {e}")
            return []
    
    def buscar_ranking_coberturas(self, limite: int = 10) -> List[Dict]:
        """
        Buscar ranking de coberturas por risco (últimos 30 dias)
        
        Args:
            limite: Número máximo de coberturas no ranking
            
        Returns:
            Lista com ranking de coberturas por risco
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            sql = f"""
            SELECT * FROM vw_ranking_risco_cobertura
            LIMIT ?
            """
            
            cursor.execute(sql, (limite,))
            rows = cursor.fetchall()
            
            result = [dict(row) for row in rows]
            conn.close()
            return result
            
        except Exception as e:
            logger.error(f"Erro ao buscar ranking de coberturas: {e}")
            return []
    
    def buscar_historico_risco(self, nr_apolice: str, cd_cobertura: int) -> List[Dict]:
        """
        Buscar histórico de análises de uma cobertura específica
        
        Args:
            nr_apolice: Número da apólice
            cd_cobertura: Código da cobertura
            
        Returns:
            Lista com histórico ordenado por data (mais recente primeiro)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            sql = """
            SELECT * FROM vw_historico_analise_cobertura
            WHERE nr_apolice = ? AND cd_cobertura = ?
            ORDER BY data_calculo DESC
            """
            
            cursor.execute(sql, (nr_apolice, cd_cobertura))
            rows = cursor.fetchall()
            
            result = [dict(row) for row in rows]
            conn.close()
            return result
            
        except Exception as e:
            logger.error(f"Erro ao buscar histórico de risco: {e}")
            return []
    
    def limpar_riscos_apolice(self, nr_apolice: str) -> int:
        """
        Remover todos os riscos de uma apólice
        
        Args:
            nr_apolice: Número da apólice
            
        Returns:
            Número de registros removidos
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM cobertura_risco WHERE nr_apolice = ?", (nr_apolice,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Removidos {deleted_count} riscos da apólice {nr_apolice}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Erro ao limpar riscos da apólice {nr_apolice}: {e}")
            raise
    
    def get_estatisticas_gerais(self) -> Dict:
        """
        Obter estatísticas gerais dos riscos por cobertura
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Estatísticas básicas
            cursor.execute("""
            SELECT 
                COUNT(*) as total_analises,
                COUNT(DISTINCT nr_apolice) as total_apolices,
                COUNT(DISTINCT cd_cobertura) as total_coberturas,
                AVG(score_risco) as score_medio,
                MAX(score_risco) as score_maximo,
                MIN(score_risco) as score_minimo,
                COUNT(CASE WHEN nivel_risco IN ('alto', 'critico') THEN 1 END) as alto_risco_count,
                AVG(tempo_processamento_ms) as tempo_medio_ms
            FROM cobertura_risco
            WHERE data_calculo >= datetime('now', '-30 days')
            """)
            
            stats = dict(cursor.fetchone())
            conn.close()
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas gerais: {e}")
            return {}