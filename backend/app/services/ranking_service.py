from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas import RankingItem, RankingResponse
from app.security import iso_utc

_SELECT = """
SELECT posicao, usuario_id, nome, acertos, erros, duracao_ms, concluida_em
FROM vw_ranking
ORDER BY posicao
LIMIT :limite OFFSET :offset
"""

_SELECT_ME = """
SELECT posicao, usuario_id, nome, acertos, erros, duracao_ms, concluida_em
FROM vw_ranking
WHERE usuario_id = :usuario_id
"""


def _item(linha) -> RankingItem:  # type: ignore[no-untyped-def]
    return RankingItem(
        posicao=int(linha["posicao"]),
        usuario_id=int(linha["usuario_id"]),
        nome=linha["nome"],
        acertos=int(linha["acertos"]),
        erros=int(linha["erros"]),
        duracao_ms=int(linha["duracao_ms"]),
        concluida_em=linha["concluida_em"],
    )


def obter_ranking(
    db: Session,
    usuario_id: int,
    limite: int,
    offset: int,
) -> RankingResponse:
    total = db.execute(text("SELECT COUNT(*) FROM vw_ranking")).scalar_one()
    linhas = db.execute(
        text(_SELECT), {"limite": limite, "offset": offset}
    ).mappings().all()
    meu = db.execute(text(_SELECT_ME), {"usuario_id": usuario_id}).mappings().first()
    return RankingResponse(
        atualizado_em=iso_utc(),
        total_participantes=int(total),
        limite=limite,
        offset=offset,
        itens=[_item(linha) for linha in linhas],
        meu_resultado=_item(meu) if meu is not None else None,
    )
