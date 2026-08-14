# "~\Code_\Python\Saludsa-Control-de-Actas-TI\server-flask\src\utils\parse_datetime.py" [Modified] line 1 of 12 --8%-- col 2
from datetime import datetime, timezone


def parse_utc_date(date_str: str, is_end_of_day: bool = False) -> datetime:
    """Convierte un string 'YYYY-MM-DD' a un datetime UTC timezone-aware."""
    
    # 1. Nace e inmediatamente le asignamos UTC
    base_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    
    if is_end_of_day:
        # 2. Ya tiene UTC, solo reemplazamos la hora
        return base_date.replace(hour=23, minute=59, second=59)
    
    return base_date
