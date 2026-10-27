import json
import logging
import os
from typing import Any

import firebase_admin
from firebase_admin import auth, credentials
from firebase_admin.exceptions import FirebaseError

from app.config import settings
from app.exceptions import (
    autenticacao_indisponivel,
    token_expirado,
    token_invalido,
    token_revogado,
)

logger = logging.getLogger("humanai.firebase")

_app: firebase_admin.App | None = None
_inicializacao_tentada = False
_disponivel = False


def _validar_credencial_json(bruto: str, projeto: str) -> dict:
    try:
        info = json.loads(bruto)
    except json.JSONDecodeError:
        raise ValueError("HUMANAI_FIREBASE_CREDENTIALS_JSON inválido.") from None

    if not isinstance(info, dict) or info.get("type") != "service_account":
        raise ValueError(
            "HUMANAI_FIREBASE_CREDENTIALS_JSON não é uma service account."
        )
    if info.get("project_id") != projeto:
        raise ValueError(
            "HUMANAI_FIREBASE_CREDENTIALS_JSON pertence a outro projeto."
        )
    return info


def _carregar_credencial():
    bruto = settings.firebase_credentials_json.strip()
    if bruto:
        return credentials.Certificate(
            _validar_credencial_json(bruto, settings.firebase_project_id.strip())
        )

    caminho = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if caminho:
        return credentials.Certificate(caminho)

    return None  # ADC


def inicializar_firebase() -> bool:
    """Inicializa o Admin SDK via JSON inline, arquivo ou ADC.

    Nunca imprime o caminho nem o conteúdo da credencial.
    """
    global _app, _inicializacao_tentada, _disponivel

    if settings.env.lower() == "test":
        _inicializacao_tentada = True
        _disponivel = True
        return True
    if _inicializacao_tentada:
        return _disponivel

    _inicializacao_tentada = True
    if not settings.firebase_project_id.strip():
        mensagem = "HUMANAI_FIREBASE_PROJECT_ID não configurado."
        if settings.producao:
            raise RuntimeError(mensagem)
        logger.warning("%s A autenticação Firebase ficará indisponível.", mensagem)
        _disponivel = False
        return False

    try:
        _app = firebase_admin.get_app()
    except ValueError:
        try:
            credencial = _carregar_credencial()
            _app = firebase_admin.initialize_app(
                credencial,
                options={"projectId": settings.firebase_project_id},
            )
        except Exception as exc:  # noqa: BLE001
            if settings.producao:
                raise RuntimeError(
                    "Firebase Admin não pôde ser inicializado. "
                    "Verifique HUMANAI_FIREBASE_CREDENTIALS_JSON, "
                    "GOOGLE_APPLICATION_CREDENTIALS ou ADC."
                ) from None
            logger.warning(
                "Firebase Admin indisponível (%s). Endpoints autenticados retornarão 503.",
                type(exc).__name__,
            )
            _disponivel = False
            return False

    _disponivel = True
    return True


def _verificar_sdk(token: str) -> dict[str, Any]:
    if not inicializar_firebase():
        raise autenticacao_indisponivel()
    try:
        return auth.verify_id_token(
            token,
            check_revoked=settings.firebase_check_revoked,
        )
    except auth.ExpiredIdTokenError as exc:
        raise token_expirado() from exc
    except auth.RevokedIdTokenError as exc:
        raise token_revogado() from exc
    except auth.InvalidIdTokenError as exc:
        raise token_invalido() from exc
    except auth.CertificateFetchError as exc:
        logger.warning("Falha ao buscar certificados do Firebase: %s", type(exc).__name__)
        raise autenticacao_indisponivel() from exc
    except FirebaseError as exc:
        logger.warning("Falha ao validar token Firebase: %s", type(exc).__name__)
        raise autenticacao_indisponivel() from exc
    except ValueError as exc:
        raise token_invalido() from exc


def validar_claims(claims: dict[str, Any]) -> dict[str, Any]:
    projeto = settings.firebase_project_id.strip()
    if not projeto:
        raise autenticacao_indisponivel()
    if claims.get("aud") != projeto:
        raise token_invalido()
    if claims.get("iss") != f"https://securetoken.google.com/{projeto}":
        raise token_invalido()
    uid = claims.get("uid") or claims.get("sub")
    if not isinstance(uid, str) or not uid.strip():
        raise token_invalido()
    return claims


def verificar_id_token(token: str) -> dict[str, Any]:
    return validar_claims(_verificar_sdk(token))


class VerificadorFirebase:
    def verificar(self, token: str) -> dict[str, Any]:
        return verificar_id_token(token)


def get_verificador() -> VerificadorFirebase:
    return VerificadorFirebase()


def uid_das_claims(claims: dict[str, Any]) -> str:
    uid = claims.get("uid") or claims.get("sub")
    if not isinstance(uid, str) or not uid.strip():
        raise token_invalido()
    return uid.strip()


def email_das_claims(claims: dict[str, Any]) -> str | None:
    email = claims.get("email")
    return email.strip().casefold() if isinstance(email, str) and email.strip() else None


def eh_professor(claims: dict[str, Any]) -> bool:
    email = email_das_claims(claims)
    if not email or claims.get("email_verified") is not True:
        return False
    return email in settings.professor_emails_list


def papel_das_claims(claims: dict[str, Any]) -> str:
    return "professor" if eh_professor(claims) else "aluno"
