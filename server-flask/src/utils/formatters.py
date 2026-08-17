from datetime import datetime
from num2words import num2words

MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

DAYS_ES = [
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"
]

# Diccionario de mapeo de ciudades
CITY_MAP = {
    "GYE": "Guayaquil",
    "CUE": "Cuenca",
    "UIO": "Quito",
    "MAC": "Machala",
    "MAN": "Manta"
}

def fecha_a_texto_extenso(fecha=None):
    """
    Convierte objeto fecha a formato narrativo completo.
    Ejemplo: 'martes, 16 de junio del 2026'
    """
    if fecha is None:
        fecha = datetime.now()
    
    # fecha.weekday() devuelve un entero de 0 (lunes) a 6 (domingo)
    dia_semana = DAYS_ES[fecha.weekday()]
    mes_minusculas = MONTHS_ES[fecha.month - 1]
    
    return f"{dia_semana}, {fecha.day} de {mes_minusculas} del {fecha.year}"

def fecha_a_texto_legal(fecha=None):
    """
    Convierte la fecha al formato legal: '14, ABRIL, 2026'
    Usa la lista MONTHS_ES en minúsculas y la transforma en el return.
    """
    if fecha is None:
        fecha = datetime.now()
    
    # 1. Buscamos el mes en tu lista (sale en minúsculas)
    mes_minusculas = MONTHS_ES[fecha.month - 1]
    
    # 2. Lo transformamos a MAYÚSCULAS en el return usando .upper()
    return f"{fecha.day}, {mes_minusculas.upper()}, {fecha.year}"

def ubicacion_a_letras(codigo_ad):
    """
    Convierte códigos de oficina (GYE, UIO, etc.) a nombres completos.
    Si el código no existe en el mapa, devuelve el código original.
    """
    if not codigo_ad:
        return "Ubicación no especificada"
        
    # .upper() por si acaso el AD lo devuelve en minúsculas
    codigo = codigo_ad.upper().strip()
    
    return CITY_MAP.get(codigo, codigo)

def fecha_a_texto(fecha=None):
    """Convierte objeto fecha a '13 de Abril del 2026'"""
    if fecha is None:
        fecha = datetime.now()
    
    return f"{fecha.day} de {MONTHS_ES[fecha.month - 1].capitalize()} del {fecha.year}"

def monto_a_letras(monto, incluir_centavos=True):
    """
    Convierte un valor numérico a texto legal en dólares y centavos.
    Ejemplo: 12.50 -> 'DOCE DÓLARES CON CINCUENTA CENTAVOS'
    """
    monto_str = f"{float(monto):.2f}"
    entero_str, decimal_str = monto_str.split('.')
    
    entero = int(entero_str)
    centavos = int(decimal_str)
    
    if entero == 1:
        texto_dolares = "UN DÓLAR"
    else:
        letras_entero = num2words(entero, lang='es').upper()
        if letras_entero.endswith("UNO"):
            letras_entero = letras_entero[:-1] # Eliminamos la 'O'
        texto_dolares = f"{letras_entero} DÓLARES"
        
    if centavos == 0:
        texto_centavos = "CERO CENTAVOS"
    elif centavos == 1:
        texto_centavos = "UN CENTAVO"
    else:
        letras_decimal = num2words(centavos, lang='es').upper()
        if letras_decimal.endswith("UNO"):
            letras_decimal = letras_decimal[:-1]
        texto_centavos = f"{letras_decimal} CENTAVOS"
        
    return f"{texto_dolares} CON {texto_centavos}"
