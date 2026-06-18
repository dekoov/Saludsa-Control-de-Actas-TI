import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from src.features.email.templates import asunto_dotacion, cuerpo_dotacion, asunto_renovacion, cuerpo_renovacion

# Configure logging
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Read config from env — NO hardcoding
        self.smtp_server   = os.getenv("SMTP_SERVER")
        self.smtp_port     = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user     = os.getenv("SALUDSA_USERNAME") + "@" + os.getenv("EMAIL_DOMAIN", "saludsa.com.ec")
        self.smtp_password = os.getenv("SALUDSA_PASSWORD")
        self.from_address  = os.getenv("SMTP_FROM", self.smtp_user)
        self.email_domain  = os.getenv("EMAIL_DOMAIN", "saludsa.com.ec")

    def is_configured(self) -> bool:
        """Verifies that minimum variables are present."""
        return bool(self.smtp_server and self.smtp_user and self.smtp_password)

    def _build_cc_list(self) -> list[str]:
        """Builds CC list from EMAIL_CC_USERNAMES."""
        raw = os.getenv("EMAIL_CC_USERNAMES", "")
        if not raw.strip():
            return []
        usernames = [u.strip() for u in raw.split(",") if u.strip()]
        return [f"{u}@{self.email_domain}" for u in usernames]

    def _send(self, to: str, cc: list[str], subject: str, body: str) -> bool:
        """Private method to manage SMTP connection and actual sending."""
        if not self.is_configured():
            logger.warning("EmailService: SMTP not configured — email skipped.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"]    = self.from_address
            msg["To"]      = to
            msg["CC"]      = ", ".join(cc)
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            all_recipients = [to] + cc

            # Try STARTTLS on port 587 first
            try:
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
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
            logger.error(f"EmailService: failed to send email to {to}: {str(e)}")
            return False

    def send_dotacion_email(self, username: str, full_name: str, tecnico_nombre: str) -> bool:
        """Sends data request email for dotación."""
        cc = self._build_cc_list()
        to = f"{username}@{self.email_domain}"
        subject = asunto_dotacion(username)
        body = cuerpo_dotacion(full_name, tecnico_nombre)
        return self._send(to, cc, subject, body)

    def send_renovacion_email(self, username: str, full_name: str, tecnico_nombre: str) -> bool:
        """Sends data request email for renovación."""
        cc = self._build_cc_list()
        to = f"{username}@{self.email_domain}"
        subject = asunto_renovacion(username)
        body = cuerpo_renovacion(full_name, tecnico_nombre)
        return self._send(to, cc, subject, body)
