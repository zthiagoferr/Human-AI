from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import (
    codigo_invalido,
    conta_ja_possui_partidas,
    usuario_ja_vinculado,
    usuario_nao_encontrado,
)
from app.firebase_auth import uid_das_claims
from app.models import CodigoVinculo, Partida, Usuario
from app.security import (
    agora_utc,
    codigo_valido,
    gerar_codigo_vinculo,
    hash_codigo,
    iso_utc,
    normalizar_codigo,
    parse_iso,
)


def _codigo_formatado(codigo: str) -> str:
    return f"{codigo[:5]}-{codigo[5:]}"


def gerar_codigo(
    db: Session,
    usuario_id: int,
    criado_por_uid: str,
) -> tuple[CodigoVinculo, str, Usuario]:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise usuario_nao_encontrado()
    if usuario.firebase_uid is not None:
        raise usuario_ja_vinculado()

    agora = agora_utc()
    ativos = db.scalars(
        select(CodigoVinculo).where(
            CodigoVinculo.usuario_id == usuario.id,
            CodigoVinculo.usado_em.is_(None),
            CodigoVinculo.revogado_em.is_(None),
        )
    ).all()
    for ativo in ativos:
        ativo.revogado_em = iso_utc(agora)

    codigo = gerar_codigo_vinculo()
    registro = CodigoVinculo(
        usuario_id=usuario.id,
        codigo_hash=hash_codigo(codigo),
        criado_em=iso_utc(agora),
        expira_em=iso_utc(agora + timedelta(hours=settings.vinculo_ttl_hours)),
        criado_por_uid=criado_por_uid,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro, _codigo_formatado(codigo), usuario


def _codigo_ativo(db: Session, codigo: str) -> CodigoVinculo:
    normalizado = normalizar_codigo(codigo)
    if not codigo_valido(normalizado):
        raise codigo_invalido()
    registro = db.scalar(
        select(CodigoVinculo).where(CodigoVinculo.codigo_hash == hash_codigo(normalizado))
    )
    if registro is None or registro.usado_em is not None or registro.revogado_em is not None:
        raise codigo_invalido()
    if parse_iso(registro.expira_em) <= agora_utc():
        raise codigo_invalido()
    return registro


def resgatar_codigo(
    db: Session,
    usuario_atual: Usuario,
    claims: dict,
    codigo: str,
) -> Usuario:
    uid = uid_das_claims(claims)
    registro = _codigo_ativo(db, codigo)
    alvo = db.get(Usuario, registro.usuario_id)
    if alvo is None:
        raise codigo_invalido()

    if alvo.firebase_uid is not None:
        if alvo.id == usuario_atual.id and alvo.firebase_uid == uid:
            agora = iso_utc()
            registro.usado_em = agora
            outros = db.scalars(
                select(CodigoVinculo).where(
                    CodigoVinculo.usuario_id == alvo.id,
                    CodigoVinculo.id != registro.id,
                    CodigoVinculo.usado_em.is_(None),
                    CodigoVinculo.revogado_em.is_(None),
                )
            ).all()
            for outro in outros:
                outro.revogado_em = agora
            db.commit()
            return alvo
        raise usuario_ja_vinculado()

    if usuario_atual.firebase_uid != uid:
        raise usuario_ja_vinculado()

    if usuario_atual.id == alvo.id:
        agora = iso_utc()
        alvo.firebase_uid = uid
        registro.usado_em = agora
        db.commit()
        db.refresh(alvo)
        return alvo

    tem_partidas = db.scalar(
        select(Partida.id).where(Partida.usuario_id == usuario_atual.id).limit(1)
    )
    if tem_partidas is not None:
        raise conta_ja_possui_partidas()

    agora = iso_utc()
    usuario_atual.firebase_uid = None
    db.flush()
    alvo.firebase_uid = uid
    registro.usado_em = agora

    outros = db.scalars(
        select(CodigoVinculo).where(
            CodigoVinculo.usuario_id == alvo.id,
            CodigoVinculo.id != registro.id,
            CodigoVinculo.usado_em.is_(None),
            CodigoVinculo.revogado_em.is_(None),
        )
    ).all()
    for outro in outros:
        outro.revogado_em = agora

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise usuario_ja_vinculado() from None
    db.refresh(alvo)
    return alvo


def listar_pendentes(db: Session, limite: int, offset: int) -> tuple[int, list[Usuario]]:
    filtro = Usuario.firebase_uid.is_(None)
    total = db.scalar(select(func.count(Usuario.id)).where(filtro)) or 0
    itens = db.scalars(
        select(Usuario)
        .where(filtro)
        .order_by(Usuario.nome_ordenacao, Usuario.id)
        .limit(limite)
        .offset(offset)
    ).all()
    return int(total), list(itens)
