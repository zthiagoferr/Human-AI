import hashlib
import re
import secrets
from datetime import datetime, timezone

CODIGO_RE = re.compile(r"^[A-F0-9]{10}$")


def agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(momento: datetime | None = None) -> str:
    return (momento or agora_utc()).isoformat()


def parse_iso(valor: str) -> datetime:
    momento = datetime.fromisoformat(valor)
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento


def gerar_codigo_vinculo() -> str:
    return secrets.token_hex(5).upper()


def normalizar_codigo(codigo: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", codigo.upper())


def codigo_valido(codigo: str) -> bool:
    return bool(CODIGO_RE.fullmatch(codigo))


def hash_codigo(codigo: str) -> str:
    return hashlib.sha256(normalizar_codigo(codigo).encode("utf-8")).hexdigest()
