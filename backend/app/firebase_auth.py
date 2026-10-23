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


def inicializar_firebase() -> bool:
    """Inicializa o Admin SDK via ADC ou GOOGLE_APPLICATION_CREDENTIALS.

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
            caminho = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            credencial = credentials.Certificate(caminho) if caminho else None
            _app = firebase_admin.initialize_app(
                credencial,
                options={"projectId": settings.firebase_project_id},
            )
        except Exception as exc:  # noqa: BLE001
            if settings.producao:
                raise RuntimeError(
                    "Firebase Admin não pôde ser inicializado. "
                    "Verifique GOOGLE_APPLICATION_CREDENTIALS/ADC."
                ) from exc
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
