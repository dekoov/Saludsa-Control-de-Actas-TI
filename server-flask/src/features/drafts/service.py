from datetime import datetime

def generate_draft_title(usuario  , equipos):
    """Genera título automático para el borrador"""
    nombre = usuario.get('full_name', 'Usuario')
    
    if not equipos or len(equipos) == 0:
        return f"{nombre} - Sin equipos - {datetime.now().strftime('%d/%m %H:%M')}"
    
    # Si hay un solo equipo principal (laptop)
    if len(equipos) == 1:
        eq = equipos[0]
        tipo = eq.get('equipment_type', 'Equipo')
        marca = eq.get('manufacturer', '')
        return f"{nombre} - {tipo} {marca} - {datetime.now().strftime('%d/%m %H:%M')}"
    
    # Si hay múltiples equipos
    tipos = [eq.get('equipment_type', 'Equipo') for eq in equipos]
    if len(tipos) == 2:
        return f"{nombre} - {tipos[0]} + {tipos[1]} - {datetime.now().strftime('%d/%m')}"
    else:
        return f"{nombre} - {tipos[0]} + {len(tipos)-1} accesorios - {datetime.now().strftime('%d/%m')}"
