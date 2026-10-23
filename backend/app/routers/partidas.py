from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_usuario_atual
from app.models import Usuario
from app.schemas import (
    PartidaResponse,
    RespostasRequest,
    ResultadoPartida,
)
from app.services import partida_service

router = APIRouter(prefix="/partidas", tags=["partidas"])


@router.get("/atual", response_model=PartidaResponse)
def atual(
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
) -> PartidaResponse:
    return PartidaResponse(partida=partida_service.obter_atual(db, usuario))


@router.post("", response_model=PartidaResponse, status_code=status.HTTP_201_CREATED)
def iniciar(
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
) -> PartidaResponse:
    return PartidaResponse(partida=partida_service.iniciar(db, usuario))


@router.post("/{partida_id}/abandonar", status_code=status.HTTP_204_NO_CONTENT)
def abandonar(
    partida_id: int,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
) -> None:
    partida_service.abandonar(db, usuario, partida_id)


@router.post("/{partida_id}/respostas", response_model=ResultadoPartida)
def responder(
    partida_id: int,
    dados: RespostasRequest,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
) -> ResultadoPartida:
    return partida_service.responder(db, usuario, partida_id, dados.respostas)


@router.get("/{partida_id}/resultado", response_model=ResultadoPartida)
def resultado(
    partida_id: int,
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
) -> ResultadoPartida:
    return partida_service.obter_resultado(db, usuario, partida_id)
