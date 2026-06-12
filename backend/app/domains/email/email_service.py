import logging
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

_log = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


class EmailService:
    """Envío de emails transaccionales del LMS.

    En entornos sin SMTP configurado (``settings.smtp_user`` vacío), no se intenta
    enviar nada: el email se loguea en consola para inspección durante desarrollo.
    """

    def _connection_config(self) -> ConnectionConfig:
        return ConnectionConfig(
            MAIL_USERNAME=settings.smtp_user,
            MAIL_PASSWORD=settings.smtp_password,
            MAIL_FROM=settings.smtp_from_email,
            MAIL_FROM_NAME=settings.smtp_from_name,
            MAIL_PORT=settings.smtp_port,
            MAIL_SERVER=settings.smtp_host,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )

    async def send_credentials(
        self,
        to_email: str,
        first_name: str,
        username: str,
        reset_link: str,
    ) -> None:
        template = _jinja_env.get_template("credentials.html")
        html_body = template.render(
            first_name=first_name,
            username=username,
            reset_link=reset_link,
        )
        subject = "Tus credenciales de acceso a RobotSchool LMS"

        if not settings.smtp_user:
            _log.warning(
                "[EmailService] SMTP no configurado (modo dev). Email NO enviado.\n"
                "  Para: %s\n  Asunto: %s\n  Link de contraseña: %s",
                to_email,
                subject,
                reset_link,
            )
            return

        message = MessageSchema(
            subject=subject,
            recipients=[to_email],
            body=html_body,
            subtype=MessageType.html,
        )
        fast_mail = FastMail(self._connection_config())
        await fast_mail.send_message(message)
        _log.info("[EmailService] Credenciales enviadas a %s", to_email)
