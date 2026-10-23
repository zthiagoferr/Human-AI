from sqlalchemy import select

from app.models import Partida
from tests.conftest import criar_usuario
from tests.fakes import headers_para


def _aluno(firebase, token="uid-aluno"):
    return headers_para(
        firebase, token, email="aluno@example.com", nome="Aluno"
    )


def _professor(firebase):
    return headers_para(
        firebase,
        "uid-prof",
        email="professor@example.com",
        nome="Professor",
        email_verified=True,
    )


def _codigo(client, headers_prof, usuario_id):
    resposta = client.post(
        f"/api/professor/legado/{usuario_id}/codigo", headers=headers_prof
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.json()["codigo"]


def test_vinculo_preserva_partidas_e_move_uid(client, firebase, db):
    legado = criar_usuario(db, nome="Ana Lima", usuario="ana.lima")
    partida = Partida(
        usuario_id=legado.id,
        status="concluida",
        total_perguntas=22,
        iniciada_em="2026-10-23T13:00:00+00:00",
        concluida_em="2026-10-23T13:30:00+00:00",
        duracao_ms=1800000,
        acertos=18,
        erros=4,
    )
    db.add(partida)
    db.commit()

    headers_aluno = _aluno(firebase)
    shell = client.get("/api/auth/me", headers=headers_aluno).json()["usuario"]
    assert shell["id"] != legado.id

    codigo = _codigo(client, _professor(firebase), legado.id)
    resposta = client.post(
        "/api/auth/vincular-legado",
        headers=headers_aluno,
        json={"codigo": codigo},
    )
    assert resposta.status_code == 200, resposta.text
    assert resposta.json()["usuario"]["id"] == legado.id

    db.expire_all()
    db.refresh(legado)
    shell_db = db.get(type(legado), shell["id"])
    assert legado.firebase_uid == "uid-aluno"
    assert shell_db is not None
    assert shell_db.firebase_uid is None
    assert db.scalar(select(Partida).where(Partida.id == partida.id)).usuario_id == legado.id

    ranking = client.get("/api/ranking?limite=500", headers=headers_aluno)
    assert ranking.status_code == 200
    assert ranking.json()["meuResultado"]["acertos"] == 18

    repetido = client.post(
        "/api/auth/vincular-legado",
        headers=headers_aluno,
        json={"codigo": codigo},
    )
    assert repetido.status_code == 400
    assert repetido.json()["erro"]["codigo"] == "CODIGO_INVALIDO"


def test_codigo_expirado_e_invalido(client, firebase, db):
    legado = criar_usuario(db, nome="Bia", usuario="bia")
    headers_aluno = _aluno(firebase)

    invalido = client.post(
        "/api/auth/vincular-legado",
        headers=headers_aluno,
        json={"codigo": "AAAAAAAAAA"},
    )
    assert invalido.status_code == 400

    codigo = _codigo(client, _professor(firebase), legado.id)
    from app.models import CodigoVinculo
    from app.security import hash_codigo, normalizar_codigo

    registro = db.scalar(
        select(CodigoVinculo).where(
            CodigoVinculo.codigo_hash == hash_codigo(normalizar_codigo(codigo))
        )
    )
    registro.expira_em = "2020-01-01T00:00:00+00:00"
    db.commit()

    expirado = client.post(
        "/api/auth/vincular-legado",
        headers=headers_aluno,
        json={"codigo": codigo},
    )
    assert expirado.status_code == 400


def test_shell_com_partida_nao_vincula(client, firebase, db):
    legado = criar_usuario(db, nome="Carla", usuario="carla")
    headers_aluno = _aluno(firebase)
    shell = client.get("/api/auth/me", headers=headers_aluno).json()["usuario"]

    db.add(
        Partida(
            usuario_id=shell["id"],
            status="abandonada",
            total_perguntas=22,
            iniciada_em="2026-10-23T13:00:00+00:00",
        )
    )
    db.commit()

    codigo = _codigo(client, _professor(firebase), legado.id)
    resposta = client.post(
        "/api/auth/vincular-legado",
        headers=headers_aluno,
        json={"codigo": codigo},
    )
    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "CONTA_JA_POSSUI_PARTIDAS"

    db.refresh(legado)
    assert legado.firebase_uid is None


def test_usuario_legado_ja_vinculado(client, firebase, db):
    legado = criar_usuario(
        db, nome="Davi", usuario="davi", firebase_uid="uid-outro"
    )
    resposta = client.post(
        f"/api/professor/legado/{legado.id}/codigo", headers=_professor(firebase)
    )
    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "USUARIO_JA_VINCULADO"
