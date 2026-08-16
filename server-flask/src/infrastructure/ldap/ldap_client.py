def map_ldap_entry_to_user(entry, default_username: str | None = None) -> dict:
    """
    Mapea una entrada LDAP a un diccionario de usuario normalizado.

    Args:
        entry: Entrada devuelta por ldap3.
        default_username: Valor por defecto para el campo username si no está en LDAP.

    Returns:
        dict: Datos normalizados del usuario.
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
