def asunto_dotacion(username: str) -> str:
    return f"Dotación de equipo :: {username}"

def asunto_renovacion(username: str) -> str:
    return f"Renovación de equipo :: {username}"

def cuerpo_dotacion(full_name: str, tecnico_nombre: str) -> str:
    return f"""Estimado/a {full_name},

Le informamos que el área de TI ha iniciado el proceso de dotación de su nuevo equipo de cómputo.

Para proceder con la asignación formal, le solicitamos completar la siguiente información
respondiendo directamente a este correo:

  • Nombres Completos:
  • Usuario:
  • Número de Cédula:
  • Dirección de domicilio:
  • Teléfono de contacto:
  • Correo personal (no institucional):

Adicionalmente, por favor envíe su clave de acceso a través de Microsoft Teams al técnico
responsable de su asignación: {tecnico_nombre}.

Agradecemos su colaboración con este proceso.

Atentamente,
Área de Tecnología — Saludsa"""

def cuerpo_renovacion(full_name: str, tecnico_nombre: str) -> str:
    return f"""Estimado/a {full_name},

Le informamos que su equipo de cómputo será renovado como parte del plan de actualización tecnológica

Para gestionar correctamente la entrega de su nuevo equipo, le solicitamos
completar la siguiente información respondiendo a este correo:

  • Nombres Completos:
  • Usuario:
  • Número de Cédula:
  • Dirección de domicilio:
  • Teléfono de contacto:
  • Correo personal (no institucional):

Por favor envíe también su clave de acceso a través de Microsoft Teams a {tecnico_nombre}.

Agradecemos su colaboración.

Atentamente,
Área de Tecnología — Saludsa"""
