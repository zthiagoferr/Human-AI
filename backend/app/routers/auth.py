from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_usuario_atual, obter_claims
from app.exceptions import autenticacao_migrada
from app.firebase_auth import papel_das_claims
from app.models import Usuario
from app.schemas import (
    SessaoRequest,
    SessaoResponse,
    UsuarioPublico,
    VincularRequest,
)
from app.services import usuario_service, vinculo_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _resposta(usuario: Usuario, claims: dict) -> SessaoResponse:
    return SessaoResponse(
        usuario=UsuarioPublico.model_validate(usuario),
        papel=papel_das_claims(claims),
    )


@router.post("/registro", status_code=status.HTTP_410_GONE, deprecated=True)
def registro_migrado() -> None:
    raise autenticacao_migrada()


@router.post("/login", status_code=status.HTTP_410_GONE, deprecated=True)
def login_migrado() -> None:
    raise autenticacao_migrada()


@router.post("/logout", status_code=status.HTTP_410_GONE, deprecated=True)
def logout_migrado() -> None:
    raise autenticacao_migrada()


@router.post("/sessao", response_model=SessaoResponse)
def sessao(
    dados: SessaoRequest | None = None,
    claims: dict = Depends(obter_claims),
    db: Session = Depends(get_db),
) -> SessaoResponse:
    usuario = usuario_service.obter_ou_criar_por_claims(
        db,
        claims,
        dados.nome if dados is not None else None,
    )
    return _resposta(usuario, claims)


@router.get("/me", response_model=SessaoResponse)
def me(
    usuario: Usuario = Depends(get_usuario_atual),
    claims: dict = Depends(obter_claims),
) -> SessaoResponse:
    return _resposta(usuario, claims)


@router.post("/vincular-legado", response_model=SessaoResponse)
def vincular_legado(
    dados: VincularRequest,
    usuario: Usuario = Depends(get_usuario_atual),
    claims: dict = Depends(obter_claims),
    db: Session = Depends(get_db),
) -> SessaoResponse:
    vinculado = vinculo_service.resgatar_codigo(db, usuario, claims, dados.codigo)
    return _resposta(vinculado, claims)
