from typing import Any


class ErroAPI(Exception):
    def __init__(
        self,
        status_code: int,
        codigo: str,
        mensagem: str,
        detalhes: Any | None = None,
    ) -> None:
        super().__init__(mensagem)
        self.status_code = status_code
        self.codigo = codigo
        self.mensagem = mensagem
        self.detalhes = detalhes


def nao_autenticado(mensagem: str = "Autenticação necessária.") -> ErroAPI:
    return ErroAPI(401, "NAO_AUTENTICADO", mensagem)


def token_invalido() -> ErroAPI:
    return ErroAPI(401, "TOKEN_INVALIDO", "Token de autenticação inválido.")


def token_expirado() -> ErroAPI:
    return ErroAPI(401, "TOKEN_EXPIRADO", "Sua sessão expirou. Entre novamente.")


def token_revogado() -> ErroAPI:
    return ErroAPI(401, "TOKEN_REVOGADO", "Sua sessão foi revogada. Entre novamente.")


def autenticacao_indisponivel() -> ErroAPI:
    return ErroAPI(
        503,
        "AUTENTICACAO_INDISPONIVEL",
        "Não foi possível validar a autenticação agora. Tente novamente.",
    )


def acesso_negado(mensagem: str = "Acesso restrito ao professor.") -> ErroAPI:
    return ErroAPI(403, "ACESSO_NEGADO", mensagem)


def autenticacao_migrada() -> ErroAPI:
    return ErroAPI(
        410,
        "AUTENTICACAO_MIGRADA",
        "A autenticação por usuário e senha foi substituída pelo Firebase Authentication.",
    )


def codigo_invalido() -> ErroAPI:
    return ErroAPI(400, "CODIGO_INVALIDO", "Código inválido ou expirado.")


def usuario_ja_vinculado() -> ErroAPI:
    return ErroAPI(409, "USUARIO_JA_VINCULADO", "Esta conta já está vinculada a outro acesso.")


def conta_ja_possui_partidas() -> ErroAPI:
    return ErroAPI(
        409,
        "CONTA_JA_POSSUI_PARTIDAS",
        "Esta conta já tem partidas. Fale com o professor antes de vincular.",
    )


def nao_encontrado(mensagem: str = "Partida não encontrada.") -> ErroAPI:
    return ErroAPI(404, "PARTIDA_NAO_ENCONTRADA", mensagem)


def usuario_nao_encontrado() -> ErroAPI:
    return ErroAPI(404, "USUARIO_NAO_ENCONTRADO", "Usuário não encontrado.")
