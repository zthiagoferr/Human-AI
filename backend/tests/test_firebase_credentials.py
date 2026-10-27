import json

import pytest

from app import firebase_auth
from app.config import settings
from app.firebase_auth import _validar_credencial_json


def test_json_invalido():
    with pytest.raises(ValueError, match="inválido"):
        _validar_credencial_json("{", "projeto")


def test_json_nao_e_service_account():
    with pytest.raises(ValueError, match="service account"):
        _validar_credencial_json('{"type": "user"}', "projeto")


def test_json_de_outro_projeto():
    with pytest.raises(ValueError, match="outro projeto"):
        _validar_credencial_json(
            '{"type": "service_account", "project_id": "outro"}',
            "projeto",
        )


def test_json_valido_retorna_dict():
    info = {"type": "service_account", "project_id": "projeto"}
    assert _validar_credencial_json(json.dumps(info), "projeto") == info


def test_credencial_inline_tem_precedencia(monkeypatch):
    info = {"type": "service_account", "project_id": "projeto"}
    monkeypatch.setattr(
        settings, "firebase_credentials_json", json.dumps(info)
    )
    monkeypatch.setattr(settings, "firebase_project_id", "projeto")
    monkeypatch.setattr(
        firebase_auth.credentials,
        "Certificate",
        lambda credencial: f"certificado:{credencial['project_id']}",
    )
    assert firebase_auth._carregar_credencial() == "certificado:projeto"
