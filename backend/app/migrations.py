from sqlalchemy.engine import Engine


def aplicar_migracoes(engine: Engine) -> None:
    """Migração idempotente e não destrutiva do SQLite.

    Adiciona firebase_uid a bancos existentes. Nunca remove/atualiza dados.
    """
    with engine.begin() as conn:
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

        duplicados = conn.exec_driver_sql(
            "SELECT firebase_uid, COUNT(*) FROM usuarios "
            "WHERE firebase_uid IS NOT NULL GROUP BY firebase_uid HAVING COUNT(*) > 1"
        ).fetchall()
        if duplicados:
            raise RuntimeError(
                "Migração abortada: firebase_uid duplicado. "
                "Corrija manualmente antes de continuar."
            )
