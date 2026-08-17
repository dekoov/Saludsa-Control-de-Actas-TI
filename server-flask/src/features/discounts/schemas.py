"""Esquemas y validaciones para actas de descuento.

Este módulo valida el payload necesario para generar un acta de descuento por
equipo entregado: datos mínimos del usuario, mes de descuento y campos
obligatorios del equipo con costo positivo.
"""

from typing import Any

from src.core.exceptions import ValidationError


def validate_discount_payload(data: dict[str, Any] | None) -> dict[str, Any]:
    """Valida el payload para generar un acta de descuento.

    Revisa que existan usuario con nombre completo y cédula, mes de descuento,
    al menos un equipo, y que cada equipo tenga los campos obligatorios con un
    costo de compra mayor a cero.

    Args:
        data: Payload JSON recibido desde el cliente.

    Returns:
        dict[str, Any]: El mismo payload validado.

    Raises:
        ValidationError: Si falta algún campo obligatorio, los tipos son
            incorrectos o el costo no es positivo.
    """
    usuario = data.get("usuario")
    equipos = data.get("equipos")

    if not usuario or not usuario.get("full_name") or not usuario.get("national_id"):
        raise ValidationError(
            "El usuario debe tener 'full_name' y 'national_id' (Cédula)."
        )

    if not data.get("deduction_month"):
        raise ValidationError("El mes de descuento ('deduction_month') es obligatorio.")

    if not equipos or len(equipos) == 0:
        raise ValidationError("Debe incluir al menos un equipo a descontar.")

    for i, eq in enumerate(equipos):
        # Campos mínimos para el descuento
        required_fields = [
            "equipment_type",
            "manufacturer",
            "model",
            "serial_number",
            "purchase_cost",
        ]
        for req in required_fields:
            if req not in eq or str(eq[req]).strip() == "":
                raise ValidationError(
                    f"El campo '{req}' es obligatorio para el equipo #{i + 1}."
                )

        if eq["purchase_cost"] <= 0:
            raise ValidationError(
                f"El valor a descontar debe ser mayor a 0 (equipo #{i + 1})."
            )

    return data
