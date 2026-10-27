import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.cartas import get_acervo
from app.exceptions import ErroAPI
from app.schemas import HealthResponse

logger = logging.getLogger("humanai.health")
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("Health check: banco indisponível (%s).", type(exc).__name__)
        raise ErroAPI(
            503,
            "BANCO_INDISPONIVEL",
            "Banco de dados indisponível.",
        ) from None

    return HealthResponse(
        status="ok",
        versao="1.0.0",
        cartas_carregadas=len(get_acervo().todas),
    )
