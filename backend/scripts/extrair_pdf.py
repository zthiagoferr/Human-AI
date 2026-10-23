from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader


def main() -> int:
    parser = argparse.ArgumentParser(description="Extrai o texto do PDF das cartas.")
    parser.add_argument("pdf", type=Path, help="Caminho do PDF de origem")
    args = parser.parse_args()

    if not args.pdf.exists():
        raise SystemExit(f"PDF não encontrado: {args.pdf}")

    leitor = PdfReader(str(args.pdf))
    for numero, pagina in enumerate(leitor.pages, start=1):
        print(f"===== PÁGINA {numero} =====")
        print(pagina.extract_text() or "")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
