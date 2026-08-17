"""Utilidades para parsear y manipular fechas con zona horaria UTC.

Este módulo proporciona funciones auxiliares para convertir cadenas de texto
en objetos ``datetime`` conscientes de zona horaria, garantizando que todas
las fechas se manejen en UTC.
"""

from datetime import datetime, timezone


def parse_utc_date(date_str: str, is_end_of_day: bool = False) -> datetime:
    """Convierte una cadena ``YYYY-MM-DD`` en un ``datetime`` UTC-aware.

    Args:
        date_str: Fecha en formato ``YYYY-MM-DD``.
        is_end_of_day: Si es ``True``, ajusta la hora a ``23:59:59`` en lugar
            de dejarla en ``00:00:00``.

    Returns:
        Objeto ``datetime`` con zona horaria UTC.

    Example:
        >>> parse_utc_date("2026-08-16", is_end_of_day=True)
        datetime.datetime(2026, 8, 16, 23, 59, 59, tzinfo=datetime.timezone.utc)
    """
    # 1. Nace e inmediatamente le asignamos UTC
    base_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    if is_end_of_day:
        # 2. Ya tiene UTC, solo reemplazamos la hora
        return base_date.replace(hour=23, minute=59, second=59)

    return base_date
