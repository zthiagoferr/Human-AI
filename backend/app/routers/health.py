from fastapi import APIRouter

from app.domain.cartas import get_acervo
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        versao="1.0.0",
        cartas_carregadas=len(get_acervo().todas),
    )
