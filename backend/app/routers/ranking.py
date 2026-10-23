from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_usuario_atual
from app.models import Usuario
from app.schemas import RankingResponse
from app.services import ranking_service

router = APIRouter(prefix="/ranking", tags=["ranking"])


@router.get("", response_model=RankingResponse)
def ranking(
    limite: int = Query(100, ge=1, le=settings.ranking_max_limit),
    offset: int = Query(0, ge=0),
    usuario: Usuario = Depends(get_usuario_atual),
    db: Session = Depends(get_db),
) -> RankingResponse:
    return ranking_service.obter_ranking(db, usuario.id, limite, offset)
