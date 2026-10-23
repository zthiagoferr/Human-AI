from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.domain.cartas import carregar_cartas  # noqa: E402


def main() -> int:
    try:
        acervo = carregar_cartas()
    except Exception as exc:  # noqa: BLE001
        print(f"ERRO: {exc}")
        return 1
    humanas = sum(1 for carta in acervo.todas if carta.origem == "humano")
    ias = 22 - humanas
    print(f"OK: {len(acervo.todas)} cartas validadas ({humanas} humanas, {ias} de IA).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
