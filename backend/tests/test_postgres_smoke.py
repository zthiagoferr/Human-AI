import os
import uuid

import pytest
from sqlalchemy import create_engine, text

from app.database import init_db

URL_POSTGRES = os.getenv("HUMANAI_TEST_POSTGRES_URL")

pytestmark = pytest.mark.skipif(
    not URL_POSTGRES,
    reason="defina HUMANAI_TEST_POSTGRES_URL para testar PostgreSQL real",
)


def test_init_db_e_ranking_em_postgresql():
    """Teste destrutivo apenas em um schema temporário isolado."""
    schema = f"humanai_test_{uuid.uuid4().hex[:12]}"
    admin = create_engine(URL_POSTGRES, pool_pre_ping=True)
    engine = create_engine(
        URL_POSTGRES,
        pool_pre_ping=True,
        connect_args={"options": f"-csearch_path={schema}"},
    )

    with admin.begin() as conn:
        conn.exec_driver_sql(f'CREATE SCHEMA "{schema}"')

    try:
        init_db(engine)
        init_db(engine)

        with engine.begin() as conn:
            usuario_id = conn.execute(
                text(
                    "INSERT INTO usuarios "
                    "(nome, nome_ordenacao, usuario, senha_hash, criado_em, firebase_uid) "
                    "VALUES ('Teste PG', 'teste pg', 'teste.pg', '!firebase', "
                    "'2026-01-01T00:00:00+00:00', NULL) RETURNING id"
                )
            ).scalar_one()
            conn.execute(
                text(
                    "INSERT INTO partidas "
                    "(usuario_id, status, total_perguntas, iniciada_em, concluida_em, "
                    "duracao_ms, acertos, erros) "
                    "VALUES (:usuario_id, 'concluida', 22, "
                    "'2026-01-02T10:00:00+00:00', '2026-01-02T10:01:00+00:00', "
                    "60000, 10, 12)"
                ),
                {"usuario_id": usuario_id},
            )
            ranking = conn.execute(
                text("SELECT COUNT(*) FROM vw_ranking")
            ).scalar_one()
            indice = conn.execute(
                text(
                    "SELECT indexdef FROM pg_indexes "
                    "WHERE schemaname = current_schema() "
                    "AND indexname = 'ux_usuarios_usuario'"
                )
            ).scalar_one()

        assert int(ranking) == 1
        assert "lower(usuario)" in indice.lower()
    finally:
        engine.dispose()
        with admin.begin() as conn:
            conn.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        admin.dispose()
