"""Servicio de envío de correos electrónicos.

Gestiona la configuración SMTP, construye listas de copias, envía correos
mediante smtplib con soporte STARTTLS y fallback a puerto 25, y provee métodos
especializados para notificar al empleado sobre procesos de dotación o
renovación de equipos.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import config
from src.features.email.templates import (
    asunto_dotacion,
    asunto_renovacion,
    cuerpo_dotacion,
    cuerpo_renovacion,
)

# Configure logging
logger = logging.getLogger(__name__)


class EmailService:
    """Servicio para enviar correos electrónicos del sistema.

    Lee la configuración SMTP desde src.config y variables de entorno al
    inicializarse. Permite enviar correos genéricos, de dotación y de
    renovación, incluyendo copias a usuarios configurados y al manager del
    empleado cuando está disponible.

    Attributes:
        smtp_server: Servidor SMTP saliente.
        smtp_port: Puerto SMTP principal.
        smtp_user: Usuario de autenticación SMTP.
        smtp_password: Contraseña de autenticación SMTP.
        from_address: Dirección remitente.
        email_domain: Dominio de correo institucional.
    """

    def __init__(self) -> None:
        """Inicializa el servicio leyendo la configuración del entorno."""
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.smtp_user = config.SALUDSA_USERNAME + "@" + config.EMAIL_DOMAIN
        self.smtp_password = config.SALUDSA_PASSWORD
        self.from_address = config.SMTP_FROM
        self.email_domain = config.EMAIL_DOMAIN

    def is_configured(self) -> bool:
        """Verifica que existan las variables mínimas de configuración SMTP.

        Returns:
            bool: True si servidor, usuario y contraseña están configurados.
        """
        return bool(self.smtp_server and self.smtp_user and self.smtp_password)

    def _build_cc_list(self) -> list[str]:
        """Construye la lista de destinatarios en copia (CC).

        Lee la variable de entorno EMAIL_CC_USERNAMES, espera una lista de
        usuarios separados por coma y retorna direcciones completas con el
        dominio institucional.

        Returns:
            list[str]: Lista de direcciones de correo en copia.
        """
        raw = os.getenv("EMAIL_CC_USERNAMES", "")
        if not raw.strip():
            return []
        usernames = [u.strip() for u in raw.split(",") if u.strip()]
        return [f"{u}@{self.email_domain}" for u in usernames]

    def _send(self, to: str, cc: list[str], subject: str, body: str) -> bool:
        """Envía un correo electrónico a través de SMTP.

        Intenta primero enviar mediante STARTTLS en el puerto configurado. Si
        falla, intenta un fallback sin TLS en el puerto 25. Cualquier error se
        registra y la función retorna False sin lanzar excepciones.

        Args:
            to: Dirección de correo del destinatario principal.
            cc: Lista de direcciones en copia.
            subject: Asunto del correo.
            body: Cuerpo del mensaje en texto plano.

        Returns:
            bool: True si el envío fue exitoso, False en caso contrario.
        """
        if not self.is_configured():
            logger.warning("EmailService: SMTP not configured — email skipped.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_address
            msg["To"] = to
            msg["CC"] = ", ".join(cc)
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            all_recipients = [to] + cc

            # Try STARTTLS on port 587 first
            try:
                with smtplib.SMTP(
                    self.smtp_server, self.smtp_port, timeout=10
                ) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.from_address, all_recipients, msg.as_string())
                    logger.info(f"Email sent to {to} — Subject: {subject}")
                    return True

            except smtplib.SMTPException:
                # Fallback: try without TLS on port 25
                with smtplib.SMTP(self.smtp_server, 25, timeout=10) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.from_address, all_recipients, msg.as_string())
                    logger.info(f"Email sent (fallback port 25) to {to}")
                    return True

        except Exception as e:
            logger.error(f"EmailService: failed to send email to {to}: {e!s}")
            return False

    def send_dotacion_email(
        self,
        username: str,
        full_name: str,
        tecnico_nombre: str,
        manager_email: str | None = None,
    ) -> bool:
        """Envía el correo de solicitud de datos para un proceso de dotación.

        Args:
            username: Nombre de usuario del empleado destinatario.
            full_name: Nombre completo del empleado.
            tecnico_nombre: Nombre del técnico responsable.
            manager_email: Correo del jefe inmediato para copia (opcional).

        Returns:
            bool: True si el correo fue enviado exitosamente.
        """
        cc = self._build_cc_list()
        if manager_email:
            cc.append(manager_email)
        to = f"{username}@{self.email_domain}"
        subject = asunto_dotacion(username)
        body = cuerpo_dotacion(full_name, tecnico_nombre)
        return self._send(to, cc, subject, body)

    def send_renovacion_email(
        self,
        username: str,
        full_name: str,
        tecnico_nombre: str,
        manager_email: str | None = None,
    ) -> bool:
        """Envía el correo de solicitud de datos para un proceso de renovación.

        Args:
            username: Nombre de usuario del empleado destinatario.
            full_name: Nombre completo del empleado.
            tecnico_nombre: Nombre del técnico responsable.
            manager_email: Correo del jefe inmediato para copia (opcional).

        Returns:
            bool: True si el correo fue enviado exitosamente.
        """
        cc = self._build_cc_list()
        if manager_email:
            cc.append(manager_email)
        to = f"{username}@{self.email_domain}"
        subject = asunto_renovacion(username)
        body = cuerpo_renovacion(full_name, tecnico_nombre)
        return self._send(to, cc, subject, body)
