from tests.conftest import criar_usuario
from tests.fakes import headers_para


def _professor(firebase, token="uid-prof", verificado=True):
    return headers_para(
        firebase,
        token,
        email="professor@example.com",
        nome="Professor",
        email_verified=verificado,
    )


def test_aluno_nao_acessa_rotas_de_professor(client, firebase):
    headers = headers_para(
        firebase, "uid-aluno", email="aluno@example.com", nome="Aluno"
    )
    resposta = client.get("/api/professor/legado/pendentes", headers=headers)
    assert resposta.status_code == 403
    assert resposta.json()["erro"]["codigo"] == "ACESSO_NEGADO"


def test_professor_sem_email_verificado_e_negado(client, firebase):
    headers = _professor(firebase, token="uid-prof-2", verificado=False)
    resposta = client.get("/api/professor/legado/pendentes", headers=headers)
    assert resposta.status_code == 403


def test_professor_lista_pendentes_e_gera_codigo(client, firebase, db):
    legado = criar_usuario(db, nome="Ana Lima", usuario="ana.lima")
    vinculado = criar_usuario(
        db,
        nome="Bia",
        usuario="bia",
        firebase_uid="uid-bia",
    )
    headers = _professor(firebase)

    pendentes = client.get("/api/professor/legado/pendentes", headers=headers)
    assert pendentes.status_code == 200, pendentes.text
    dados = pendentes.json()
    ids = [item["id"] for item in dados["itens"]]
    assert legado.id in ids
    assert vinculado.id not in ids

    gerado = client.post(
        f"/api/professor/legado/{legado.id}/codigo", headers=headers
    )
    assert gerado.status_code == 200, gerado.text
    corpo = gerado.json()
    assert len(corpo["codigo"]) == 11
    assert corpo["codigo"][5] == "-"
    assert corpo["usuario"]["id"] == legado.id

    db.refresh(legado)
    assert legado.firebase_uid is None


def test_gerar_codigo_para_usuario_inexistente_ou_vinculado(client, firebase, db):
    headers = _professor(firebase)
    inexistente = client.post("/api/professor/legado/99999/codigo", headers=headers)
    assert inexistente.status_code == 404

    vinculado = criar_usuario(db, nome="Bia", usuario="bia", firebase_uid="uid-bia")
    resposta = client.post(
        f"/api/professor/legado/{vinculado.id}/codigo", headers=headers
    )
    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "USUARIO_JA_VINCULADO"
