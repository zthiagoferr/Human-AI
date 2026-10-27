from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.schema import CreateTable

from app.database import (
    INDEX_SQL_POSTGRES,
    INDEX_SQL_SQLITE,
    VIEW_SQL,
    VIEW_SQL_POSTGRES,
)
from app.models import Usuario


def test_modelo_nao_usa_nocase_no_postgresql():
    sql = str(CreateTable(Usuario.__table__).compile(dialect=postgresql.dialect()))
    assert "NOCASE" not in sql


def test_modelo_mantem_nocase_no_sqlite():
    sql = str(CreateTable(Usuario.__table__).compile(dialect=sqlite.dialect()))
    assert "NOCASE" in sql


def test_indice_de_usuario_por_dialeto():
    assert "lower(usuario)" in INDEX_SQL_POSTGRES[0]
    assert "COLLATE NOCASE" in INDEX_SQL_SQLITE[0]


def test_view_ranking_e_portavel():
    assert "ROW_NUMBER() OVER" in VIEW_SQL
    assert "CREATE VIEW" in VIEW_SQL
    assert "CREATE OR REPLACE VIEW" in VIEW_SQL_POSTGRES
    assert "NOCASE" not in VIEW_SQL
