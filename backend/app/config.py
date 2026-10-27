import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


def normalizar_database_url(valor: str) -> str:
    """Normaliza a URL do banco para o driver psycopg 3."""
    url = (valor or "").strip()
    if not url:
        return url

    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    elif url.startswith("postgresql+psycopg2://"):
        url = "postgresql+psycopg://" + url[len("postgresql+psycopg2://") :]

    partes = urlsplit(url)
    if partes.scheme != "postgresql+psycopg":
        return url

    query = parse_qsl(partes.query, keep_blank_values=True)
    tem_sslmode = any(chave == "sslmode" for chave, _ in query)
    nova_query: list[tuple[str, str]] = []
    for chave, valor_query in query:
        if chave == "ssl":
            if not tem_sslmode and valor_query.lower() in {"require", "true", "1"}:
                nova_query.append(("sslmode", "require"))
            continue
        nova_query.append((chave, valor_query))

    return urlunsplit(
        (partes.scheme, partes.netloc, partes.path, urlencode(nova_query), partes.fragment)
    )


def validar_database_url(url: str, producao: bool) -> None:
    """Impede SQLite persistente em produção."""
    if producao and not url.startswith("postgresql"):
        raise RuntimeError(
            "HUMANAI_ENV=production exige PostgreSQL em DATABASE_URL. "
            "SQLite não é persistente no Railway."
        )


class Settings(BaseSettings):
    env: str = "dev"
    database_url: str = "sqlite:///./humanai.db"
    cors_origins: str = "http://localhost:4200,http://127.0.0.1:4200"
    ranking_max_limit: int = 500
    cartas_path: str = "app/data/cartas_gabarito.json"
    docs_enabled: bool = True

    firebase_project_id: str = ""
    firebase_credentials_json: str = ""
    professor_emails: str = ""
    firebase_check_revoked: bool = False
    vinculo_ttl_hours: int = 24

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="HUMANAI_",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origem.strip() for origem in self.cors_origins.split(",") if origem.strip()]

    @property
    def professor_emails_list(self) -> list[str]:
        return [
            email.strip().casefold()
            for email in self.professor_emails.split(",")
            if email.strip()
        ]

    @property
    def cartas_arquivo(self) -> Path:
        caminho = Path(self.cartas_path)
        if caminho.is_absolute():
            return caminho
        return BASE_DIR / caminho

    @property
    def database_url_efetiva(self) -> str:
        railway_url = (os.getenv("DATABASE_URL") or "").strip()
        bruto = railway_url or self.database_url
        return normalizar_database_url(bruto)

    @property
    def producao(self) -> bool:
        return self.env.strip().lower() in {"prod", "production"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
