import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import init_db
from app.domain.cartas import get_acervo, inicializar_acervo
from app.exceptions import ErroAPI
from app.firebase_auth import inicializar_firebase
from app.routers import auth, health, partidas, professor, ranking

logger = logging.getLogger("humanai")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    inicializar_acervo()
    init_db()
    inicializar_firebase()
    yield


def _erro(
    status_code: int,
    codigo: str,
    mensagem: str,
    detalhes: object | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "erro": {
                "codigo": codigo,
                "mensagem": mensagem,
                "detalhes": detalhes,
            }
        },
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="Humano ou IA?",
        version="1.0.0",
        description="API do jogo educacional de letramento digital.",
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
        expose_headers=[],
        max_age=600,
    )

    @app.middleware("http")
    async def cabecalhos(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        if request.url.path.startswith("/api/") and request.url.path != "/api/health":
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ErroAPI)
    async def erro_api_handler(_request: Request, exc: ErroAPI) -> JSONResponse:
        return _erro(exc.status_code, exc.codigo, exc.mensagem, exc.detalhes)

    @app.exception_handler(RequestValidationError)
    async def validacao_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        detalhes = []
        for erro in exc.errors():
            loc = [str(parte) for parte in erro.get("loc", []) if parte != "body"]
            detalhes.append(
                {
                    "campo": ".".join(loc) if loc else None,
                    "mensagem": erro.get("msg", "Valor inválido."),
                }
            )
        return _erro(422, "DADOS_INVALIDOS", "Um ou mais campos são inválidos.", detalhes)

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        if exc.status_code == 404:
            return _erro(404, "ROTA_NAO_ENCONTRADA", "Rota não encontrada.")
        if exc.status_code == 405:
            return _erro(405, "METODO_NAO_PERMITIDO", "Método não permitido.")
        return _erro(exc.status_code, "ERRO_HTTP", "Não foi possível processar a requisição.")

    @app.exception_handler(Exception)
    async def inesperado_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Erro inesperado", exc_info=exc)
        return _erro(500, "ERRO_INTERNO", "Erro interno do servidor.")

    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(partidas.router, prefix="/api")
    app.include_router(ranking.router, prefix="/api")
    app.include_router(professor.router, prefix="/api")

    @app.get("/api", include_in_schema=False)
    def raiz_api() -> dict[str, str]:
        return {"nome": "Humano ou IA?", "versao": "1.0.0"}

    return app


app = create_app()


def cartas_carregadas() -> int:
    return len(get_acervo().todas)
