from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_professor_atual, obter_claims
from app.firebase_auth import uid_das_claims
from app.models import Usuario
from app.schemas import (
    CodigoGeradoResponse,
    PendentesResponse,
    UsuarioPendente,
    UsuarioPublico,
)
from app.services import vinculo_service

router = APIRouter(prefix="/professor", tags=["professor"])


@router.get("/legado/pendentes", response_model=PendentesResponse)
def pendentes(
    limite: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _professor: Usuario = Depends(get_professor_atual),
    db: Session = Depends(get_db),
) -> PendentesResponse:
    total, itens = vinculo_service.listar_pendentes(db, limite, offset)
    return PendentesResponse(
        total=total,
        limite=limite,
        offset=offset,
        itens=[UsuarioPendente.model_validate(item) for item in itens],
    )


@router.post("/legado/{usuario_id}/codigo", response_model=CodigoGeradoResponse)
def gerar_codigo(
    usuario_id: int,
    _professor: Usuario = Depends(get_professor_atual),
    claims: dict = Depends(obter_claims),
    db: Session = Depends(get_db),
) -> CodigoGeradoResponse:
    registro, codigo, usuario = vinculo_service.gerar_codigo(
        db,
        usuario_id,
        uid_das_claims(claims),
    )
    return CodigoGeradoResponse(
        codigo=codigo,
        expira_em=registro.expira_em,
        usuario=UsuarioPublico.model_validate(usuario),
    )
