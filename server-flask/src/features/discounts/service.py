from typing import Dict, Any
from src.utils.formatters import fecha_a_texto_extenso, monto_a_letras
from src.utils.document_builder import build_document

class DiscountDocumentService:
    """
    Servicio dedicado a la generación del Acta de Descuento.
    Actualmente opera sin persistencia en Base de Datos.
    """
    def generate_discount_document(self, payload: Dict[str, Any]) -> dict:
        usuario = payload.get('usuario', {})
        equipos = payload.get('equipos', [])
        mes_descuento = payload.get('deduction_month')

        # Asumimos que el descuento aplica al primer equipo de la lista
        eq = equipos[0]
        
        # Transformamos el valor a entero para usar tu función monto_a_letras
        costo_descuento = eq.get('purchase_cost', 0)

        # Mapeo exacto para tu archivo Word
        context = {
            'actual_date_narrative': fecha_a_texto_extenso(),
            'full_name': usuario.get('full_name', 'NA'),
            'national_id': usuario.get('national_id', 'NA'),
            'discount_month': mes_descuento,
            'text_amount': monto_a_letras(costo_descuento),
            'eq': {
                'quantity': eq.get('quantity', 1),
                'manufacturer': eq.get('manufacturer', 'NA'),
                'model': eq.get('model', 'NA'),
                'serial_number': eq.get('serial_number', 'NA'),
                'purchase_cost': eq.get('purchase_cost', 0)
            }
        }

        # Generar un nombre de archivo dinámico y limpio
        nombre_limpio = usuario.get('username', 'Empleado').replace(' ', '_')
        filename = f"DESCUENTO_{nombre_limpio}_{eq.get('equipment_type')}_{eq.get('serial_number')}.docx"

        # Generar el documento usando el helper global
        doc_data = build_document(
            doc_type="acta_descuento",
            context=context,
            template='descuento_template.docx',
            filename=filename
        )

        return doc_data
