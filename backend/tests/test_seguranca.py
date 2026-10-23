from app.domain.cartas import get_acervo
from tests.fakes import headers_para


def _headers(firebase, token="uid-seguro", email="seguro@example.com"):
    return headers_para(firebase, token, email=email, nome="Aluno Seguro")


def test_cors_preflight(client):
    resposta = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://localhost:4200",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert resposta.status_code == 200
    assert resposta.headers["access-control-allow-origin"] == "http://localhost:4200"


def test_cors_origem_nao_permitida(client):
    resposta = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in resposta.headers


def test_nenhum_gabarito_antes_do_fim(client, firebase):
    headers = _headers(firebase)
    partida = client.post("/api/partidas", headers=headers).json()["partida"]
    corpo = str(partida)
    assert "origem" not in corpo
    assert "analise" not in corpo
    assert "respostaCorreta" not in corpo

    for carta in partida["cartas"]:
        assert carta["id"] in {item.id for item in get_acervo().todas}
        assert set(carta) == {"id", "numero", "citacao", "categoria", "tema"}

    resultado = client.get(
        f"/api/partidas/{partida['id']}/resultado", headers=headers
    )
    assert resultado.status_code == 409
    assert resultado.json()["erro"]["codigo"] == "PARTIDA_NAO_CONCLUIDA"
    assert "analise" not in resultado.text
    assert "respostaCorreta" not in resultado.text


def test_health_publico(client):
    resposta = client.get("/api/health")
    assert resposta.status_code == 200
    assert resposta.json()["cartasCarregadas"] == 22


def test_cache_control_em_rota_autenticada(client, firebase):
    headers = _headers(firebase)
    resposta = client.get("/api/auth/me", headers=headers)
    assert resposta.headers["cache-control"] == "no-store"
    assert resposta.headers["x-content-type-options"] == "nosniff"
