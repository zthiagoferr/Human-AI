from __future__ import annotations

from typing import Any

from app.config import settings
from app.exceptions import ErroAPI


class VerificadorFake:
    def __init__(self) -> None:
        self.claims_por_token: dict[str, dict[str, Any]] = {}
        self.erros_por_token: dict[str, Exception] = {}

    def adicionar(
        self,
        token: str,
        *,
        uid: str | None = None,
        email: str | None = None,
        nome: str | None = None,
        email_verified: bool = True,
        aud: str | None = None,
        iss: str | None = None,
        **extras: Any,
    ) -> dict[str, Any]:
        identificador = uid or token
        projeto = aud or settings.firebase_project_id
        claims: dict[str, Any] = {
            "uid": identificador,
            "sub": identificador,
            "aud": projeto,
            "iss": iss or f"https://securetoken.google.com/{projeto}",
            "email": email or f"{identificador}@example.com",
            "email_verified": email_verified,
            "name": nome or "Aluno Teste",
        }
        claims.update(extras)
        self.claims_por_token[token] = claims
        return claims

    def verificar(self, token: str) -> dict[str, Any]:
        if token in self.erros_por_token:
            raise self.erros_por_token[token]
        claims = self.claims_por_token.get(token)
        if claims is None:
            raise ErroAPI(401, "TOKEN_INVALIDO", "Token de autenticação inválido.")
        return dict(claims)


def headers_para(fake: VerificadorFake, token: str, **dados: Any) -> dict[str, str]:
    fake.adicionar(token, **dados)
    return {"Authorization": f"Bearer {token}"}
