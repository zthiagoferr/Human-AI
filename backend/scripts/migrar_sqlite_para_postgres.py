from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.config import normalizar_database_url, validar_database_url  # noqa: E402
from app.database import init_db  # noqa: E402

TABELAS = (
    "usuarios",
    "codigos_vinculo",
    "partidas",
    "partida_cartas",
    "respostas",
)

COLUNAS = {
    "usuarios": (
        "id",
        "nome",
        "nome_ordenacao",
        "usuario",
        "senha_hash",
        "criado_em",
        "firebase_uid",
    ),
    "codigos_vinculo": (
        "id",
        "usuario_id",
        "codigo_hash",
        "criado_em",
        "expira_em",
        "usado_em",
        "revogado_em",
        "criado_por_uid",
    ),
    "partidas": (
        "id",
        "usuario_id",
        "status",
        "total_perguntas",
        "iniciada_em",
        "concluida_em",
        "duracao_ms",
        "acertos",
        "erros",
    ),
    "partida_cartas": ("id", "partida_id", "carta_id", "posicao"),
    "respostas": ("id", "partida_id", "carta_id", "escolha", "correta", "respondida_em"),
}


def _erro(mensagem: str) -> None:
    print(f"ERRO: {mensagem}", file=sys.stderr)


def _url_destino() -> str:
    bruto = (os.getenv("DATABASE_URL") or "").strip()
    if not bruto:
        bruto = (os.getenv("HUMANAI_DATABASE_URL") or "").strip()
    url = normalizar_database_url(bruto)
    if not url:
        raise SystemExit(
            "ERRO: configure DATABASE_URL com a URL do PostgreSQL de destino."
        )
    if url.startswith("sqlite"):
        raise SystemExit(
            "ERRO: destino SQLite recusado. Use a URL PostgreSQL do Railway."
        )
    if not url.startswith("postgresql"):
        raise SystemExit("ERRO: o destino precisa ser PostgreSQL.")
    validar_database_url(url, True)
    return url


def _conectar_origem(caminho: Path) -> sqlite3.Connection:
    uri = f"file:{quote(str(caminho.resolve()))}?mode=ro"
    try:
        con = sqlite3.connect(uri, uri=True)
    except sqlite3.Error as exc:
        raise SystemExit(
            f"ERRO: não foi possível abrir {caminho.name} em modo somente leitura "
            f"({type(exc).__name__}). Se houver WAL, copie .db, -wal e -shm "
            "para um diretório temporário e use a cópia."
        ) from None
    con.row_factory = sqlite3.Row
    return con


def _tabela_existe(con: sqlite3.Connection, nome: str) -> bool:
    linha = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (nome,),
    ).fetchone()
    return linha is not None


def _view_existe(con: sqlite3.Connection, nome: str) -> bool:
    linha = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'view' AND name = ?",
        (nome,),
    ).fetchone()
    return linha is not None


def _colunas(con: sqlite3.Connection, tabela: str) -> set[str]:
    return {linha[1] for linha in con.execute(f"PRAGMA table_info({tabela})")}


def _contar(con: sqlite3.Connection, tabela: str) -> int:
    return int(con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0])


def _contar_condicao(con: sqlite3.Connection, sql: str) -> int:
    return int(con.execute(sql).fetchone()[0])


def _validar_origem(con: sqlite3.Connection) -> list[str]:
    erros: list[str] = []
    for tabela in TABELAS:
        if not _tabela_existe(con, tabela):
            erros.append(f"tabela ausente: {tabela}")
    if erros:
        return erros

    colunas_usuarios = _colunas(con, "usuarios")
    if "firebase_uid" not in colunas_usuarios:
        erros.append(
            "coluna usuarios.firebase_uid ausente; use uma cópia atualizada "
            "do banco após init_db ou migre a coluna antes da cópia"
        )

    checks = {
        "usuarios com campos longos": (
            "SELECT COUNT(*) FROM usuarios WHERE length(usuario) > 32 "
            "OR length(nome) > 80 OR length(nome_ordenacao) > 160 "
            "OR length(criado_em) > 40"
        ),
        "usuarios com handle duplicado (case-insensitive)": (
            "SELECT COUNT(*) FROM (SELECT lower(usuario) FROM usuarios "
            "GROUP BY lower(usuario) HAVING COUNT(*) > 1)"
        ),
        "partidas com status inválido": (
            "SELECT COUNT(*) FROM partidas WHERE status NOT IN "
            "('em_andamento', 'concluida', 'abandonada')"
        ),
        "partidas com total diferente de 22": (
            "SELECT COUNT(*) FROM partidas WHERE total_perguntas <> 22"
        ),
        "partidas com acertos/erros fora da faixa": (
            "SELECT COUNT(*) FROM partidas WHERE "
            "(acertos IS NOT NULL AND (acertos < 0 OR acertos > 22)) OR "
            "(erros IS NOT NULL AND (erros < 0 OR erros > 22))"
        ),
        "partidas com conclusão inconsistente": (
            "SELECT COUNT(*) FROM partidas WHERE "
            "(status = 'concluida' AND (concluida_em IS NULL OR duracao_ms IS NULL "
            "OR acertos IS NULL OR erros IS NULL OR acertos + erros <> total_perguntas)) "
            "OR (status <> 'concluida' AND (concluida_em IS NOT NULL OR duracao_ms IS NOT NULL "
            "OR acertos IS NOT NULL OR erros IS NOT NULL))"
        ),
        "partidas ativas duplicadas por usuário": (
            "SELECT COUNT(*) FROM (SELECT usuario_id FROM partidas "
            "WHERE status = 'em_andamento' GROUP BY usuario_id HAVING COUNT(*) > 1)"
        ),
        "partida_cartas com carta_id inválido": (
            "SELECT COUNT(*) FROM partida_cartas WHERE length(carta_id) <> 2"
        ),
        "partida_cartas duplicadas": (
            "SELECT COUNT(*) FROM (SELECT partida_id, carta_id FROM partida_cartas "
            "GROUP BY partida_id, carta_id HAVING COUNT(*) > 1)"
        ),
        "partida_cartas com posição duplicada": (
            "SELECT COUNT(*) FROM (SELECT partida_id, posicao FROM partida_cartas "
            "GROUP BY partida_id, posicao HAVING COUNT(*) > 1)"
        ),
        "respostas com escolha inválida": (
            "SELECT COUNT(*) FROM respostas WHERE escolha NOT IN ('humano', 'ia')"
        ),
        "respostas com correta inválida": (
            "SELECT COUNT(*) FROM respostas WHERE correta NOT IN (0, 1)"
        ),
        "respostas com carta_id inválido": (
            "SELECT COUNT(*) FROM respostas WHERE length(carta_id) <> 2"
        ),
        "respostas duplicadas": (
            "SELECT COUNT(*) FROM (SELECT partida_id, carta_id FROM respostas "
            "GROUP BY partida_id, carta_id HAVING COUNT(*) > 1)"
        ),
    }

    if "firebase_uid" in colunas_usuarios:
        checks["usuarios com firebase_uid duplicado"] = (
            "SELECT COUNT(*) FROM (SELECT firebase_uid FROM usuarios "
            "WHERE firebase_uid IS NOT NULL GROUP BY firebase_uid HAVING COUNT(*) > 1)"
        )
        checks["usuarios com firebase_uid longo"] = (
            "SELECT COUNT(*) FROM usuarios WHERE "
            "firebase_uid IS NOT NULL AND length(firebase_uid) > 128"
        )

    if _tabela_existe(con, "codigos_vinculo"):
        checks["códigos com hash inválido"] = (
            "SELECT COUNT(*) FROM codigos_vinculo WHERE length(codigo_hash) <> 64"
        )
        checks["códigos com hash duplicado"] = (
            "SELECT COUNT(*) FROM (SELECT codigo_hash FROM codigos_vinculo "
            "GROUP BY codigo_hash HAVING COUNT(*) > 1)"
        )

    for rotulo, sql in checks.items():
        try:
            total = _contar_condicao(con, sql)
        except sqlite3.Error as exc:
            erros.append(f"{rotulo}: falha ao validar ({type(exc).__name__})")
            continue
        if total:
            erros.append(f"{rotulo}: {total}")

    try:
        orfaos = con.execute("PRAGMA foreign_key_check").fetchall()
    except sqlite3.Error as exc:
        erros.append(f"foreign_key_check: falha ({type(exc).__name__})")
    else:
        if orfaos:
            erros.append(f"foreign_key_check: {len(orfaos)} referência(s) órfã(s)")

    return erros


def _contar_pg(engine: Engine, tabela: str) -> int:
    with engine.connect() as conn:
        return int(conn.execute(text(f"SELECT COUNT(*) FROM {tabela}")).scalar_one())


def _tabelas_pg(engine: Engine) -> set[str]:
    return set(inspect(engine).get_table_names())


def _contagens_pg(engine: Engine) -> dict[str, int]:
    return {tabela: _contar_pg(engine, tabela) for tabela in TABELAS}


def _verificar_destino_vazio(engine: Engine) -> None:
    existentes = _tabelas_pg(engine)
    if not existentes:
        return
    for tabela in TABELAS:
        if tabela in existentes and _contar_pg(engine, tabela) > 0:
            raise RuntimeError(
                f"Destino não vazio em {tabela}. Nenhuma alteração foi feita."
            )


def _copiar_usuarios(con: sqlite3.Connection) -> list[dict]:
    colunas = _colunas(con, "usuarios")
    if "firebase_uid" in colunas:
        select_sql = f"SELECT {', '.join(COLUNAS['usuarios'])} FROM usuarios ORDER BY id"
    else:
        base = ", ".join(
            coluna for coluna in COLUNAS["usuarios"] if coluna != "firebase_uid"
        )
        select_sql = f"SELECT {base}, NULL AS firebase_uid FROM usuarios ORDER BY id"
    return [dict(linha) for linha in con.execute(select_sql)]


def _copiar_tabela(con: sqlite3.Connection, tabela: str) -> list[dict]:
    colunas = ", ".join(COLUNAS[tabela])
    return [dict(linha) for linha in con.execute(f"SELECT {colunas} FROM {tabela} ORDER BY id")]


def _inserir(conn, tabela: str, linhas: list[dict], lote: int) -> None:
    if not linhas:
        return
    colunas = COLUNAS[tabela]
    sql = text(
        f"INSERT INTO {tabela} ({', '.join(colunas)}) "
        f"VALUES ({', '.join(':' + coluna for coluna in colunas)})"
    )
    for inicio in range(0, len(linhas), lote):
        conn.execute(sql, linhas[inicio : inicio + lote])


def _ajustar_sequences(conn) -> None:
    for tabela in TABELAS:
        sequencia = conn.execute(
            text("SELECT pg_get_serial_sequence(:tabela, 'id')"),
            {"tabela": tabela},
        ).scalar_one()
        if sequencia is None:
            raise RuntimeError(f"Sequência não encontrada para {tabela}.")
        conn.execute(
            text(
                "SELECT setval("
                "CAST(:sequencia AS regclass), "
                f"COALESCE((SELECT MAX(id) FROM {tabela}), 1), "
                f"(SELECT COUNT(*) FROM {tabela}) > 0"
                ")"
            ),
            {"sequencia": sequencia},
        )


def _executar_copia(origem: sqlite3.Connection, engine: Engine, lote: int) -> None:
    linhas_usuarios = _copiar_usuarios(origem)
    linhas_codigos = _copiar_tabela(origem, "codigos_vinculo")
    linhas_partidas = _copiar_tabela(origem, "partidas")
    linhas_partida_cartas = _copiar_tabela(origem, "partida_cartas")
    linhas_respostas = _copiar_tabela(origem, "respostas")

    with engine.begin() as conn:
        _verificar_destino_vazio(engine)
        _inserir(conn, "usuarios", linhas_usuarios, lote)
        _inserir(conn, "codigos_vinculo", linhas_codigos, lote)
        _inserir(conn, "partidas", linhas_partidas, lote)
        _inserir(conn, "partida_cartas", linhas_partida_cartas, lote)
        _inserir(conn, "respostas", linhas_respostas, lote)
        _ajustar_sequences(conn)

        origem_contagens = {tabela: _contar(origem, tabela) for tabela in TABELAS}
        destino_contagens = {
            tabela: int(
                conn.execute(text(f"SELECT COUNT(*) FROM {tabela}")).scalar_one()
            )
            for tabela in TABELAS
        }
        if origem_contagens != destino_contagens:
            raise RuntimeError(
                "Contagens divergiram após a cópia; transação será revertida."
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copia dados de um SQLite local para o PostgreSQL do Railway."
    )
    parser.add_argument("--source", default=str(BACKEND / "humanai.db"))
    parser.add_argument(
        "--executar",
        action="store_true",
        help="Executa a cópia. Sem esta flag, apenas valida (dry-run).",
    )
    parser.add_argument("--lote", type=int, default=1000)
    args = parser.parse_args()

    origem_path = Path(args.source)
    if not origem_path.exists():
        print(f"OK: nenhum banco local em {origem_path.name}; nada a migrar.")
        return 0

    url = _url_destino()
    engine = create_engine(url, pool_pre_ping=True)
    origem = _conectar_origem(origem_path)
    try:
        erros = _validar_origem(origem)
        if erros:
            _erro("pré-validação da origem falhou:")
            for item in erros:
                print(f"  - {item}", file=sys.stderr)
            return 1

        contagens = {tabela: _contar(origem, tabela) for tabela in TABELAS}
        print("Origem:", contagens)

        if not args.executar:
            existentes = _tabelas_pg(engine)
            if not existentes:
                print("Destino sem schema; --executar criará via init_db.")
            else:
                for tabela in TABELAS:
                    if tabela in existentes:
                        print(f"Destino {tabela}: {_contar_pg(engine, tabela)}")
            print("DRY-RUN: nenhuma escrita foi feita.")
            return 0

        _verificar_destino_vazio(engine)
        init_db(engine)
        _verificar_destino_vazio(engine)
        _executar_copia(origem, engine, args.lote)

        print("OK: cópia concluída; sequences ajustadas.")
        print("Destino:", _contagens_pg(engine))
        return 0
    except SQLAlchemyError as exc:
        _erro(
            f"falha de conexão/banco ({type(exc).__name__}); "
            "verifique DATABASE_URL e o PostgreSQL de destino"
        )
        return 1
    except (RuntimeError, SystemExit) as exc:
        _erro(str(exc))
        return 1
    finally:
        origem.close()
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
