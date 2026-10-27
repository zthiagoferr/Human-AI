from sqlalchemy import inspect
from sqlalchemy.engine import Engine


def aplicar_migracoes(engine: Engine) -> None:
    """Migração idempotente e não destrutiva de SQLite ou PostgreSQL.

    Adiciona firebase_uid a bancos existentes. Nunca remove/atualiza dados.
    """
    dialeto = engine.dialect.name
    with engine.begin() as conn:
        if dialeto == "sqlite":
            tabelas = {
                row[0]
                for row in conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            if "usuarios" not in tabelas:
                return

            colunas = {
                row[1] for row in conn.exec_driver_sql("PRAGMA table_info(usuarios)")
            }
            if "firebase_uid" not in colunas:
                conn.exec_driver_sql("ALTER TABLE usuarios ADD COLUMN firebase_uid TEXT")
        elif dialeto == "postgresql":
            insp = inspect(conn)
            if not insp.has_table("usuarios"):
                return
            colunas = {coluna["name"] for coluna in insp.get_columns("usuarios")}
            if "firebase_uid" not in colunas:
                conn.exec_driver_sql(
                    "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS "
                    "firebase_uid VARCHAR(128)"
                )
        else:
            raise RuntimeError(f"Dialeto de banco não suportado: {dialeto}")

        duplicados = conn.exec_driver_sql(
            "SELECT firebase_uid, COUNT(*) FROM usuarios "
            "WHERE firebase_uid IS NOT NULL GROUP BY firebase_uid HAVING COUNT(*) > 1"
        ).fetchall()
        if duplicados:
            raise RuntimeError(
                "Migração abortada: firebase_uid duplicado. "
                "Corrija manualmente antes de continuar."
            )

        if dialeto == "postgresql":
            duplicados_usuario = conn.exec_driver_sql(
                "SELECT lower(usuario), COUNT(*) FROM usuarios "
                "GROUP BY lower(usuario) HAVING COUNT(*) > 1"
            ).fetchall()
            if duplicados_usuario:
                raise RuntimeError(
                    "Migração abortada: usuario duplicado ignorando maiúsculas. "
                    "Corrija manualmente antes de continuar."
                )
