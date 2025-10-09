#!/usr/bin/env python3
"""CLI para gerenciamento de bloqueios por prefixo de CEP.

Uso:
  python scripts/manage_blocks.py add --prefix 01234 --reason "Alto risco hídrico" --severity 2 --scope residencial --user admin
  python scripts/manage_blocks.py list --active-only
  python scripts/manage_blocks.py unblock --prefix 01234 --user admin
  python scripts/manage_blocks.py deactivate --prefix 01234 --user admin
  python scripts/manage_blocks.py remove --prefix 01234 --user admin --hard

Observações:
- Prefixo deve ser somente dígitos (3 a 8). Recomendado 5.
- 'unblock' mantém o registro ativo mas libera emissão (blocked=0).
- 'deactivate' desativa completamente a regra (active=0 e blocked=0).
- 'remove' exclui do banco se usar --hard; caso contrário faz soft delete.
"""

import argparse
import sys
from typing import Optional

# Garantir path
sys.path.append('.')

from database import get_database, CRUDOperations  # type: ignore


def parse_args():
    parser = argparse.ArgumentParser(description="Gerenciamento de bloqueios por CEP prefixo")
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = sub.add_parser("add", help="Adicionar ou atualizar bloqueio")
    p_add.add_argument("--prefix", required=True, help="Prefixo de CEP (3-8 dígitos)")
    p_add.add_argument("--reason", required=True, help="Motivo do bloqueio")
    p_add.add_argument("--severity", type=int, default=1, choices=[1, 2, 3], help="Severidade (1=normal,2=alto,3=critico)")
    p_add.add_argument("--scope", default="residencial", help="Escopo (ex.: residencial, global)")
    p_add.add_argument("--user", default="cli", help="Usuário responsável")

    # list
    p_list = sub.add_parser("list", help="Listar bloqueios")
    p_list.add_argument("--active-only", action="store_true", help="Mostrar apenas ativos")
    p_list.add_argument("--scope", default=None, help="Filtrar por escopo")

    # unblock
    p_unblock = sub.add_parser("unblock", help="Liberar emissão mantendo registro")
    p_unblock.add_argument("--prefix", required=True)
    p_unblock.add_argument("--user", default="cli")
    p_unblock.add_argument("--reason", default=None, help="Motivo opcional da mudança")

    # deactivate
    p_deactivate = sub.add_parser("deactivate", help="Desativar bloqueio (active=0 e blocked=0)")
    p_deactivate.add_argument("--prefix", required=True)
    p_deactivate.add_argument("--user", default="cli")

    # remove
    p_remove = sub.add_parser("remove", help="Remover bloqueio (soft ou hard)")
    p_remove.add_argument("--prefix", required=True)
    p_remove.add_argument("--user", default="cli")
    p_remove.add_argument("--hard", action="store_true", help="Hard delete definitivo")

    return parser.parse_args()


def main():
    args = parse_args()
    db = get_database()
    crud = CRUDOperations(db)

    if args.command == "add":
        block_id = crud.create_block(
            cep_prefix=args.prefix,
            reason=args.reason,
            severity=args.severity,
            scope=args.scope,
            created_by=args.user
        )
        print(f"[OK] Bloqueio ativo para prefixo {args.prefix} (ID {block_id})")

    elif args.command == "list":
        blocks = crud.list_blocks(active_only=args.active_only, scope=args.scope)
        if not blocks:
            print("(vazio)")
            return
        for b in blocks:
            status = "BLOCKED" if b.blocked and b.active else "FREE"
            print(f"{b.cep_prefix} | {status} | severity={b.severity} | scope={b.scope} | reason={b.reason}")

    elif args.command == "unblock":
        crud.set_block_status(args.prefix, blocked=False, reason=args.reason, updated_by=args.user)
        print(f"[OK] Prefixo {args.prefix} liberado (registro permanece ativo)")

    elif args.command == "deactivate":
        crud.remove_block(args.prefix, updated_by=args.user, hard_delete=False)
        print(f"[OK] Prefixo {args.prefix} desativado (soft)")

    elif args.command == "remove":
        crud.remove_block(args.prefix, updated_by=args.user, hard_delete=args.hard)
        mode = "hard" if args.hard else "soft"
        print(f"[OK] Remoção {mode} executada para prefixo {args.prefix}")

    else:
        print("Comando não reconhecido")


if __name__ == "__main__":
    main()
