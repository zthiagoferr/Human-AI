from app.domain.cartas import (
    HUMANAS,
    IAS,
    CartaGabarito,
    carregar_cartas,
    validar_cartas,
)


def test_cartas_carregadas():
    acervo = carregar_cartas()
    assert len(acervo.todas) == 22
    assert [carta.numero for carta in acervo.todas] == list(range(1, 23))
    assert {carta.id for carta in acervo.todas} == HUMANAS | IAS
    assert {carta.id for carta in acervo.todas if carta.origem == "humano"} == HUMANAS
    assert {carta.id for carta in acervo.todas if carta.origem == "ia"} == IAS
    assert all(carta.citacao.strip() for carta in acervo.todas)
    assert all(carta.categoria.strip() for carta in acervo.todas)
    assert all(carta.tema.strip() for carta in acervo.todas)
    assert all(carta.analise.strip() for carta in acervo.todas)


def test_publicas_nao_vazam_gabarito():
    acervo = carregar_cartas()
    publicas = acervo.publicas()
    assert len(publicas) == 22
    for carta in publicas:
        campos = set(carta.model_dump().keys())
        assert campos == {"id", "numero", "citacao", "categoria", "tema"}


def test_validacao_rejeita_origem_divergente():
    acervo = carregar_cartas()
    cartas = [carta.model_copy() for carta in acervo.todas]
    primeira = cartas[0]
    cartas[0] = CartaGabarito(
        **{
            **primeira.model_dump(),
            "origem": "ia",
        }
    )
    try:
        validar_cartas(cartas)
    except ValueError as exc:
        assert "origens" in str(exc)
    else:
        raise AssertionError("a validação deveria falhar")
