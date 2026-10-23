from app.domain.cartas import get_acervo
from tests.fakes import headers_para


def _headers(firebase, token="uid-aluno", email="aluno@example.com", nome="Aluno Teste"):
    return headers_para(firebase, token, email=email, nome=nome)


def _iniciar(client, headers):
    resposta = client.post("/api/partidas", headers=headers)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["partida"]


def _respostas(partida, escolha="humano"):
    return [{"cartaId": carta["id"], "escolha": escolha} for carta in partida["cartas"]]


def test_partida_retorna_22_cartas_sem_gabarito(client, firebase):
    headers = _headers(firebase)
    atual = client.get("/api/partidas/atual", headers=headers)
    assert atual.status_code == 200
    assert atual.json() == {"partida": None}

    partida = _iniciar(client, headers)
    assert partida["totalPerguntas"] == 22
    assert len(partida["cartas"]) == 22
    assert [carta["numero"] for carta in partida["cartas"]] == list(range(1, 23))
    for carta in partida["cartas"]:
        assert set(carta.keys()) == {"id", "numero", "citacao", "categoria", "tema"}

    corpo = client.get("/api/partidas/atual", headers=headers).text
    assert "origem" not in corpo
    assert "analise" not in corpo
    assert "respostaCorreta" not in corpo


def test_uma_partida_ativa_e_retomada(client, firebase):
    headers = _headers(firebase)
    partida = _iniciar(client, headers)
    segunda = client.post("/api/partidas", headers=headers)
    assert segunda.status_code == 409
    assert segunda.json()["erro"]["codigo"] == "PARTIDA_EM_ANDAMENTO"
    atual = client.get("/api/partidas/atual", headers=headers)
    assert atual.status_code == 200
    assert atual.json()["partida"]["id"] == partida["id"]


def test_submissao_exige_22_respostas(client, firebase):
    headers = _headers(firebase)
    partida = _iniciar(client, headers)
    respostas = _respostas(partida)
    faltando = client.post(
        f"/api/partidas/{partida['id']}/respostas",
        headers=headers,
        json={"respostas": respostas[:21]},
    )
    assert faltando.status_code == 422
    assert faltando.json()["erro"]["codigo"] == "RESPOSTAS_INCOMPLETAS"

    duplicada = respostas[:21] + [respostas[0]]
    resposta = client.post(
        f"/api/partidas/{partida['id']}/respostas",
        headers=headers,
        json={"respostas": duplicada},
    )
    assert resposta.status_code == 422
    assert resposta.json()["erro"]["codigo"] == "RESPOSTA_DUPLICADA"

    invalida = respostas[:21] + [{"cartaId": "99", "escolha": "humano"}]
    resposta = client.post(
        f"/api/partidas/{partida['id']}/respostas",
        headers=headers,
        json={"respostas": invalida},
    )
    assert resposta.status_code == 422


def test_resultado_com_acertos_e_analises(client, firebase):
    headers = _headers(firebase)
    partida = _iniciar(client, headers)
    acervo = get_acervo()
    respostas = [
        {"cartaId": carta["id"], "escolha": acervo.obter(carta["id"]).origem}
        for carta in partida["cartas"]
    ]
    resposta = client.post(
        f"/api/partidas/{partida['id']}/respostas",
        headers=headers,
        json={"respostas": respostas},
    )
    assert resposta.status_code == 200, resposta.text
    resultado = resposta.json()
    assert resultado["acertos"] == 22
    assert resultado["erros"] == 0
    assert resultado["percentual"] == 100.0
    assert resultado["duracaoMs"] >= 0
    assert len(resultado["correcao"]) == 22
    assert all(item["acertou"] for item in resultado["correcao"])
    assert all(item["analise"] for item in resultado["correcao"])
    assert resultado["correcao"][0]["respostaCorreta"] == acervo.obter("01").origem

    final = client.get(f"/api/partidas/{partida['id']}/resultado", headers=headers)
    assert final.status_code == 200
    assert final.json() == resultado


def test_resultado_antes_de_finalizar(client, firebase):
    headers = _headers(firebase)
    partida = _iniciar(client, headers)
    resposta = client.get(f"/api/partidas/{partida['id']}/resultado", headers=headers)
    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "PARTIDA_NAO_CONCLUIDA"
    assert "analise" not in resposta.text


def test_idempotencia_do_envio(client, firebase):
    headers = _headers(firebase)
    partida = _iniciar(client, headers)
    respostas = _respostas(partida)
    primeira = client.post(
        f"/api/partidas/{partida['id']}/respostas",
        headers=headers,
        json={"respostas": respostas},
    )
    assert primeira.status_code == 200
    segunda = client.post(
        f"/api/partidas/{partida['id']}/respostas",
        headers=headers,
        json={"respostas": []},
    )
    assert segunda.status_code == 200
    assert segunda.json()["acertos"] == primeira.json()["acertos"]


def test_abandonar_e_outro_usuario(client, firebase):
    headers = _headers(firebase)
    partida = _iniciar(client, headers)
    abandono = client.post(f"/api/partidas/{partida['id']}/abandonar", headers=headers)
    assert abandono.status_code == 204
    assert client.get("/api/partidas/atual", headers=headers).json()["partida"] is None

    outra = _iniciar(client, headers)
    headers_b = _headers(
        firebase, token="uid-outro", email="outro@example.com", nome="Outro Aluno"
    )
    alheia = client.get(f"/api/partidas/{outra['id']}/resultado", headers=headers_b)
    assert alheia.status_code == 404
    tentativa = client.post(
        f"/api/partidas/{outra['id']}/respostas",
        headers=headers_b,
        json={"respostas": _respostas(outra)},
    )
    assert tentativa.status_code == 404
