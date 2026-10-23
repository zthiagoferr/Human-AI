from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from app.domain.cartas import CartaPublica
from app.domain.normalizacao import nome_valido


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class SessaoRequest(BaseSchema):
    nome: str | None = None

    @field_validator("nome")
    @classmethod
    def _nome(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        valor = " ".join(valor.split())
        if not nome_valido(valor):
            raise ValueError(
                "O nome deve ter 3 a 80 caracteres, conter letras e usar apenas letras, "
                "espaços, apóstrofo, hífen ou ponto."
            )
        return valor


class VincularRequest(BaseSchema):
    codigo: str = Field(min_length=4, max_length=40)

    @field_validator("codigo")
    @classmethod
    def _codigo(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("Informe o código.")
        return valor


class UsuarioPublico(BaseSchema):
    id: int
    nome: str
    usuario: str


class SessaoResponse(BaseSchema):
    usuario: UsuarioPublico
    papel: Literal["aluno", "professor"]


class UsuarioResponse(SessaoResponse):
    pass


class UsuarioPendente(BaseSchema):
    id: int
    nome: str
    usuario: str
    criado_em: str


class PendentesResponse(BaseSchema):
    total: int
    limite: int
    offset: int
    itens: list[UsuarioPendente]


class CodigoGeradoResponse(BaseSchema):
    codigo: str
    expira_em: str
    usuario: UsuarioPublico


class PartidaPublica(BaseSchema):
    id: int
    iniciada_em: str
    total_perguntas: int
    cartas: list[CartaPublica]


class PartidaResponse(BaseSchema):
    partida: PartidaPublica | None


class RespostaItem(BaseSchema):
    carta_id: str = Field(pattern=r"^(0[1-9]|1[0-9]|2[0-2])$")
    escolha: str = Field(pattern=r"^(humano|ia)$")


class RespostasRequest(BaseSchema):
    respostas: list[RespostaItem]


class CorrecaoItem(BaseSchema):
    numero: int
    carta_id: str
    citacao: str
    categoria: str
    tema: str
    escolha_aluno: str
    resposta_correta: str
    acertou: bool
    analise: str


class ResultadoPartida(BaseSchema):
    partida_id: int
    total_perguntas: int
    acertos: int
    erros: int
    percentual: float
    duracao_ms: int
    iniciada_em: str
    concluida_em: str
    correcao: list[CorrecaoItem]


class RankingItem(BaseSchema):
    posicao: int
    usuario_id: int
    nome: str
    acertos: int
    erros: int
    duracao_ms: int
    concluida_em: str


class RankingResponse(BaseSchema):
    atualizado_em: str
    total_participantes: int
    limite: int
    offset: int
    itens: list[RankingItem]
    meu_resultado: RankingItem | None


class HealthResponse(BaseSchema):
    status: str
    versao: str
    cartas_carregadas: int


class ErroDetalhe(BaseSchema):
    campo: str | None = None
    mensagem: str


class ErroCorpo(BaseSchema):
    codigo: str
    mensagem: str
    detalhes: object | None = None


class ErroResponse(BaseSchema):
    erro: ErroCorpo
