import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.config import settings

ID_RE = re.compile(r"^(0[1-9]|1[0-9]|2[0-2])$")

# Lista oficial privada. Mantida apenas no back-end.
HUMANAS = {"01", "03", "06", "07", "09", "11", "13", "15", "17", "20", "21"}
IAS = {"02", "04", "05", "08", "10", "12", "14", "16", "18", "19", "22"}


class CartaGabarito(BaseModel):
    id: str = Field(pattern=ID_RE.pattern)
    numero: int = Field(ge=1, le=22)
    citacao: str = Field(min_length=20)
    categoria: str = Field(min_length=2)
    tema: str = Field(min_length=2)
    origem: Literal["humano", "ia"]
    analise: str = Field(min_length=20)

    @field_validator("citacao", "categoria", "tema", "analise")
    @classmethod
    def _sem_vazio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("campo não pode ser vazio")
        return valor.strip()


class ArquivoCartas(BaseModel):
    versao: int
    fonte: str
    cartas: list[CartaGabarito]


class CartaPublica(BaseModel):
    id: str
    numero: int
    citacao: str
    categoria: str
    tema: str


class AcervoCartas:
    def __init__(self, cartas: list[CartaGabarito]) -> None:
        self._cartas = {carta.id: carta for carta in cartas}
        self._ordenadas = sorted(cartas, key=lambda carta: carta.numero)

    @property
    def todas(self) -> list[CartaGabarito]:
        return self._ordenadas

    def obter(self, carta_id: str) -> CartaGabarito:
        return self._cartas[carta_id]

    def publicas(self) -> list[CartaPublica]:
        return [
            CartaPublica(
                id=carta.id,
                numero=carta.numero,
                citacao=carta.citacao,
                categoria=carta.categoria,
                tema=carta.tema,
            )
            for carta in self._ordenadas
        ]


def validar_cartas(cartas: list[CartaGabarito]) -> None:
    if len(cartas) != 22:
        raise ValueError(f"esperadas 22 cartas, encontradas {len(cartas)}")
    ids = {carta.id for carta in cartas}
    if len(ids) != 22:
        raise ValueError("IDs de cartas duplicados")
    if ids != set(HUMANAS) | set(IAS):
        raise ValueError("IDs das cartas não correspondem a #01..#22")
    for carta in cartas:
        if carta.numero != int(carta.id):
            raise ValueError(f"numero divergente para a carta {carta.id}")
    humanas = {carta.id for carta in cartas if carta.origem == "humano"}
    ias = {carta.id for carta in cartas if carta.origem == "ia"}
    if humanas != HUMANAS or ias != IAS:
        raise ValueError("origens divergem do gabarito oficial (11 humanas / 11 IA)")


def carregar_cartas(caminho: Path | None = None) -> AcervoCartas:
    arquivo = caminho or settings.cartas_arquivo
    if not arquivo.exists():
        raise RuntimeError(f"arquivo de cartas não encontrado: {arquivo}")
    try:
        bruto = json.loads(arquivo.read_text(encoding="utf-8"))
        dados = ArquivoCartas.model_validate(bruto)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise RuntimeError(f"arquivo de cartas inválido: {exc}") from exc
    validar_cartas(dados.cartas)
    return AcervoCartas(dados.cartas)


_acervo: AcervoCartas | None = None


def inicializar_acervo(caminho: Path | None = None) -> AcervoCartas:
    global _acervo
    _acervo = carregar_cartas(caminho)
    return _acervo


def get_acervo() -> AcervoCartas:
    if _acervo is None:
        raise RuntimeError("acervo de cartas não inicializado")
    return _acervo
