from sqlalchemy import select

from app.models import Usuario
from tests.fakes import headers_para


def test_rotas_legadas_retornam_410(client):
    for rota in ("/api/auth/registro", "/api/auth/login", "/api/auth/logout"):
        resposta = client.post(rota, json={"usuario": "x", "senha": "y"})
        assert resposta.status_code == 410, rota
        assert resposta.json()["erro"]["codigo"] == "AUTENTICACAO_MIGRADA"


def test_sessao_auto_provisiona_e_e_idempotente(client, firebase, db):
    headers = headers_para(
        firebase, "uid-ana", email="ana@example.com", nome="Ana Lima"
    )

    primeira = client.post("/api/auth/sessao", headers=headers, json={"nome": "Ana Lima"})
    assert primeira.status_code == 200, primeira.text
    dados = primeira.json()
    assert dados["usuario"]["nome"] == "Ana Lima"
    assert dados["usuario"]["usuario"] == "ana"
    assert dados["papel"] == "aluno"

    usuario = db.scalar(select(Usuario).where(Usuario.firebase_uid == "uid-ana"))
    assert usuario is not None
    assert usuario.senha_hash == "!firebase"

    segunda = client.get("/api/auth/me", headers=headers)
    assert segunda.status_code == 200
    assert segunda.json()["usuario"]["id"] == dados["usuario"]["id"]
    assert db.scalar(select(Usuario).where(Usuario.firebase_uid == "uid-ana")).id == usuario.id


def test_email_igual_nao_vincula_conta_legada(client, firebase, db):
    legado = db.scalar(select(Usuario).where(Usuario.usuario == "aluno.teste"))
    if legado is None:
        from tests.conftest import criar_usuario

        legado = criar_usuario(db, usuario="aluno.teste")

    headers = headers_para(
        firebase, "uid-novo", email="aluno.teste@example.com", nome="Outro Nome"
    )
    resposta = client.get("/api/auth/me", headers=headers)
    assert resposta.status_code == 200

    db.refresh(legado)
    assert legado.firebase_uid is None
    novo = db.scalar(select(Usuario).where(Usuario.firebase_uid == "uid-novo"))
    assert novo is not None
    assert novo.id != legado.id
    assert novo.usuario != legado.usuario


def test_username_colisao_recebe_sufixo(client, firebase, db):
    from tests.conftest import criar_usuario

    criar_usuario(db, nome="Maria Souza", usuario="maria.souza")
    headers = headers_para(
        firebase, "uid-maria", email="maria.souza@example.com", nome="Maria Souza"
    )
    resposta = client.get("/api/auth/me", headers=headers)
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["usuario"]["usuario"] == "maria.souza-2"


def test_nome_invalido_usa_fallback_do_email(client, firebase):
    headers = headers_para(
        firebase,
        "uid-joao",
        email="joao.silva@example.com",
        nome="Joao 123",
    )
    resposta = client.get("/api/auth/me", headers=headers)
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["usuario"]["nome"] == "joao.silva"


def test_sessao_valida_nome_informado(client, firebase):
    headers = headers_para(
        firebase, "uid-carla", email="carla@example.com", nome="Nome do Token"
    )
    resposta = client.post(
        "/api/auth/sessao",
        headers=headers,
        json={"nome": "Carla Mendes"},
    )
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["usuario"]["nome"] == "Carla Mendes"

    invalido = client.post(
        "/api/auth/sessao",
        headers=headers,
        json={"nome": "Carla 123"},
    )
    assert invalido.status_code == 422


def test_me_sem_token_e_token_invalido(client, firebase):
    sem = client.get("/api/auth/me")
    assert sem.status_code == 401
    assert sem.json()["erro"]["codigo"] == "NAO_AUTENTICADO"

    # O verificador falso garante 401 determinístico, sem depender de
    # Application Default Credentials ou do estado global do firebase-admin.
    invalido = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer token-desconhecido"}
    )
    assert invalido.status_code == 401
    assert invalido.json()["erro"]["codigo"] == "TOKEN_INVALIDO"


def test_token_de_outro_projeto_e_rejeitado(client, firebase):
    headers = headers_para(
        firebase,
        "uid-x",
        email="x@example.com",
        aud="outro-projeto",
        iss="https://securetoken.google.com/outro-projeto",
    )
    resposta = client.get("/api/auth/me", headers=headers)
    assert resposta.status_code == 401
    assert resposta.json()["erro"]["codigo"] == "TOKEN_INVALIDO"


def test_papel_professor_exige_allowlist_e_email_verificado(client, firebase):
    headers = headers_para(
        firebase,
        "uid-prof",
        email="professor@example.com",
        nome="Professor",
        email_verified=True,
    )
    resposta = client.get("/api/auth/me", headers=headers)
    assert resposta.status_code == 200
    assert resposta.json()["papel"] == "professor"

    headers_nao_verificado = headers_para(
        firebase,
        "uid-prof-2",
        email="professor@example.com",
        nome="Professor",
        email_verified=False,
    )
    resposta = client.get("/api/auth/me", headers=headers_nao_verificado)
    assert resposta.status_code == 200
    assert resposta.json()["papel"] == "aluno"
