"""Normaliza entradas de Active Directory a diccionarios de usuario.

Este módulo contiene utilidades para mapear atributos LDAP (como
``sAMAccountName``, ``displayName``, ``mail``, etc.) a un formato uniforme
que el resto de la aplicación puede consumir sin depender de la estructura
interna de ``ldap3``.
"""


def map_ldap_entry_to_user(
    entry: object,
    default_username: str | None = None,
) -> dict[str, str | None]:
    """Mapea una entrada LDAP a un diccionario de usuario normalizado.

    Extrae los atributos más comunes de un objeto devuelto por ``ldap3`` y los
    devuelve en un ``dict`` con claves en snake_case. Si un atributo no está
    presente en la entrada, se retorna ``None`` o ``\"N/A\"`` según corresponda.

    Args:
        entry: Entrada devuelta por ``ldap3`` que permite acceso a atributos
            mediante notación de punto (``entry.atributo``).
        default_username: Valor por defecto para el campo ``username`` si no se
            encuentra ``sAMAccountName`` en la entrada.

    Returns:
        dict[str, str | None]: Datos normalizados del usuario con las claves
        ``first_names``, ``last_names``, ``display_name``, ``full_name``,
        ``username``, ``national_id``, ``department``, ``position``, ``email``,
        ``city`` y ``manager``.
    """
    return {
        "first_names": str(entry.GivenName) if "GivenName" in entry else "N/A",
        "last_names": str(entry.sn) if "sn" in entry else "N/A",
        "display_name": str(entry.displayName) if "displayName" in entry else "N/A",
        "full_name": str(entry.Name) if "Name" in entry else "N/A",
        "username": str(entry.sAMAccountName)
        if "sAMAccountName" in entry
        else default_username,
        "national_id": str(entry.employeeID) if "employeeID" in entry else None,
        "department": str(entry.Department) if "Department" in entry else None,
        "position": str(entry.Description) if "Description" in entry else None,
        "email": str(entry.mail) if "mail" in entry else None,
        "city": str(entry.l) if "l" in entry else None,
        "manager": str(entry.manager) if "manager" in entry else None,
    }