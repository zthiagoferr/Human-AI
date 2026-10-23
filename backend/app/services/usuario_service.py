import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.normalizacao import nome_valido, normalizar_nome
from app.exceptions import ErroAPI
from app.firebase_auth import email_das_claims, uid_das_claims
from app.models import SENHA_HASH_INERTE, Usuario
from app.security import iso_utc

_USUARIO_INVALIDO = re.compile(r"[^a-z0-9._-]+")


def _limpar_nome(valor: str) -> str:
    return " ".join(valor.split())


def nome_de_exibicao(claims: dict, nome_informado: str | None = None) -> str:
    candidatos: list[str] = []
    if nome_informado:
        candidatos.append(nome_informado)
    claim_nome = claims.get("name")
    if isinstance(claim_nome, str):
        candidatos.append(claim_nome)

    for candidato in candidatos:
        nome = _limpar_nome(candidato)
        if nome_valido(nome):
            return nome[:80].strip()

    email = email_das_claims(claims)
    if email:
        local = email.split("@", 1)[0]
        local = unicodedata.normalize("NFKD", local)
        local = "".join(c for c in local if not unicodedata.combining(c))
        local = re.sub(r"[^A-Za-z' .-]", " ", local)
        nome = _limpar_nome(local)
        if nome_valido(nome):
            return nome[:80].strip()

    return "Aluno"


def _base_usuario(claims: dict) -> str:
    email = email_das_claims(claims)
    if email:
        base = email.split("@", 1)[0]
    else:
        base = uid_das_claims(claims)

    base = unicodedata.normalize("NFKD", base)
    base = "".join(c for c in base if not unicodedata.combining(c)).lower()
    base = _USUARIO_INVALIDO.sub(".", base)
    base = re.sub(r"[._-]{2,}", ".", base).strip("._-")
    if len(base) < 3:
        base = "aluno"
    if not base[0].isalnum():
        base = f"a{base}"
    return base[:32]


def _candidato_usuario(base: str, indice: int) -> str:
    if indice <= 1:
        return base
    sufixo = f"-{indice}"
    return f"{base[: 32 - len(sufixo)]}{sufixo}"


def _usuario_existe(db: Session, candidato: str) -> bool:
    return db.scalar(select(Usuario.id).where(Usuario.usuario == candidato)) is not None


def obter_por_uid(db: Session, uid: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.firebase_uid == uid))


def obter_ou_criar_por_claims(
    db: Session,
    claims: dict,
    nome_informado: str | None = None,
) -> Usuario:
    uid = uid_das_claims(claims)
    existente = obter_por_uid(db, uid)
    if existente is not None:
        return existente

    nome = nome_de_exibicao(claims, nome_informado)
    base = _base_usuario(claims)

    ultimo_erro: IntegrityError | None = None
    for indice in range(1, 7):
        candidato = _candidato_usuario(base, indice)
        if _usuario_existe(db, candidato):
            continue
        usuario = Usuario(
            nome=nome,
            nome_ordenacao=normalizar_nome(nome),
            usuario=candidato,
            senha_hash=SENHA_HASH_INERTE,
            criado_em=iso_utc(),
            firebase_uid=uid,
        )
        try:
            db.add(usuario)
            db.commit()
            db.refresh(usuario)
            return usuario
        except IntegrityError as exc:
            db.rollback()
            ultimo_erro = exc
            existente = obter_por_uid(db, uid)
            if existente is not None:
                return existente

    raise ErroAPI(
        409,
        "CONFLITO_USUARIO",
        "Não foi possível criar o usuário local. Tente novamente.",
    ) from ultimo_erro


def obter_por_id(db: Session, usuario_id: int) -> Usuario | None:
    return db.get(Usuario, usuario_id)
