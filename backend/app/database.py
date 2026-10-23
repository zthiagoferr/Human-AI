from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings
from app.migrations import aplicar_migracoes


class Base(DeclarativeBase):
    pass


def _configurar_sqlite(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _pragmas(dbapi_connection, _connection_record):  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA busy_timeout = 5000")
        cursor.close()


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)
_configurar_sqlite(engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


INDEX_SQL = (
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_usuario "
    "ON usuarios(usuario COLLATE NOCASE)",
    "CREATE INDEX IF NOT EXISTS ix_usuarios_nome_ordenacao ON usuarios(nome_ordenacao)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_firebase_uid "
    "ON usuarios(firebase_uid) WHERE firebase_uid IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_codigos_vinculo_usuario "
    "ON codigos_vinculo(usuario_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_codigos_vinculo_hash "
    "ON codigos_vinculo(codigo_hash)",
    "CREATE INDEX IF NOT EXISTS ix_codigos_vinculo_expira "
    "ON codigos_vinculo(expira_em)",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_partidas_ativa "
    "ON partidas(usuario_id) WHERE status = 'em_andamento'",
    "CREATE INDEX IF NOT EXISTS ix_partidas_usuario ON partidas(usuario_id)",
    "CREATE INDEX IF NOT EXISTS ix_partidas_concluidas "
    "ON partidas(usuario_id, acertos DESC, duracao_ms ASC, concluida_em ASC) "
    "WHERE status = 'concluida'",
    "CREATE INDEX IF NOT EXISTS ix_partida_cartas_partida "
    "ON partida_cartas(partida_id, posicao)",
    "CREATE INDEX IF NOT EXISTS ix_respostas_partida ON respostas(partida_id)",
)

VIEW_SQL = """
CREATE VIEW vw_ranking AS
WITH melhores AS (
    SELECT
        p.id AS partida_id,
        p.usuario_id,
        p.acertos,
        p.erros,
        p.duracao_ms,
        p.concluida_em,
        ROW_NUMBER() OVER (
            PARTITION BY p.usuario_id
            ORDER BY p.acertos DESC, p.duracao_ms ASC, p.concluida_em ASC, p.id ASC
        ) AS rn
    FROM partidas p
    WHERE p.status = 'concluida'
)
SELECT
    ROW_NUMBER() OVER (
        ORDER BY m.acertos DESC, m.duracao_ms ASC, u.nome_ordenacao ASC, u.id ASC
    ) AS posicao,
    u.id AS usuario_id,
    u.nome AS nome,
    m.partida_id AS partida_id,
    m.acertos AS acertos,
    m.erros AS erros,
    m.duracao_ms AS duracao_ms,
    m.concluida_em AS concluida_em
FROM melhores m
JOIN usuarios u ON u.id = m.usuario_id
WHERE m.rn = 1
"""


def init_db(target_engine: Engine | None = None) -> None:
    from app import models  # noqa: F401  (registra as tabelas no metadata)

    db_engine = target_engine or engine
    Base.metadata.create_all(bind=db_engine)
    aplicar_migracoes(db_engine)
    with db_engine.begin() as connection:
        for statement in INDEX_SQL:
            connection.exec_driver_sql(statement)
        connection.exec_driver_sql("DROP VIEW IF EXISTS vw_ranking")
        connection.exec_driver_sql(VIEW_SQL)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
