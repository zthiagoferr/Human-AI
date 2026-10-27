from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

SENHA_HASH_INERTE = "!firebase"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    nome_ordenacao: Mapped[str] = mapped_column(String(160), nullable=False)
    usuario: Mapped[str] = mapped_column(
        String(32).with_variant(String(32, collation="NOCASE"), "sqlite"),
        nullable=False,
    )
    senha_hash: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[str] = mapped_column(String(40), nullable=False)
    firebase_uid: Mapped[str | None] = mapped_column(String(128), nullable=True)


class CodigoVinculo(Base):
    __tablename__ = "codigos_vinculo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    codigo_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    criado_em: Mapped[str] = mapped_column(String(40), nullable=False)
    expira_em: Mapped[str] = mapped_column(String(40), nullable=False)
    usado_em: Mapped[str | None] = mapped_column(String(40), nullable=True)
    revogado_em: Mapped[str | None] = mapped_column(String(40), nullable=True)
    criado_por_uid: Mapped[str] = mapped_column(String(128), nullable=False)


class Partida(Base):
    __tablename__ = "partidas"
    __table_args__ = (
        CheckConstraint(
            "status IN ('em_andamento', 'concluida', 'abandonada')",
            name="ck_partidas_status",
        ),
        CheckConstraint("total_perguntas = 22", name="ck_partidas_total"),
        CheckConstraint(
            "duracao_ms IS NULL OR duracao_ms >= 0", name="ck_partidas_duracao"
        ),
        CheckConstraint(
            "acertos IS NULL OR acertos BETWEEN 0 AND 22", name="ck_partidas_acertos"
        ),
        CheckConstraint(
            "erros IS NULL OR erros BETWEEN 0 AND 22", name="ck_partidas_erros"
        ),
        CheckConstraint(
            "(status = 'concluida' AND concluida_em IS NOT NULL "
            "AND duracao_ms IS NOT NULL AND acertos IS NOT NULL "
            "AND erros IS NOT NULL AND acertos + erros = total_perguntas) "
            "OR (status <> 'concluida' AND concluida_em IS NULL "
            "AND duracao_ms IS NULL AND acertos IS NULL AND erros IS NULL)",
            name="ck_partidas_conclusao",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="em_andamento")
    total_perguntas: Mapped[int] = mapped_column(Integer, nullable=False, default=22)
    iniciada_em: Mapped[str] = mapped_column(String(40), nullable=False)
    concluida_em: Mapped[str | None] = mapped_column(String(40), nullable=True)
    duracao_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    acertos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    erros: Mapped[int | None] = mapped_column(Integer, nullable=True)


class PartidaCarta(Base):
    __tablename__ = "partida_cartas"
    __table_args__ = (
        UniqueConstraint("partida_id", "posicao", name="uq_partida_cartas_posicao"),
        UniqueConstraint("partida_id", "carta_id", name="uq_partida_cartas_carta"),
        CheckConstraint("length(carta_id) = 2", name="ck_partida_cartas_id"),
        CheckConstraint("posicao BETWEEN 1 AND 22", name="ck_partida_cartas_posicao"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    partida_id: Mapped[int] = mapped_column(
        ForeignKey("partidas.id", ondelete="CASCADE"), nullable=False
    )
    carta_id: Mapped[str] = mapped_column(String(2), nullable=False)
    posicao: Mapped[int] = mapped_column(Integer, nullable=False)


class Resposta(Base):
    __tablename__ = "respostas"
    __table_args__ = (
        UniqueConstraint("partida_id", "carta_id", name="uq_respostas_partida_carta"),
        CheckConstraint("length(carta_id) = 2", name="ck_respostas_carta_id"),
        CheckConstraint("escolha IN ('humano', 'ia')", name="ck_respostas_escolha"),
        CheckConstraint("correta IN (0, 1)", name="ck_respostas_correta"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    partida_id: Mapped[int] = mapped_column(
        ForeignKey("partidas.id", ondelete="CASCADE"), nullable=False
    )
    carta_id: Mapped[str] = mapped_column(String(2), nullable=False)
    escolha: Mapped[str] = mapped_column(String(10), nullable=False)
    correta: Mapped[int] = mapped_column(Integer, nullable=False)
    respondida_em: Mapped[str] = mapped_column(String(40), nullable=False)
