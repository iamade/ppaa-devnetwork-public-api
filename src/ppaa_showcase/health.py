"""Deterministic dependency health checks (PostgreSQL + Redis)."""

from psycopg import Connection

from .config import settings


def check_postgres(
    host: str | None = None, port: int | None = None, timeout: float = 2.0
) -> tuple[bool, str]:
    """Check PostgreSQL reachability with SELECT 1.

    Returns:
        (ok, detail) tuple; detail carries an error string when not ok.
    """
    conn_info = (
        f"host={host or settings.postgres_host} port={port or settings.postgres_port} "
        f"user={settings.postgres_user} password={settings.postgres_password} "
        f"dbname={settings.postgres_db} connect_timeout={int(timeout)}"
    )
    try:
        with Connection.connect(conn_info) as conn:
            result = conn.execute("SELECT 1").fetchone()
            ok = result is not None and result[0] == 1
            return (ok, "" if ok else "SELECT 1 returned unexpected result")
    except Exception as exc:  # noqa: BLE001 - report any failure as detail
        return (False, f"{type(exc).__name__}: {exc}")


def check_redis(
    host: str | None = None, port: int | None = None, timeout: float = 2.0
) -> tuple[bool, str]:
    """Check Redis reachability with PING.

    Returns:
        (ok, detail) tuple; detail carries an error string when not ok.
    """
    from redis import Redis

    client = Redis(
        host=host or settings.redis_host,
        port=port or settings.redis_port,
        socket_connect_timeout=timeout,
        socket_timeout=timeout,
    )
    try:
        pong = client.ping()
        return (bool(pong), "" if pong else "PING returned falsy")
    except Exception as exc:  # noqa: BLE001 - report any failure as detail
        return (False, f"{type(exc).__name__}: {exc}")
    finally:
        client.close()
