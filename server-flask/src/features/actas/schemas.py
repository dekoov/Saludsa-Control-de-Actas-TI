from src.core.exceptions import ValidationError
from typing import Dict, Any, List
from src.models.enums import EquipmentType, EquipmentStatus

def validate_acta_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Valida que el payload para crear un acta tenga la estructura correcta."""
    usuario = data.get('usuario')
    equipos = data.get('equipos')

    if not usuario or not isinstance(usuario, dict):
        raise ValidationError("El campo 'usuario' es requerido y debe ser un objeto.")
    if not usuario or not usuario.get('username'):
        raise ValidationError("El campo 'username' es requerido.")

    if not equipos or not isinstance(equipos, list) or len(equipos) == 0:
        raise ValidationError("El campo 'equipos' es requerido y debe ser una lista no vacía.")

    # 1. Validaciones universales
    for i, eq in enumerate(equipos):
        required_fields = ['equipment_type', 'manufacturer', 'model', 'serial_number', 'purchase_cost', 'status']
        for req in required_fields:
            if req not in eq or str(eq[req]).strip() == "":
                raise ValidationError(f"El campo '{req}' es obligatorio para el equipo #{i+1}.")
        if eq['quantity'] <= 0:
            raise ValidationError(f"La cantidad debe ser un número positivo para el equipo #{i+1}.")

        if int(eq.get('purchase_cost', 0)) <= 0:
            raise ValidationError(f"El costo de compra debe ser un número positivo para el equipo #{i+1}.")

        # 2. .Validaciones de categorias
        type = eq['equipment_type']
        if type == EquipmentType.LAPTOP.value:
            if not eq['serial_number'] or eq['serial_number'].strip() == "":
                raise ValidationError(f"Una Laptop DEBE tener número de serie (equipo #{i+1}).")
            if not eq['model'] or eq['model'].strip() == "":
                raise ValidationError(f"Una Laptop DEBE tener modelo (equipo #{i+1}).")
            if 'hostname' not in eq or eq['hostname'].strip() == "":
                raise ValidationError(f"Una Laptop DEBE tener un Hostname asignado (equipo #{i+1}).")

        elif type in [EquipmentType.CARGADOR.value, EquipmentType.DIADEMA.value]:
            if not eq['model']:
                raise ValidationError(f"El accesorio {type} requiere un modelo (equipo #{i+1}).")
            if not eq['serial_number'] or eq['serial_number'].strip() == "":
                eq['serial_number'] = "NA"

        elif type == EquipmentType.MOCHILA.value:
            if not eq['model']:
                eq['model'] = "Genérico"
            if not eq['serial_number']:
                eq['serial_number'] = "NA"

    return data
