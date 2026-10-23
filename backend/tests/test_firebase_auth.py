import pytest
from firebase_admin import auth

from app import firebase_auth
from app.exceptions import ErroAPI


def _claims(**extras):
    dados = {
        "uid": "uid-1",
        "sub": "uid-1",
        "aud": "humanai-test",
        "iss": "https://securetoken.google.com/humanai-test",
        "email": "aluno@example.com",
        "email_verified": True,
    }
    dados.update(extras)
    return dados


def test_verifica_token_valido(monkeypatch):
    monkeypatch.setattr(
        firebase_auth.auth, "verify_id_token", lambda token, **kwargs: _claims()
    )
    assert firebase_auth.verificar_id_token("token")["uid"] == "uid-1"


def test_audiencia_de_outro_projeto(monkeypatch):
    monkeypatch.setattr(
        firebase_auth.auth,
        "verify_id_token",
        lambda token, **kwargs: _claims(aud="outro-projeto"),
    )
    with pytest.raises(ErroAPI) as exc:
        firebase_auth.verificar_id_token("token")
    assert exc.value.codigo == "TOKEN_INVALIDO"


def test_emissor_invalido(monkeypatch):
    monkeypatch.setattr(
        firebase_auth.auth,
        "verify_id_token",
        lambda token, **kwargs: _claims(
            iss="https://securetoken.google.com/outro-projeto"
        ),
    )
    with pytest.raises(ErroAPI) as exc:
        firebase_auth.verificar_id_token("token")
    assert exc.value.codigo == "TOKEN_INVALIDO"


def test_claim_sem_uid(monkeypatch):
    monkeypatch.setattr(
        firebase_auth.auth,
        "verify_id_token",
        lambda token, **kwargs: _claims(uid=None, sub=None),
    )
    with pytest.raises(ErroAPI) as exc:
        firebase_auth.verificar_id_token("token")
    assert exc.value.codigo == "TOKEN_INVALIDO"


def test_token_expirado(monkeypatch):
    def falha(token, **kwargs):
        raise auth.ExpiredIdTokenError("expirado", None)

    monkeypatch.setattr(firebase_auth.auth, "verify_id_token", falha)
    with pytest.raises(ErroAPI) as exc:
        firebase_auth.verificar_id_token("token")
    assert exc.value.status_code == 401
    assert exc.value.codigo == "TOKEN_EXPIRADO"


def test_token_revogado(monkeypatch):
    def falha(token, **kwargs):
        raise auth.RevokedIdTokenError("revogado")

    monkeypatch.setattr(firebase_auth.auth, "verify_id_token", falha)
    with pytest.raises(ErroAPI) as exc:
        firebase_auth.verificar_id_token("token")
    assert exc.value.codigo == "TOKEN_REVOGADO"


def test_token_invalido(monkeypatch):
    def falha(token, **kwargs):
        raise auth.InvalidIdTokenError("invalido")

    monkeypatch.setattr(firebase_auth.auth, "verify_id_token", falha)
    with pytest.raises(ErroAPI) as exc:
        firebase_auth.verificar_id_token("token")
    assert exc.value.codigo == "TOKEN_INVALIDO"


def test_falha_de_certificado(monkeypatch):
    def falha(token, **kwargs):
        raise auth.CertificateFetchError("sem rede", None)

    monkeypatch.setattr(firebase_auth.auth, "verify_id_token", falha)
    with pytest.raises(ErroAPI) as exc:
        firebase_auth.verificar_id_token("token")
    assert exc.value.status_code == 503
    assert exc.value.codigo == "AUTENTICACAO_INDISPONIVEL"
