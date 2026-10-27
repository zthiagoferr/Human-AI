import pytest

from app.config import (
    Settings,
    normalizar_database_url,
    validar_database_url,
)


def test_normaliza_postgres_para_psycopg():
    assert normalizar_database_url("postgres://u:p@h:5432/db") == (
        "postgresql+psycopg://u:p@h:5432/db"
    )
    assert normalizar_database_url("postgresql://u:p@h:5432/db") == (
        "postgresql+psycopg://u:p@h:5432/db"
    )
    assert normalizar_database_url("postgresql+psycopg2://u:p@h/db") == (
        "postgresql+psycopg://u:p@h/db"
    )


def test_converte_ssl_require_para_sslmode():
    url = normalizar_database_url(
        "postgresql://u:p@h:5432/db?ssl=require&channel_binding=require"
    )
    assert "sslmode=require" in url
    assert "ssl=require" not in url
    assert "channel_binding=require" in url


def test_preserva_sslmode_existente():
    url = normalizar_database_url(
        "postgresql://u:p@h/db?ssl=require&sslmode=verify-full"
    )
    assert "sslmode=verify-full" in url
    assert "ssl=require" not in url


def test_database_url_do_railway_tem_precedencia(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgres://u:p@h:5432/db?ssl=require"
    )
    settings = Settings(_env_file=None, database_url="sqlite:///./local.db")
    assert settings.database_url_efetiva == (
        "postgresql+psycopg://u:p@h:5432/db?sslmode=require"
    )


def test_producao_aceita_prod_e_production():
    assert Settings(_env_file=None, env="prod").producao is True
    assert Settings(_env_file=None, env="production").producao is True
    assert Settings(_env_file=None, env="dev").producao is False


def test_producao_recusa_sqlite():
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        validar_database_url("sqlite:///./humanai.db", True)
    validar_database_url("postgresql+psycopg://u:p@h/db", True)


def test_cors_lista_com_espacos():
    settings = Settings(
        _env_file=None,
        cors_origins=" https://a.example , http://localhost:4200 ",
    )
    assert settings.cors_origins_list == [
        "https://a.example",
        "http://localhost:4200",
    ]
