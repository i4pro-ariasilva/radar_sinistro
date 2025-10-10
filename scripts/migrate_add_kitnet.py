"""Migração para adicionar suporte a 'kitnet' em tipo_residencia.

SQLite não permite alterar/remover diretamente uma CHECK constraint existente.
Portanto, a estratégia é:
 1. Verificar se a definição atual da tabela 'apolices' já contém 'kitnet'.
 2. Se NÃO contém, recriar a tabela com a nova constraint incluindo 'kitnet'.
 3. Copiar os dados, recriar índices e views.
 4. Preservar backup da tabela antiga (apolices_old) até o final; opção de limpar.

Uso:
  python scripts/migrate_add_kitnet.py --db database/radar_sinistro.db
  python scripts/migrate_add_kitnet.py --db database/radar_sinistro.db --apply
  (Por padrão já aplica; --dry-run apenas simula.)

Argumentos:
  --db <path>      Caminho do arquivo .db (default: database/radar_sinistro.db)
  --dry-run        Não executa alterações, só informa o que faria.
  --force          Força recriação mesmo que já exista 'kitnet' no schema.
  --cleanup-old    Após sucesso, remove a tabela apolices_old.

Saídas de log no console para acompanhamento.
"""
from __future__ import annotations
import argparse
import os
import shutil
import sqlite3
import datetime as dt
import sys
from textwrap import dedent

NEW_TABLE_SQL = dedent(
    """
    CREATE TABLE apolices_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_apolice VARCHAR(50) UNIQUE NOT NULL,
        segurado VARCHAR(100) NOT NULL,
        email TEXT,
        telefone TEXT,
        cep VARCHAR(9) NOT NULL,
        latitude REAL,
        longitude REAL,
        tipo_residencia VARCHAR(20) NOT NULL CHECK(tipo_residencia IN ('casa','apartamento','sobrado','kitnet')),
        valor_segurado DECIMAL(12,2) NOT NULL CHECK(valor_segurado > 0),
        data_contratacao DATE NOT NULL,
        data_inicio DATE,
        score_risco DECIMAL(5,2),
        nivel_risco VARCHAR(10) CHECK(nivel_risco IN ('baixo','medio','alto','critico')),
        probabilidade_sinistro DECIMAL(5,2),
        ativa BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
)

INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_apolices_cep ON apolices(cep);",
    "CREATE INDEX IF NOT EXISTS idx_apolices_coords ON apolices(latitude, longitude);",
    "CREATE INDEX IF NOT EXISTS idx_apolices_ativa ON apolices(ativa);",
    "CREATE INDEX IF NOT EXISTS idx_apolices_score ON apolices(score_risco);",
]

VIEWS_SQL = [
    dedent(
        """
        CREATE VIEW IF NOT EXISTS vw_apolices_ativas AS
        SELECT 
            a.*,
            COUNT(s.id) as total_sinistros,
            COALESCE(SUM(s.valor_prejuizo), 0) as valor_total_sinistros
        FROM apolices a
        LEFT JOIN sinistros_historicos s ON a.id = s.apolice_id
        WHERE a.ativa = 1
        GROUP BY a.id;
        """
    ),
    dedent(
        """
        CREATE VIEW IF NOT EXISTS vw_previsoes_recentes AS
        SELECT 
            p.*,
            a.numero_apolice,
            a.cep,
            a.tipo_residencia,
            a.valor_segurado
        FROM previsoes_risco p
        JOIN apolices a ON p.apolice_id = a.id
        WHERE p.data_previsao >= datetime('now', '-1 day')
        ORDER BY p.score_risco DESC;
        """
    ),
]

COPY_SQL = dedent(
    """
    INSERT INTO apolices_new
    (id, numero_apolice, segurado, email, telefone, cep, latitude, longitude,
     tipo_residencia, valor_segurado, data_contratacao, data_inicio, score_risco,
     nivel_risco, probabilidade_sinistro, ativa, created_at, updated_at)
    SELECT 
     id, numero_apolice, segurado, email, telefone, cep, latitude, longitude,
     tipo_residencia, valor_segurado, data_contratacao, data_inicio, score_risco,
     nivel_risco, probabilidade_sinistro, ativa, created_at, updated_at
    FROM apolices;
    """
)

DROP_VIEWS = [
    "DROP VIEW IF EXISTS vw_apolices_ativas;",
    "DROP VIEW IF EXISTS vw_previsoes_recentes;",
]


def detect_has_kitnet_schema(conn: sqlite3.Connection) -> bool:
    cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='apolices';")
    row = cur.fetchone()
    if not row or not row[0]:
        return False
    return "kitnet" in row[0].lower()


def backup_database(db_path: str) -> str:
    timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{db_path}.bak_{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"[OK] Backup criado: {backup_path}")
    return backup_path


def migrate(db_path: str, dry_run: bool, force: bool, cleanup_old: bool):
    if not os.path.exists(db_path):
        print(f"[ERRO] Banco não encontrado: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    try:
        has_kitnet = detect_has_kitnet_schema(conn)
        if has_kitnet and not force:
            print("[INFO] A tabela 'apolices' já suporta 'kitnet'. Nada a fazer.")
            return
        print(f"[INFO] Suporte atual a 'kitnet': {'SIM' if has_kitnet else 'NÃO'}")
        if dry_run:
            print("[DRY-RUN] Recriação seria executada." + (" (forçada)" if force else ""))
            return

        backup_database(db_path)
        print("[INFO] Iniciando transação de migração...")
        conn.execute("PRAGMA foreign_keys=OFF;")
        conn.execute("BEGIN TRANSACTION;")

        for sql in DROP_VIEWS:
            conn.execute(sql)
        conn.execute(NEW_TABLE_SQL)
        conn.execute(COPY_SQL)

        # Renomear tabelas
        conn.execute("ALTER TABLE apolices RENAME TO apolices_old;")
        conn.execute("ALTER TABLE apolices_new RENAME TO apolices;")

        # Índices
        for sql in INDEXES_SQL:
            conn.execute(sql)
        # Views
        for sql in VIEWS_SQL:
            conn.execute(sql)

        conn.execute("COMMIT;")
        conn.execute("PRAGMA foreign_keys=ON;")
        print("[OK] Migração concluída com sucesso.")

        if cleanup_old:
            try:
                conn.execute("DROP TABLE IF EXISTS apolices_old;")
                print("[OK] Tabela antiga removida (apolices_old).")
            except Exception as e:
                print(f"[WARN] Falha ao remover apolices_old: {e}")

        # Validação rápida
        cur = conn.execute("SELECT COUNT(*) FROM apolices;")
        total = cur.fetchone()[0]
        print(f"[INFO] Registros preservados: {total}")

    except Exception as e:
        print(f"[ERRO] Falha na migração: {e}")
        try:
            conn.execute("ROLLBACK;")
        except Exception:
            pass
        sys.exit(2)
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Migração para incluir 'kitnet' na constraint de tipo_residencia")
    parser.add_argument('--db', default='database/radar_sinistro.db', help='Caminho do banco SQLite')
    parser.add_argument('--dry-run', action='store_true', help='Simula sem aplicar mudanças')
    parser.add_argument('--force', action='store_true', help='Força recriação mesmo que já tenha kitnet')
    parser.add_argument('--cleanup-old', action='store_true', help='Remove tabela apolices_old após sucesso')
    args = parser.parse_args()

    migrate(args.db, args.dry_run, args.force, args.cleanup_old)

if __name__ == '__main__':
    main()
