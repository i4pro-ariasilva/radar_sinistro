"""
Operações CRUD para o Sistema de Radar de Sinistro
"""

from typing import List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from .database import Database
from .models import (
    Apolice, SinistroHistorico, PrevisaoRisco, DadoClimatico,
    ApoliceAtiva, PrevisaoRecente, determinar_nivel_risco,
    RegionBlock
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
            numero_apolice, segurado, cd_produto, cep, latitude, longitude, tipo_residencia,
            valor_segurado, data_contratacao, data_inicio, ativa, 
            score_risco, nivel_risco, probabilidade_sinistro, email, telefone, notificada, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            apolice.numero_apolice,
            getattr(apolice, 'segurado', 'N/A'),
            getattr(apolice, 'cd_produto', None),
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
            getattr(apolice, 'email', None),
            getattr(apolice, 'telefone', None),
            getattr(apolice, 'notificada', 0),
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
                id=row['id'],
                numero_apolice=row['numero_apolice'],
                segurado=row['segurado'],
                cd_produto=row['cd_produto'] if 'cd_produto' in row.keys() else None,
                cep=row['cep'],
                latitude=row['latitude'],
                longitude=row['longitude'],
                tipo_residencia=row['tipo_residencia'],
                valor_segurado=row['valor_segurado'],
                data_contratacao=datetime.fromisoformat(row['data_contratacao']),
                ativa=bool(row['ativa']),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
                # Campos estendidos
                data_inicio=datetime.fromisoformat(row['data_inicio']) if row['data_inicio'] else None,
                score_risco=row['score_risco'] if 'score_risco' in row.keys() else 0.0,
                nivel_risco=row['nivel_risco'] if 'nivel_risco' in row.keys() else 'baixo',
                probabilidade_sinistro=row['probabilidade_sinistro'] if 'probabilidade_sinistro' in row.keys() else 0.0,
                email=row['email'] if 'email' in row.keys() else None,
                telefone=row['telefone'] if 'telefone' in row.keys() else None,
                notificada=row['notificada'] if 'notificada' in row.keys() else 0
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
                id=row['id'],
                numero_apolice=row['numero_apolice'],
                cep=row['cep'],
                latitude=row['latitude'],
                longitude=row['longitude'],
                tipo_residencia=row['tipo_residencia'],
                valor_segurado=row['valor_segurado'],
                data_contratacao=datetime.fromisoformat(row['data_contratacao']),
                ativa=bool(row['ativa'])
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

    # ==================== BLOQUEIOS POR REGIÃO (CEP PREFIX) ====================

    @staticmethod
    def _normalize_cep(cep: str) -> str:
        """Remove caracteres não numéricos e retorna apenas dígitos."""
        if not cep:
            return ""
        return "".join(filter(str.isdigit, cep))

    @staticmethod
    def _generate_prefixes(cep_digits: str, min_len: int = 3, max_len: int = 8) -> List[str]:
        """Gera lista de prefixos decrescentes para lookup (mais específico primeiro)."""
        if not cep_digits:
            return []
        length = len(cep_digits)
        upper = min(length, max_len)
        prefixes = []
        for l in range(upper, min_len - 1, -1):  # decresce
            prefixes.append(cep_digits[:l])
        return prefixes

    def create_block(self, cep_prefix: str, reason: str, severity: int = 1,
                     scope: str = "residencial", created_by: str = "system") -> int:
        """Cria um bloqueio por prefixo de CEP. Usa inserção ou atualização se já existir."""
        cep_prefix_digits = self._normalize_cep(cep_prefix)
        if not (3 <= len(cep_prefix_digits) <= 8):
            raise ValueError("Prefixo de CEP deve ter entre 3 e 8 dígitos")

        # Tentar inserir; se existir, atualizar
        existing = self.db.execute_query(
            "SELECT id FROM region_blocks WHERE cep_prefix = ?", (cep_prefix_digits,)
        )
        now_iso = datetime.now().isoformat()
        if existing:
            query = """
            UPDATE region_blocks
            SET blocked = 1, reason = ?, severity = ?, scope = ?, active = 1,
                updated_at = ?, updated_by = ?
            WHERE id = ?
            """
            self.db.execute_command(query, (reason, severity, scope, now_iso, created_by, existing[0]['id']))
            # LOG_EVENT BLOCK_UPDATE prefix=<cep_prefix> severity=<severity>
            logger.info(f"BLOCK_UPDATE prefix={cep_prefix_digits} severity={severity} scope={scope}")
            return existing[0]['id']
        else:
            query = """
            INSERT INTO region_blocks (cep_prefix, blocked, reason, severity, scope, active, created_at, created_by, updated_at, updated_by)
            VALUES (?, 1, ?, ?, ?, 1, ?, ?, ?, ?)
            """
            block_id = self.db.execute_command(query, (
                cep_prefix_digits, reason, severity, scope,
                now_iso, created_by, now_iso, created_by
            ))
            # LOG_EVENT BLOCK_CREATE prefix=<cep_prefix> id=<block_id>
            logger.info(f"BLOCK_CREATE prefix={cep_prefix_digits} id={block_id} severity={severity} scope={scope}")
            return block_id

    def remove_block(self, cep_prefix: str, updated_by: str = "system", hard_delete: bool = False) -> None:
        """Remove ou desativa bloqueio de prefixo de CEP."""
        cep_prefix_digits = self._normalize_cep(cep_prefix)
        if hard_delete:
            self.db.execute_command(
                "DELETE FROM region_blocks WHERE cep_prefix = ?", (cep_prefix_digits,)
            )
            # LOG_EVENT BLOCK_REMOVE prefix=<cep_prefix> hard_delete=true
            logger.info(f"BLOCK_REMOVE prefix={cep_prefix_digits} hard=true")
        else:
            now_iso = datetime.now().isoformat()
            self.db.execute_command(
                "UPDATE region_blocks SET active = 0, blocked = 0, updated_at = ?, updated_by = ? WHERE cep_prefix = ?",
                (now_iso, updated_by, cep_prefix_digits)
            )
            # LOG_EVENT BLOCK_DEACTIVATE prefix=<cep_prefix>
            logger.info(f"BLOCK_DEACTIVATE prefix={cep_prefix_digits}")

    def set_block_status(self, cep_prefix: str, blocked: bool, reason: Optional[str] = None,
                         updated_by: str = "system") -> None:
        """Altera status (bloqueado/liberado) mantendo registro ativo."""
        cep_prefix_digits = self._normalize_cep(cep_prefix)
        now_iso = datetime.now().isoformat()
        self.db.execute_command(
            "UPDATE region_blocks SET blocked = ?, reason = COALESCE(?, reason), updated_at = ?, updated_by = ? WHERE cep_prefix = ?",
            (1 if blocked else 0, reason, now_iso, updated_by, cep_prefix_digits)
        )
        # LOG_EVENT BLOCK_STATUS prefix=<cep_prefix> blocked=<blocked>
        logger.info(f"BLOCK_STATUS prefix={cep_prefix_digits} blocked={blocked}")

    def list_blocks(self, active_only: bool = True, scope: Optional[str] = None) -> List[RegionBlock]:
        """Lista bloqueios conforme filtros."""
        conditions = []
        params: List = []
        if active_only:
            conditions.append("active = 1")
        if scope:
            conditions.append("(scope = ? OR scope IS NULL)")
            params.append(scope)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM region_blocks {where_clause} ORDER BY LENGTH(cep_prefix) DESC"
        rows = self.db.execute_query(query, tuple(params))
        blocks: List[RegionBlock] = []
        for r in rows:
            blocks.append(RegionBlock(
                id=r['id'],
                cep_prefix=r['cep_prefix'],
                blocked=bool(r['blocked']),
                reason=r['reason'] or "",
                severity=r['severity'] or 1,
                scope=r['scope'] or "residencial",
                active=bool(r['active']),
                created_at=datetime.fromisoformat(r['created_at']) if r['created_at'] else None,
                created_by=r['created_by'],
                updated_at=datetime.fromisoformat(r['updated_at']) if r['updated_at'] else None,
                updated_by=r['updated_by']
            ))
        return blocks

    def lookup_region_block(self, cep: str, scope: str = "residencial") -> Optional[RegionBlock]:
        """Retorna bloqueio mais específico (prefixo maior) aplicável ao CEP informado."""
        cep_digits = self._normalize_cep(cep)
        if len(cep_digits) < 3:
            return None
        prefixes = self._generate_prefixes(cep_digits)
        # Consulta única com IN
        placeholders = ",".join(["?"] * len(prefixes))
        query = f"""
            SELECT * FROM region_blocks
            WHERE cep_prefix IN ({placeholders})
              AND active = 1
              AND (scope = ? OR scope IS NULL)
            ORDER BY LENGTH(cep_prefix) DESC
            LIMIT 1
        """
        params = prefixes + [scope]
        rows = self.db.execute_query(query, tuple(params))
        if not rows:
            return None
        r = rows[0]
        return RegionBlock(
            id=r['id'],
            cep_prefix=r['cep_prefix'],
            blocked=bool(r['blocked']),
            reason=r['reason'] or "",
            severity=r['severity'] or 1,
            scope=r['scope'] or "residencial",
            active=bool(r['active']),
            created_at=datetime.fromisoformat(r['created_at']) if r['created_at'] else None,
            created_by=r['created_by'],
            updated_at=datetime.fromisoformat(r['updated_at']) if r['updated_at'] else None,
            updated_by=r['updated_by']
        )

    def is_cep_blocked(self, cep: str, scope: str = "residencial") -> Tuple[bool, Optional[str], Optional[int]]:
        """Verifica se o CEP está bloqueado. Retorna (blocked, reason, severity)."""
        block = self.lookup_region_block(cep, scope=scope)
        if block and block.is_effective():
            # LOG_EVENT BLOCK_MATCH cep=<cep> prefix=<block_prefix> severity=<severity>
            logger.info(f"BLOCK_MATCH cep={cep} prefix={block.cep_prefix} severity={block.severity}")
            return True, block.reason or None, block.severity
        # Mesmo que não esteja bloqueado, se existir registro retornamos a reason para contexto.
        if block:
            return False, block.reason or None, None
        return False, None, None


    # ==================== OPERAÇÕES PARA PRODUTOS ====================
    
    def insert_produto(self, produto) -> int:
        """Insere um novo produto"""
        from .models import Produto
        query = """
        INSERT INTO produtos (cd_produto, cd_ramo, nm_produto, dt_criacao, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (
            produto.cd_produto,
            produto.cd_ramo,
            produto.nm_produto,
            produto.dt_criacao,
            produto.created_at
        )
        return self.db.execute_command(query, params)
    
    def get_produto_by_codigo(self, cd_produto: int):
        """Busca produto por código"""
        from .models import Produto
        query = "SELECT * FROM produtos WHERE cd_produto = ?"
        rows = self.db.execute_query(query, (cd_produto,))
        if rows:
            r = rows[0]
            return Produto(
                cd_produto=r['cd_produto'],
                cd_ramo=r['cd_ramo'],
                nm_produto=r['nm_produto'],
                dt_criacao=datetime.fromisoformat(r['dt_criacao']) if r['dt_criacao'] else None,
                created_at=datetime.fromisoformat(r['created_at']) if r['created_at'] else None,
                updated_at=datetime.fromisoformat(r['updated_at']) if r['updated_at'] else None
            )
        return None
    
    def get_produtos_by_ramo(self, cd_ramo: int) -> List:
        """Busca produtos por ramo"""
        from .models import Produto
        query = "SELECT * FROM produtos WHERE cd_ramo = ? ORDER BY nm_produto"
        rows = self.db.execute_query(query, (cd_ramo,))
        produtos = []
        for r in rows:
            produtos.append(Produto(
                cd_produto=r['cd_produto'],
                cd_ramo=r['cd_ramo'],
                nm_produto=r['nm_produto'],
                dt_criacao=datetime.fromisoformat(r['dt_criacao']) if r['dt_criacao'] else None,
                created_at=datetime.fromisoformat(r['created_at']) if r['created_at'] else None,
                updated_at=datetime.fromisoformat(r['updated_at']) if r['updated_at'] else None
            ))
        return produtos

    # ==================== OPERAÇÕES PARA COBERTURAS ====================
    
    def insert_cobertura(self, cobertura) -> int:
        """Insere uma nova cobertura"""
        from .models import Cobertura
        query = """
        INSERT INTO coberturas (cd_cobertura, cd_produto, nm_cobertura, dv_basica, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (
            cobertura.cd_cobertura,
            cobertura.cd_produto,
            cobertura.nm_cobertura,
            cobertura.dv_basica,
            cobertura.created_at
        )
        return self.db.execute_command(query, params)
    
    def get_cobertura_by_codigo(self, cd_cobertura: int):
        """Busca cobertura por código"""
        from .models import Cobertura
        query = "SELECT * FROM coberturas WHERE cd_cobertura = ?"
        rows = self.db.execute_query(query, (cd_cobertura,))
        if rows:
            r = rows[0]
            return Cobertura(
                cd_cobertura=r['cd_cobertura'],
                cd_produto=r['cd_produto'],
                nm_cobertura=r['nm_cobertura'],
                dv_basica=bool(r['dv_basica']),
                created_at=datetime.fromisoformat(r['created_at']) if r['created_at'] else None,
                updated_at=datetime.fromisoformat(r['updated_at']) if r['updated_at'] else None
            )
        return None
    
    def get_coberturas_by_produto(self, cd_produto: int) -> List:
        """Busca coberturas por produto"""
        from .models import Cobertura
        query = "SELECT * FROM coberturas WHERE cd_produto = ? ORDER BY dv_basica DESC, nm_cobertura"
        rows = self.db.execute_query(query, (cd_produto,))
        coberturas = []
        for r in rows:
            coberturas.append(Cobertura(
                cd_cobertura=r['cd_cobertura'],
                cd_produto=r['cd_produto'],
                nm_cobertura=r['nm_cobertura'],
                dv_basica=bool(r['dv_basica']),
                created_at=datetime.fromisoformat(r['created_at']) if r['created_at'] else None,
                updated_at=datetime.fromisoformat(r['updated_at']) if r['updated_at'] else None
            ))
        return coberturas

    # ==================== OPERAÇÕES PARA APÓLICE-COBERTURA ====================
    
    def insert_apolice_cobertura(self, apolice_cobertura) -> int:
        """Insere uma nova relação apólice-cobertura"""
        from .models import ApoliceCobertura
        query = """
        INSERT INTO apolice_cobertura (cd_cobertura, cd_produto, nr_apolice, dt_inclusao, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (
            apolice_cobertura.cd_cobertura,
            apolice_cobertura.cd_produto,
            apolice_cobertura.nr_apolice,
            apolice_cobertura.dt_inclusao,
            apolice_cobertura.created_at
        )
        return self.db.execute_command(query, params)
    
    def get_coberturas_by_apolice(self, nr_apolice: str) -> List:
        """Busca coberturas de uma apólice"""
        from .models import ApoliceCobertura
        query = """
        SELECT ac.*, c.nm_cobertura, c.dv_basica, p.nm_produto 
        FROM apolice_cobertura ac
        JOIN coberturas c ON ac.cd_cobertura = c.cd_cobertura
        JOIN produtos p ON ac.cd_produto = p.cd_produto
        WHERE ac.nr_apolice = ?
        ORDER BY c.dv_basica DESC, c.nm_cobertura
        """
        rows = self.db.execute_query(query, (nr_apolice,))
        resultado = []
        for r in rows:
            resultado.append({
                'id': r['id'],
                'cd_cobertura': r['cd_cobertura'],
                'cd_produto': r['cd_produto'],
                'nr_apolice': r['nr_apolice'],
                'dt_inclusao': r['dt_inclusao'],
                'nm_cobertura': r['nm_cobertura'],
                'dv_basica': bool(r['dv_basica']),
                'nm_produto': r['nm_produto']
            })
        return resultado
    
    def remove_apolice_cobertura(self, nr_apolice: str, cd_cobertura: int) -> bool:
        """Remove uma cobertura de uma apólice"""
        query = "DELETE FROM apolice_cobertura WHERE nr_apolice = ? AND cd_cobertura = ?"
        affected = self.db.execute_command(query, (nr_apolice, cd_cobertura))
        return affected > 0
    
    def remove_all_apolice_coberturas(self, nr_apolice: str) -> bool:
        """Remove todas as coberturas de uma apólice"""
        query = "DELETE FROM apolice_cobertura WHERE nr_apolice = ?"
        try:
            self.db.execute_command(query, (nr_apolice,))
            return True
        except Exception as e:
            logger.error(f"Erro ao remover coberturas da apólice {nr_apolice}: {e}")
            return False
    
    def insert_multiple_apolice_coberturas(self, nr_apolice: str, cd_produto: int, cd_coberturas: List[int], dt_inclusao: str = None) -> bool:
        """Insere múltiplas coberturas para uma apólice"""
        from .models import ApoliceCobertura
        from datetime import datetime
        
        if not cd_coberturas:
            return True  # Nada para inserir
            
        if dt_inclusao is None:
            dt_inclusao = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Remove coberturas existentes primeiro
            self.remove_all_apolice_coberturas(nr_apolice)
            
            # Insere as novas coberturas
            for cd_cobertura in cd_coberturas:
                apolice_cobertura = ApoliceCobertura(
                    cd_cobertura=cd_cobertura,
                    cd_produto=cd_produto,
                    nr_apolice=nr_apolice,
                    dt_inclusao=dt_inclusao,
                    created_at=datetime.now()
                )
                self.insert_apolice_cobertura(apolice_cobertura)
            
            logger.info(f"Inseridas {len(cd_coberturas)} coberturas para apólice {nr_apolice}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inserir coberturas para apólice {nr_apolice}: {e}")
            return False

    # ==================== OPERAÇÕES PARA NOTIFICAÇÕES ====================
    
    def insert_notificacao_risco(self, apolice_id: int, numero_apolice: str, segurado: str = None,
                                email: str = None, telefone: str = None, canal: str = 'sistema_alertas',
                                mensagem: str = '', score_risco: float = None, nivel_risco: str = None,
                                simulacao: bool = False, status: str = 'sucesso') -> int:
        """
        Insere uma nova notificação de risco
        
        Args:
            apolice_id: ID da apólice
            numero_apolice: Número da apólice
            segurado: Nome do segurado
            email: Email do segurado
            telefone: Telefone do segurado
            canal: Canal de notificação (email, sms, sistema_alertas, etc.)
            mensagem: Mensagem da notificação
            score_risco: Score de risco
            nivel_risco: Nível de risco
            simulacao: Se é uma simulação ou notificação real
            status: Status da notificação
            
        Returns:
            ID da notificação inserida
        """
        query = """
        INSERT INTO notificacoes_risco (
            apolice_id, numero_apolice, segurado, email, telefone, canal,
            mensagem, score_risco, nivel_risco, simulacao, status,
            data_envio, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
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
            simulacao,
            status
        )
        
        try:
            notificacao_id = self.db.execute_command(query, params)
            logger.info(f"Notificação inserida com ID {notificacao_id} para apólice {numero_apolice}")
            return notificacao_id
        except Exception as e:
            logger.error(f"Erro ao inserir notificação para apólice {numero_apolice}: {e}")
            raise
    
    def get_notificacoes_hoje(self) -> List[str]:
        """
        Retorna lista de números de apólices que já receberam notificação hoje
        
        Returns:
            Lista de números de apólices notificadas hoje
        """
        query = """
        SELECT DISTINCT numero_apolice 
        FROM notificacoes_risco 
        WHERE DATE(data_envio) = DATE('now')
        """
        
        try:
            results = self.db.execute_query(query)
            return [row[0] for row in results] if results else []
        except Exception as e:
            logger.error(f"Erro ao buscar notificações de hoje: {e}")
            return []
    
    def get_historico_notificacoes(self, numero_apolice: str = None, limite: int = 100) -> List[dict]:
        """
        Retorna histórico de notificações
        
        Args:
            numero_apolice: Filtrar por apólice específica (opcional)
            limite: Limite de registros a retornar
            
        Returns:
            Lista de notificações
        """
        query = """
        SELECT id, apolice_id, numero_apolice, segurado, email, telefone,
               canal, mensagem, score_risco, nivel_risco, simulacao, status,
               data_envio, created_at
        FROM notificacoes_risco
        """
        
        params = []
        
        if numero_apolice:
            query += " WHERE numero_apolice = ?"
            params.append(numero_apolice)
        
        query += " ORDER BY data_envio DESC LIMIT ?"
        params.append(limite)
        
        try:
            results = self.db.execute_query(query, tuple(params))
            
            notificacoes = []
            for row in results:
                notificacoes.append({
                    'id': row[0],
                    'apolice_id': row[1],
                    'numero_apolice': row[2],
                    'segurado': row[3],
                    'email': row[4],
                    'telefone': row[5],
                    'canal': row[6],
                    'mensagem': row[7],
                    'score_risco': row[8],
                    'nivel_risco': row[9],
                    'simulacao': bool(row[10]),
                    'status': row[11],
                    'data_envio': row[12],
                    'created_at': row[13]
                })
            
            return notificacoes
            
        except Exception as e:
            logger.error(f"Erro ao buscar histórico de notificações: {e}")
            return []

    def marcar_apolice_notificada(self, numero_apolice: str) -> bool:
        """
        Marca uma apólice como notificada (campo notificada = 1)
        
        Args:
            numero_apolice: Número da apólice a ser marcada
            
        Returns:
            True se a atualização foi bem-sucedida, False caso contrário
        """
        try:
            query = "UPDATE apolices SET notificada = 1 WHERE numero_apolice = ?"
            
            affected_rows = self.db.execute_command(query, (numero_apolice,))
            
            if affected_rows:
                logger.info(f"Apólice {numero_apolice} marcada como notificada")
                return True
            else:
                logger.warning(f"Nenhuma apólice encontrada com número {numero_apolice}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao marcar apólice {numero_apolice} como notificada: {e}")
            return False
