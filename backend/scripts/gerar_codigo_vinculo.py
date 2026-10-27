from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import func, select

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.database import SessionLocal, init_db  # noqa: E402
from app.exceptions import ErroAPI  # noqa: E402
from app.models import Usuario  # noqa: E402
from app.services import vinculo_service  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera um código de vínculo para uma conta legada."
    )
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--usuario", help="Handle do usuário legado")
    grupo.add_argument("--usuario-id", type=int, help="ID do usuário legado")
    parser.add_argument(
        "--criado-por-uid",
        default="cli-professor",
        help="UID do professor que está emitindo o código (auditoria)",
    )
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        if args.usuario_id is not None:
            usuario = db.get(Usuario, args.usuario_id)
        else:
            usuario = db.scalar(
                select(Usuario).where(
                    func.lower(Usuario.usuario) == args.usuario.strip().casefold()
                )
            )
        if usuario is None:
            print("ERRO: usuário não encontrado.", file=sys.stderr)
            return 1
        registro, codigo, alvo = vinculo_service.gerar_codigo(
            db,
            usuario.id,
            args.criado_por_uid,
        )
        print(f"Usuário: {alvo.nome} ({alvo.usuario}, id={alvo.id})")
        print(f"Código: {codigo}")
        print(f"Expira em: {registro.expira_em}")
        print("Entregue individualmente ao aluno. Este código não será exibido novamente.")
        return 0
    except ErroAPI as exc:
        print(f"ERRO: {exc.mensagem}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
