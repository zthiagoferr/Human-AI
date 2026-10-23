import logging

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import (
    ErroAPI,
    acesso_negado,
    autenticacao_indisponivel,
    nao_autenticado,
)
from app.firebase_auth import (
    VerificadorFirebase,
    eh_professor,
    get_verificador,
    validar_claims,
)
from app.models import Usuario
from app.services import usuario_service

logger = logging.getLogger("humanai.auth")

_bearer = HTTPBearer(auto_error=False)


def obter_claims(
    credenciais: HTTPAuthorizationCredentials | None = Depends(_bearer),
    verificador: VerificadorFirebase = Depends(get_verificador),
) -> dict:
    if credenciais is None or credenciais.scheme.lower() != "bearer":
        raise nao_autenticado("Informe o token Bearer.")
    try:
        claims = verificador.verificar(credenciais.credentials)
    except ErroAPI:
        raise
    except Exception as exc:
        logger.warning("Falha inesperada ao validar token: %s", type(exc).__name__)
        raise autenticacao_indisponivel() from exc
    return validar_claims(claims)


def get_usuario_atual(
    claims: dict = Depends(obter_claims),
    db: Session = Depends(get_db),
) -> Usuario:
    return usuario_service.obter_ou_criar_por_claims(db, claims)


def get_professor_atual(
    usuario: Usuario = Depends(get_usuario_atual),
    claims: dict = Depends(obter_claims),
) -> Usuario:
    if not eh_professor(claims):
        raise acesso_negado()
    return usuario
