from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import text

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.database import engine, init_db  # noqa: E402


def _tabela_existe(conn, nome: str) -> bool:
    linha = conn.execute(
        text(
            "SELECT name FROM sqlite_master "
            "WHERE type IN ('table', 'view') AND name = :nome"
        ),
        {"nome": nome},
    ).first()
    return linha is not None


def _contagens() -> dict[str, int]:
    with engine.connect() as conn:
        dados: dict[str, int] = {}
        for tabela in ("usuarios", "partidas", "partida_cartas", "respostas"):
            if _tabela_existe(conn, tabela):
                dados[tabela] = int(
                    conn.execute(text(f"SELECT COUNT(*) FROM {tabela}")).scalar_one()
                )
            else:
                dados[tabela] = 0
        if _tabela_existe(conn, "vw_ranking"):
            dados["ranking"] = int(
                conn.execute(text("SELECT COUNT(*) FROM vw_ranking")).scalar_one()
            )
        else:
            dados["ranking"] = 0
        return dados


def main() -> int:
    if engine.dialect.name != "sqlite":
        print(
            "Este script é específico de SQLite. "
            "Em PostgreSQL, use scripts/migrar_sqlite_para_postgres.py.",
            file=sys.stderr,
        )
        return 2

    antes = _contagens()
    print("Antes:", antes)

    init_db(engine)

    depois = _contagens()
    print("Depois:", depois)

    tabelas_dados = ("usuarios", "partidas", "partida_cartas", "respostas")
    if any(antes[t] != depois[t] for t in tabelas_dados):
        print("ERRO: contagens divergiram; migração abortada para análise.", file=sys.stderr)
        return 1

    with engine.connect() as conn:
        colunas = {
            linha[1] for linha in conn.execute(text("PRAGMA table_info(usuarios)")).fetchall()
        }
        if "firebase_uid" not in colunas:
            print("ERRO: coluna firebase_uid ausente.", file=sys.stderr)
            return 1
        pendentes = int(
            conn.execute(
                text("SELECT COUNT(*) FROM usuarios WHERE firebase_uid IS NULL")
            ).scalar_one()
        )
        indice = conn.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type = 'index' "
                "AND name = 'ux_usuarios_firebase_uid'"
            )
        ).first()

    print(f"OK: {pendentes} usuário(s) preservados sem vínculo Firebase.")
    if indice is None:
        print("ERRO: índice ux_usuarios_firebase_uid ausente.", file=sys.stderr)
        return 1
    print("OK: migração idempotente concluída.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
