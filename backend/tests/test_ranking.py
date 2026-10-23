from app.domain.normalizacao import normalizar_nome
from app.models import SENHA_HASH_INERTE, Partida, Usuario
from tests.fakes import headers_para


def _viewer(client, firebase, usuario="viewer", nome="Viewer"):
    headers = headers_para(
        firebase, "uid-viewer", email="viewer@example.com", nome=nome
    )
    resposta = client.get("/api/auth/me", headers=headers)
    assert resposta.status_code == 200
    return headers, resposta.json()["usuario"]["id"]


def _partida_concluida(
    db,
    usuario_id,
    acertos,
    duracao_ms,
    concluida_em="2026-10-23T14:00:00+00:00",
):
    db.add(
        Partida(
            usuario_id=usuario_id,
            status="concluida",
            total_perguntas=22,
            iniciada_em="2026-10-23T13:00:00+00:00",
            concluida_em=concluida_em,
            duracao_ms=duracao_ms,
            acertos=acertos,
            erros=22 - acertos,
        )
    )


def _criar_usuario(db, nome, usuario):
    user = Usuario(
        nome=nome,
        nome_ordenacao=normalizar_nome(nome),
        usuario=usuario,
        senha_hash=SENHA_HASH_INERTE,
        criado_em="2026-10-23T12:00:00+00:00",
    )
    db.add(user)
    db.flush()
    return user


def test_ranking_com_220_alunos(client, firebase, db):
    headers, viewer_id = _viewer(client, firebase, "viewer", "Viewer da Silva")
    _partida_concluida(db, viewer_id, 10, 500000)
    for indice in range(1, 220):
        user = _criar_usuario(db, f"Aluno {indice:03d}", f"aluno.{indice:03d}")
        _partida_concluida(
            db,
            user.id,
            acertos=indice % 23,
            duracao_ms=100000 + indice,
        )
    db.commit()

    resposta = client.get("/api/ranking?limite=500", headers=headers)
    assert resposta.status_code == 200, resposta.text
    dados = resposta.json()
    assert dados["totalParticipantes"] == 220
    assert len(dados["itens"]) == 220
    assert dados["itens"][0]["posicao"] == 1
    assert dados["itens"][-1]["posicao"] == 220
    assert dados["meuResultado"] is not None

    pagina = client.get("/api/ranking?limite=1&offset=1", headers=headers)
    assert pagina.status_code == 200
    assert len(pagina.json()["itens"]) == 1
    assert pagina.json()["itens"][0]["posicao"] == 2


def test_ranking_desempate_alfabetico_e_tempo(client, firebase, db):
    headers, ana_id = _viewer(client, firebase, "ana", "Ana")
    alvaro = _criar_usuario(db, "Álvaro", "alvaro")
    bruno = _criar_usuario(db, "Bruno", "bruno")
    _partida_concluida(db, alvaro.id, 20, 110000, "2026-10-23T14:00:00+00:00")
    _partida_concluida(db, bruno.id, 20, 110000, "2026-10-23T14:01:00+00:00")
    _partida_concluida(db, ana_id, 20, 120000, "2026-10-23T14:02:00+00:00")
    db.commit()

    dados = client.get("/api/ranking?limite=500", headers=headers).json()
    nomes = [item["nome"] for item in dados["itens"]]
    assert nomes == ["Álvaro", "Bruno", "Ana"]
    assert dados["meuResultado"]["posicao"] == 3


def test_ranking_usa_melhor_tentativa(client, firebase, db):
    headers, user_id = _viewer(client, firebase, "melhor", "Melhor Aluno")
    _partida_concluida(db, user_id, 10, 100000, "2026-10-23T14:00:00+00:00")
    _partida_concluida(db, user_id, 20, 300000, "2026-10-23T14:05:00+00:00")
    db.commit()
    dados = client.get("/api/ranking?limite=500", headers=headers).json()
    assert dados["totalParticipantes"] == 1
    assert dados["itens"][0]["acertos"] == 20


def test_ranking_sem_partida_concluida(client, firebase):
    headers, _ = _viewer(client, firebase, "sem.partida", "Sem Partida")
    dados = client.get("/api/ranking?limite=500", headers=headers).json()
    assert dados["totalParticipantes"] == 0
    assert dados["itens"] == []
    assert dados["meuResultado"] is None
