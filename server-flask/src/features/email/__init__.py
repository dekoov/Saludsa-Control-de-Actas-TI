"""Paquete de envío de correos electrónicos.

Provee una instancia global de EmailService lista para ser importada desde
otros features del backend (por ejemplo, actas). La instancia se configura con
los valores de src.config al momento de su creación.
"""

from src.features.email.service import EmailService

email_service = EmailService()
