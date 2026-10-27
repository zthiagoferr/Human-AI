import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DIR = Path(tempfile.mkdtemp(prefix="humanai-test-"))
os.environ.pop("DATABASE_URL", None)
os.environ["HUMANAI_ENV"] = "test"
os.environ["HUMANAI_DATABASE_URL"] = f"sqlite:///{TEST_DIR / 'test.db'}"
os.environ["HUMANAI_CARTAS_PATH"] = "app/data/cartas_gabarito.json"
os.environ["HUMANAI_FIREBASE_PROJECT_ID"] = "humanai-test"
os.environ["HUMANAI_PROFESSOR_EMAILS"] = "professor@example.com"
os.environ["HUMANAI_VINCULO_TTL_HOURS"] = "24"

from app.database import Base, SessionLocal, engine, init_db  # noqa: E402
from app.firebase_auth import get_verificador  # noqa: E402
from app.main import app  # noqa: E402
from app.models import SENHA_HASH_INERTE, Usuario  # noqa: E402
from tests.fakes import VerificadorFake  # noqa: E402


@pytest.fixture()
def client():
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP VIEW IF EXISTS vw_ranking")
    Base.metadata.drop_all(bind=engine)
    init_db(engine)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def firebase():
    fake = VerificadorFake()
    app.dependency_overrides[get_verificador] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_verificador, None)


def criar_usuario(
    db,
    nome: str = "Aluno Teste",
    usuario: str = "aluno.teste",
    senha: str = "Senha1234",
    firebase_uid: str | None = None,
) -> Usuario:
    from app.domain.normalizacao import normalizar_nome

    user = Usuario(
        nome=nome,
        nome_ordenacao=normalizar_nome(nome),
        usuario=usuario,
        senha_hash=SENHA_HASH_INERTE,
        criado_em="2026-01-01T00:00:00+00:00",
        firebase_uid=firebase_uid,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
