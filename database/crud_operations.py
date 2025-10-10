"""
Operações CRUD para o Sistema de Radar de Sinistro
"""

from typing import List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from .database import Database
from .models import (
    Apolice, SinistroHistorico, PrevisaoRisco, DadoClimatico,
    ApoliceAtiva, PrevisaoRecente, determinar_nivel_risco
)

logger = logging.getLogger(__name__)


class CRUDOperations:
    """Classe para operações CRUD no banco de dados"""
    
    def __init__(self, database: Database):
        self.db = database
    
    # ==================== OPERAÇÕES PARA APÓLICES ====================
    
    def insert_apolice(self, apolice: Apolice) -> int:
        """
        Insere uma nova apólice
        
        Args:
            apolice: Objeto Apolice para inserir
            
        Returns:
            ID da apólice inserida
        """
        query = """
        INSERT INTO apolices (
            numero_apolice, segurado, cep, latitude, longitude, tipo_residencia,
            valor_segurado, data_contratacao, data_inicio, ativa, 
            score_risco, nivel_risco, probabilidade_sinistro, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            apolice.numero_apolice,
            getattr(apolice, 'segurado', 'N/A'),
            apolice.cep,
            apolice.latitude,
            apolice.longitude,
            apolice.tipo_residencia,
            apolice.valor_segurado,
            apolice.data_contratacao,
            getattr(apolice, 'data_inicio', apolice.data_contratacao),
            apolice.ativa,
            getattr(apolice, 'score_risco', 0.0),
            getattr(apolice, 'nivel_risco', 'baixo'),
            getattr(apolice, 'probabilidade_sinistro', 0.0),
            datetime.now().isoformat()
        )
        
        try:
            apolice_id = self.db.execute_command(query, params)
            logger.info(f"Apólice {apolice.numero_apolice} inserida com ID {apolice_id}")
            return apolice_id
        except Exception as e:
            logger.error(f"Erro ao inserir apólice: {e}")
            raise
    
    def get_apolice_by_numero(self, numero_apolice: str) -> Optional[Apolice]:
        """Busca apólice por número"""
        query = "SELECT * FROM apolices WHERE numero_apolice = ?"
        results = self.db.execute_query(query, (numero_apolice,))
        
        if results:
            row = results[0]
            return Apolice(
                numero_apolice=row['numero_apolice'],
                segurado=row.get('segurado', 'N/A'),
                cep=row['cep'],
                tipo_residencia=row['tipo_residencia'],
                valor_segurado=row['valor_segurado'],
                data_contratacao=datetime.fromisoformat(row['data_contratacao']),
                email=row.get('email'),
                telefone=row.get('telefone'),
                latitude=row['latitude'],
                longitude=row['longitude'],
                ativa=bool(row['ativa']),
                id=row['id'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
            )
        return None
    
    def get_apolices_by_region(self, cep_prefix: str = None, 
                              lat_center: float = None, lon_center: float = None,
                              radius_km: float = 10) -> List[Apolice]:
        """
        Busca apólices por região (CEP ou coordenadas)
        
        Args:
            cep_prefix: Prefixo do CEP (ex: "01310")
            lat_center: Latitude central para busca por raio
            lon_center: Longitude central para busca por raio
            radius_km: Raio de busca em km
        """
        if cep_prefix:
            query = "SELECT * FROM apolices WHERE cep LIKE ? AND ativa = 1"
            params = (f"{cep_prefix}%",)
        elif lat_center and lon_center:
            # Busca por proximidade geográfica (aproximação simples)
            lat_delta = radius_km / 111.0  # 1 grau ≈ 111 km
            lon_delta = radius_km / (111.0 * abs(lat_center))
            
            query = """
            SELECT * FROM apolices 
            WHERE latitude BETWEEN ? AND ?
            AND longitude BETWEEN ? AND ?
            AND ativa = 1
            """
            params = (
                lat_center - lat_delta, lat_center + lat_delta,
                lon_center - lon_delta, lon_center + lon_delta
            )
        else:
            query = "SELECT * FROM apolices WHERE ativa = 1"
            params = ()
        
        results = self.db.execute_query(query, params)
        apolices = []
        
        for row in results:
            apolices.append(Apolice(
                numero_apolice=row['numero_apolice'],
                segurado=row.get('segurado', 'N/A'),
                cep=row['cep'],
                tipo_residencia=row['tipo_residencia'],
                valor_segurado=row['valor_segurado'],
                data_contratacao=datetime.fromisoformat(row['data_contratacao']),
                email=row.get('email'),
                telefone=row.get('telefone'),
                latitude=row['latitude'],
                longitude=row['longitude'],
                ativa=bool(row['ativa']),
                id=row['id']
            ))
        
        return apolices
    
    def update_apolice_coordinates(self, apolice_id: int, latitude: float, longitude: float):
        """Atualiza coordenadas de uma apólice"""
        query = "UPDATE apolices SET latitude = ?, longitude = ? WHERE id = ?"
        self.db.execute_command(query, (latitude, longitude, apolice_id))
        logger.info(f"Coordenadas atualizadas para apólice ID {apolice_id}")
    
    # ==================== OPERAÇÕES PARA SINISTROS ====================
    
    def insert_sinistro(self, sinistro: SinistroHistorico) -> int:
        """Insere um novo sinistro histórico"""
        query = """
        INSERT INTO sinistros_historicos (
            apolice_id, data_sinistro, tipo_sinistro, valor_prejuizo,
            causa, condicoes_climaticas, precipitacao_mm, vento_kmh, temperatura_c
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            sinistro.apolice_id,
            sinistro.data_sinistro,
            sinistro.tipo_sinistro,
            sinistro.valor_prejuizo,
            sinistro.causa,
            sinistro.condicoes_climaticas,
            sinistro.precipitacao_mm,
            sinistro.vento_kmh,
            sinistro.temperatura_c
        )
        
        sinistro_id = self.db.execute_command(query, params)
        logger.info(f"Sinistro inserido com ID {sinistro_id}")
        return sinistro_id
    
    def get_sinistros_by_region(self, lat: float, lon: float, radius_km: float = 5) -> List[SinistroHistorico]:
        """Busca sinistros históricos por região geográfica"""
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * abs(lat))
        
        query = """
        SELECT s.* FROM sinistros_historicos s
        JOIN apolices a ON s.apolice_id = a.id
        WHERE a.latitude BETWEEN ? AND ?
        AND a.longitude BETWEEN ? AND ?
        ORDER BY s.data_sinistro DESC
        """
        params = (lat - lat_delta, lat + lat_delta, lon - lon_delta, lon + lon_delta)
        
        results = self.db.execute_query(query, params)
        sinistros = []
        
        for row in results:
            sinistros.append(SinistroHistorico(
                id=row['id'],
                apolice_id=row['apolice_id'],
                data_sinistro=datetime.fromisoformat(row['data_sinistro']),
                tipo_sinistro=row['tipo_sinistro'],
                valor_prejuizo=row['valor_prejuizo'],
                causa=row['causa'],
                condicoes_climaticas=row['condicoes_climaticas'],
                precipitacao_mm=row['precipitacao_mm'],
                vento_kmh=row['vento_kmh'],
                temperatura_c=row['temperatura_c']
            ))
        
        return sinistros
    
    # ==================== OPERAÇÕES PARA PREVISÕES ====================
    
    def insert_previsao(self, previsao: PrevisaoRisco) -> int:
        """Insere uma nova previsão de risco"""
        query = """
        INSERT INTO previsoes_risco (
            apolice_id, data_previsao, score_risco, nivel_risco,
            fatores_risco, dados_climaticos, modelo_versao
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            previsao.apolice_id,
            previsao.data_previsao,
            previsao.score_risco,
            previsao.nivel_risco,
            previsao.fatores_risco,
            previsao.dados_climaticos,
            previsao.modelo_versao
        )
        
        previsao_id = self.db.execute_command(query, params)
        logger.info(f"Previsão inserida com ID {previsao_id}")
        return previsao_id
    
    def get_latest_predictions(self, limit: int = 100) -> List[PrevisaoRecente]:
        """Busca as previsões mais recentes"""
        query = "SELECT * FROM vw_previsoes_recentes LIMIT ?"
        results = self.db.execute_query(query, (limit,))
        
        previsoes = []
        for row in results:
            previsoes.append(PrevisaoRecente(
                id=row['id'],
                apolice_id=row['apolice_id'],
                data_previsao=datetime.fromisoformat(row['data_previsao']),
                score_risco=row['score_risco'],
                nivel_risco=row['nivel_risco'],
                numero_apolice=row['numero_apolice'],
                cep=row['cep'],
                tipo_residencia=row['tipo_residencia'],
                valor_segurado=row['valor_segurado']
            ))
        
        return previsoes
    
    def get_high_risk_policies(self, min_score: float = 70.0) -> List[Tuple]:
        """Busca apólices com alto risco"""
        query = """
        SELECT a.numero_apolice, a.cep, a.tipo_residencia, a.valor_segurado,
               p.score_risco, p.nivel_risco, p.data_previsao
        FROM apolices a
        JOIN previsoes_risco p ON a.id = p.apolice_id
        WHERE p.score_risco >= ? AND a.ativa = 1
        AND p.data_previsao >= datetime('now', '-1 day')
        ORDER BY p.score_risco DESC
        """
        
        return self.db.execute_query(query, (min_score,))
    
    # ==================== OPERAÇÕES PARA DADOS CLIMÁTICOS ====================
    
    def insert_dado_climatico(self, dado: DadoClimatico) -> int:
        """Insere dados climáticos"""
        query = """
        INSERT INTO dados_climaticos (
            latitude, longitude, data_coleta, temperatura_c, precipitacao_mm,
            vento_kmh, umidade_percent, pressao_hpa, fonte
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            dado.latitude, dado.longitude, dado.data_coleta,
            dado.temperatura_c, dado.precipitacao_mm, dado.vento_kmh,
            dado.umidade_percent, dado.pressao_hpa, dado.fonte
        )
        
        return self.db.execute_command(query, params)
    
    def get_dados_climaticos_recentes(self, lat: float, lon: float, 
                                    horas: int = 24) -> List[DadoClimatico]:
        """Busca dados climáticos recentes por localização"""
        lat_delta = 0.1  # ~11km
        lon_delta = 0.1
        
        query = """
        SELECT * FROM dados_climaticos
        WHERE latitude BETWEEN ? AND ?
        AND longitude BETWEEN ? AND ?
        AND data_coleta >= datetime('now', '-{} hours')
        ORDER BY data_coleta DESC
        """.format(horas)
        
        params = (lat - lat_delta, lat + lat_delta, lon - lon_delta, lon + lon_delta)
        results = self.db.execute_query(query, params)
        
        dados = []
        for row in results:
            dados.append(DadoClimatico(
                id=row['id'],
                latitude=row['latitude'],
                longitude=row['longitude'],
                data_coleta=datetime.fromisoformat(row['data_coleta']),
                temperatura_c=row['temperatura_c'],
                precipitacao_mm=row['precipitacao_mm'],
                vento_kmh=row['vento_kmh'],
                umidade_percent=row['umidade_percent'],
                pressao_hpa=row['pressao_hpa'],
                fonte=row['fonte']
            ))
        
        return dados
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def get_apolices_ativas_stats(self) -> List[ApoliceAtiva]:
        """Busca estatísticas de apólices ativas"""
        query = "SELECT * FROM vw_apolices_ativas ORDER BY total_sinistros DESC"
        results = self.db.execute_query(query)
        
        stats = []
        for row in results:
            stats.append(ApoliceAtiva(
                id=row['id'],
                numero_apolice=row['numero_apolice'],
                cep=row['cep'],
                latitude=row['latitude'],
                longitude=row['longitude'],
                tipo_residencia=row['tipo_residencia'],
                valor_segurado=row['valor_segurado'],
                data_contratacao=datetime.fromisoformat(row['data_contratacao']),
                total_sinistros=row['total_sinistros'],
                valor_total_sinistros=row['valor_total_sinistros']
            ))
        
        return stats

    # ==================== NOTIFICAÇÕES DE RISCO ====================

    def insert_notificacao_risco(self,
                                  apolice_id: int,
                                  numero_apolice: str,
                                  segurado: str = None,
                                  email: str = None,
                                  telefone: str = None,
                                  canal: str = 'simulado',
                                  mensagem: str = 'Mensagem de risco simulada',
                                  score_risco: float = None,
                                  nivel_risco: str = None,
                                  simulacao: bool = True,
                                  status: str = 'sucesso',
                                  erro: str = None) -> int:
        """Registra uma notificação (simulada ou real). Idempotente por (numero_apolice, canal, dia)."""
        query = """
        INSERT OR IGNORE INTO notificacoes_risco (
            apolice_id, numero_apolice, segurado, email, telefone,
            canal, mensagem, score_risco_enviado, nivel_risco_enviado,
            simulacao, status, erro
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            apolice_id,
            numero_apolice,
            segurado,
            email,
            telefone,
            canal,
            mensagem,
            score_risco,
            nivel_risco,
            1 if simulacao else 0,
            status,
            erro
        )
        try:
            return self.db.execute_command(query, params)
        except Exception as e:
            msg = str(e).lower()
            if 'no such table' in msg and 'notificacoes_risco' in msg:
                # Tentar criar tabela on-the-fly
                try:
                    self.db._ensure_additional_tables()  # type: ignore (método interno)
                    return self.db.execute_command(query, params)
                except Exception as e2:
                    logger.warning(f"Primeira tentativa de criar notificacoes_risco falhou: {e2}. Tentando criação explícita...")
                    create_sql = """
                    CREATE TABLE IF NOT EXISTS notificacoes_risco (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        apolice_id INTEGER NOT NULL,
                        numero_apolice VARCHAR(50) NOT NULL,
                        segurado VARCHAR(100),
                        email TEXT,
                        telefone TEXT,
                        canal VARCHAR(20) NOT NULL,
                        mensagem TEXT NOT NULL,
                        score_risco_enviado DECIMAL(5,2),
                        nivel_risco_enviado VARCHAR(10),
                        enviado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        simulacao BOOLEAN DEFAULT 1,
                        status VARCHAR(20) DEFAULT 'sucesso',
                        erro TEXT
                    );
                    CREATE INDEX IF NOT EXISTS idx_notificacoes_apolice ON notificacoes_risco(apolice_id);
                    CREATE INDEX IF NOT EXISTS idx_notificacoes_data ON notificacoes_risco(enviado_em);
                    """
                    try:
                        self.db.execute_command(create_sql)
                        return self.db.execute_command(query, params)
                    except Exception as e3:
                        logger.error(f"Falha na criação explícita da tabela notificacoes_risco: {e3}")
                        raise
            logger.error(f"Erro ao registrar notificação: {e}")
            raise

    def get_notificacoes_por_apolices(self, numeros_apolice: List[str]) -> dict:
        """Retorna últimas notificações (por dia) para um conjunto de apólices."""
        if not numeros_apolice:
            return {}
        placeholders = ','.join(['?'] * len(numeros_apolice))
        query = f"""
        SELECT numero_apolice, MAX(enviado_em) as ultimo_envio,
               COUNT(*) as total_envios_dia,
               MAX(status) as status
        FROM notificacoes_risco
        WHERE numero_apolice IN ({placeholders})
          AND date(enviado_em) = date('now')
        GROUP BY numero_apolice
        """
        try:
            rows = self.db.execute_query(query, tuple(numeros_apolice))
            return {row['numero_apolice']: {
                'ultimo_envio': row['ultimo_envio'],
                'total_envios_dia': row['total_envios_dia'],
                'status': row['status']
            } for row in rows}
        except Exception as e:
            logger.error(f"Erro ao buscar notificações: {e}")
            return {}