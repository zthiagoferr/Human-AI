from pathlib import Path

from sqlalchemy import create_engine, text

from app.database import init_db

USUARIOS_ANTIGOS = (
    """
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    nome_ordenacao TEXT NOT NULL,
    usuario TEXT NOT NULL COLLATE NOCASE,
    senha_hash TEXT NOT NULL,
    criado_em TEXT NOT NULL
)
""",
    "CREATE UNIQUE INDEX ux_usuarios_usuario ON usuarios(usuario COLLATE NOCASE)",
    "CREATE INDEX ix_usuarios_nome_ordenacao ON usuarios(nome_ordenacao)",
)

PARTIDAS_ANTIGAS = (
    """
CREATE TABLE partidas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    total_perguntas INTEGER NOT NULL,
    iniciada_em TEXT NOT NULL,
    concluida_em TEXT,
    duracao_ms INTEGER,
    acertos INTEGER,
    erros INTEGER
)
""",
    "CREATE UNIQUE INDEX ux_partidas_ativa "
    "ON partidas(usuario_id) WHERE status = 'em_andamento'",
    "CREATE INDEX ix_partidas_usuario ON partidas(usuario_id)",
)


def _contar(engine, tabela: str) -> int:
    with engine.connect() as conn:
        return int(conn.execute(text(f"SELECT COUNT(*) FROM {tabela}")).scalar_one())


def test_migracao_preserva_dados_e_e_idempotente(tmp_path: Path):
    arquivo = tmp_path / "antigo.db"
    engine = create_engine(f"sqlite:///{arquivo}")
    with engine.begin() as conn:
        for statement in USUARIOS_ANTIGOS:
            conn.exec_driver_sql(statement)
        for statement in PARTIDAS_ANTIGAS:
            conn.exec_driver_sql(statement)
        conn.exec_driver_sql(
            "INSERT INTO usuarios (nome, nome_ordenacao, usuario, senha_hash, criado_em) "
            "VALUES ('Ana Lima', 'ana lima', 'ana.lima', '$argon2id$legado', "
            "'2026-01-01T00:00:00+00:00')"
        )
        conn.exec_driver_sql(
            "INSERT INTO partidas "
            "(usuario_id, status, total_perguntas, iniciada_em, concluida_em, "
            "duracao_ms, acertos, erros) VALUES "
            "(1, 'concluida', 22, '2026-01-02T10:00:00+00:00', "
            "'2026-01-02T10:30:00+00:00', 1800000, 18, 4)"
        )

    antes = {
        "usuarios": _contar(engine, "usuarios"),
        "partidas": _contar(engine, "partidas"),
    }

    init_db(engine)
    init_db(engine)

    assert _contar(engine, "usuarios") == antes["usuarios"]
    assert _contar(engine, "partidas") == antes["partidas"]

    with engine.connect() as conn:
        colunas = {
            linha[1] for linha in conn.execute(text("PRAGMA table_info(usuarios)")).fetchall()
        }
        assert "firebase_uid" in colunas

        usuario = conn.execute(
            text(
                "SELECT nome, usuario, senha_hash, criado_em, firebase_uid "
                "FROM usuarios WHERE id = 1"
            )
        ).mappings().one()
        assert usuario["nome"] == "Ana Lima"
        assert usuario["usuario"] == "ana.lima"
        assert usuario["senha_hash"] == "$argon2id$legado"
        assert usuario["criado_em"] == "2026-01-01T00:00:00+00:00"
        assert usuario["firebase_uid"] is None

        partida = conn.execute(
            text(
                "SELECT acertos, erros, duracao_ms, concluida_em "
                "FROM partidas WHERE id = 1"
            )
        ).mappings().one()
        assert partida["acertos"] == 18
        assert partida["erros"] == 4
        assert partida["duracao_ms"] == 1800000

        ranking = conn.execute(text("SELECT COUNT(*) FROM vw_ranking")).scalar_one()
        assert int(ranking) == 1

        indice = conn.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type = 'index' "
                "AND name = 'ux_usuarios_firebase_uid'"
            )
        ).first()
        assert indice is not None


def test_indice_permite_varios_nulos(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'nulos.db'}")
    init_db(engine)
    with engine.begin() as conn:
        for indice in range(2):
            conn.exec_driver_sql(
                "INSERT INTO usuarios (nome, nome_ordenacao, usuario, senha_hash, criado_em) "
                f"VALUES ('Aluno {indice}', 'aluno {indice}', 'aluno{indice}', '!firebase', "
                "'2026-01-01T00:00:00+00:00')"
            )
        total = conn.exec_driver_sql(
            "SELECT COUNT(*) FROM usuarios WHERE firebase_uid IS NULL"
        ).scalar_one()
    assert int(total) == 2
