from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    env: str = "dev"
    database_url: str = "sqlite:///./humanai.db"
    cors_origins: str = "http://localhost:4200,http://127.0.0.1:4200"
    ranking_max_limit: int = 500
    cartas_path: str = "app/data/cartas_gabarito.json"
    docs_enabled: bool = True

    firebase_project_id: str = ""
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
    def producao(self) -> bool:
        return self.env.lower() == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
