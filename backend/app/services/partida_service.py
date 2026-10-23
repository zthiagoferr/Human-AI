from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.cartas import CartaPublica, get_acervo
from app.exceptions import ErroAPI, nao_encontrado
from app.models import Partida, PartidaCarta, Resposta, Usuario
from app.schemas import (
    CorrecaoItem,
    PartidaPublica,
    RespostaItem,
    ResultadoPartida,
)
from app.security import agora_utc, iso_utc, parse_iso

TOTAL = 22


def _publica(db: Session, partida: Partida) -> PartidaPublica:
    cartas_ids = db.scalars(
        select(PartidaCarta.carta_id)
        .where(PartidaCarta.partida_id == partida.id)
        .order_by(PartidaCarta.posicao)
    ).all()
    acervo = get_acervo()
    cartas = [
        CartaPublica(
            id=carta.id,
            numero=carta.numero,
            citacao=carta.citacao,
            categoria=carta.categoria,
            tema=carta.tema,
        )
        for carta in (acervo.obter(carta_id) for carta_id in cartas_ids)
    ]
    return PartidaPublica(
        id=partida.id,
        iniciada_em=partida.iniciada_em,
        total_perguntas=partida.total_perguntas,
        cartas=cartas,
    )


def obter_atual(db: Session, usuario: Usuario) -> PartidaPublica | None:
    partida = db.scalar(
        select(Partida).where(
            Partida.usuario_id == usuario.id,
            Partida.status == "em_andamento",
        )
    )
    if partida is None:
        return None
    return _publica(db, partida)


def iniciar(db: Session, usuario: Usuario) -> PartidaPublica:
    ativa = db.scalar(
        select(Partida).where(
            Partida.usuario_id == usuario.id,
            Partida.status == "em_andamento",
        )
    )
    if ativa is not None:
        raise ErroAPI(
            409,
            "PARTIDA_EM_ANDAMENTO",
            "Já existe uma partida em andamento.",
            {"partidaId": ativa.id},
        )
    partida = Partida(
        usuario_id=usuario.id,
        status="em_andamento",
        total_perguntas=TOTAL,
        iniciada_em=iso_utc(),
    )
    try:
        db.add(partida)
        db.flush()
        for posicao, carta in enumerate(get_acervo().todas, start=1):
            db.add(
                PartidaCarta(
                    partida_id=partida.id,
                    carta_id=carta.id,
                    posicao=posicao,
                )
            )
        db.commit()
        db.refresh(partida)
    except IntegrityError as exc:
        db.rollback()
        ativa = db.scalar(
            select(Partida).where(
                Partida.usuario_id == usuario.id,
                Partida.status == "em_andamento",
            )
        )
        if ativa is not None:
            raise ErroAPI(
                409,
                "PARTIDA_EM_ANDAMENTO",
                "Já existe uma partida em andamento.",
                {"partidaId": ativa.id},
            ) from exc
        raise
    return _publica(db, partida)


def abandonar(db: Session, usuario: Usuario, partida_id: int) -> None:
    partida = db.scalar(
        select(Partida).where(
            Partida.id == partida_id,
            Partida.usuario_id == usuario.id,
        )
    )
    if partida is None:
        raise nao_encontrado()
    if partida.status == "abandonada":
        return
    if partida.status != "em_andamento":
        raise ErroAPI(
            409,
            "PARTIDA_NAO_ESTA_EM_ANDAMENTO",
            "Somente uma partida em andamento pode ser abandonada.",
        )
    partida.status = "abandonada"
    db.commit()


def _montar_resultado(db: Session, partida: Partida) -> ResultadoPartida:
    if (
        partida.concluida_em is None
        or partida.duracao_ms is None
        or partida.acertos is None
        or partida.erros is None
    ):
        raise RuntimeError("partida concluída sem dados de conclusão")
    linhas = db.execute(
        select(PartidaCarta, Resposta)
        .join(Resposta, Resposta.carta_id == PartidaCarta.carta_id)
        .where(
            PartidaCarta.partida_id == partida.id,
            Resposta.partida_id == partida.id,
        )
        .order_by(PartidaCarta.posicao)
    ).all()
    if len(linhas) != TOTAL:
        raise RuntimeError("quantidade de respostas inconsistente")
    acervo = get_acervo()
    correcao: list[CorrecaoItem] = []
    for partida_carta, resposta in linhas:
        carta = acervo.obter(partida_carta.carta_id)
        correcao.append(
            CorrecaoItem(
                numero=carta.numero,
                carta_id=carta.id,
                citacao=carta.citacao,
                categoria=carta.categoria,
                tema=carta.tema,
                escolha_aluno=resposta.escolha,
                resposta_correta=carta.origem,
                acertou=bool(resposta.correta),
                analise=carta.analise,
            )
        )
    return ResultadoPartida(
        partida_id=partida.id,
        total_perguntas=partida.total_perguntas,
        acertos=partida.acertos,
        erros=partida.erros,
        percentual=round(partida.acertos / partida.total_perguntas * 100, 1),
        duracao_ms=partida.duracao_ms,
        iniciada_em=partida.iniciada_em,
        concluida_em=partida.concluida_em,
        correcao=correcao,
    )


def obter_resultado(db: Session, usuario: Usuario, partida_id: int) -> ResultadoPartida:
    partida = db.scalar(
        select(Partida).where(
            Partida.id == partida_id,
            Partida.usuario_id == usuario.id,
        )
    )
    if partida is None:
        raise nao_encontrado()
    if partida.status != "concluida":
        raise ErroAPI(
            409,
            "PARTIDA_NAO_CONCLUIDA",
            "A partida ainda não foi concluída.",
        )
    return _montar_resultado(db, partida)


def responder(
    db: Session,
    usuario: Usuario,
    partida_id: int,
    respostas: list[RespostaItem],
) -> ResultadoPartida:
    partida = db.scalar(
        select(Partida).where(
            Partida.id == partida_id,
            Partida.usuario_id == usuario.id,
        )
    )
    if partida is None:
        raise nao_encontrado()
    if partida.status == "concluida":
        return _montar_resultado(db, partida)
    if partida.status != "em_andamento":
        raise ErroAPI(
            409,
            "PARTIDA_NAO_ESTA_EM_ANDAMENTO",
            "A partida não está em andamento.",
        )

    esperadas = list(
        db.scalars(
            select(PartidaCarta.carta_id)
            .where(PartidaCarta.partida_id == partida.id)
            .order_by(PartidaCarta.posicao)
        ).all()
    )
    if len(respostas) != TOTAL:
        raise ErroAPI(
            422,
            "RESPOSTAS_INCOMPLETAS",
            f"Envie exatamente {TOTAL} respostas.",
            {"recebidas": len(respostas)},
        )
    recebidas = [item.carta_id for item in respostas]
    if len(set(recebidas)) != TOTAL:
        raise ErroAPI(422, "RESPOSTA_DUPLICADA", "Há cartas respondidas mais de uma vez.")
    if set(recebidas) != set(esperadas):
        raise ErroAPI(
            422,
            "CARTA_FORA_DA_PARTIDA",
            "As respostas devem corresponder exatamente às cartas da partida.",
        )

    acervo = get_acervo()
    acertos = sum(
        1 for item in respostas if acervo.obter(item.carta_id).origem == item.escolha
    )
    fim = agora_utc()
    inicio = parse_iso(partida.iniciada_em)
    duracao_ms = max(0, int((fim - inicio).total_seconds() * 1000))
    try:
        for item in respostas:
            carta = acervo.obter(item.carta_id)
            db.add(
                Resposta(
                    partida_id=partida.id,
                    carta_id=item.carta_id,
                    escolha=item.escolha,
                    correta=1 if carta.origem == item.escolha else 0,
                    respondida_em=iso_utc(fim),
                )
            )
        partida.status = "concluida"
        partida.concluida_em = iso_utc(fim)
        partida.duracao_ms = duracao_ms
        partida.acertos = acertos
        partida.erros = TOTAL - acertos
        db.commit()
    except IntegrityError:
        db.rollback()
        partida = db.scalar(
            select(Partida).where(
                Partida.id == partida_id,
                Partida.usuario_id == usuario.id,
            )
        )
        if partida is not None and partida.status == "concluida":
            return _montar_resultado(db, partida)
        raise
    db.refresh(partida)
    return _montar_resultado(db, partida)
