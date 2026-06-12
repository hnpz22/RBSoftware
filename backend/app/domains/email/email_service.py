import logging
from pathlib import Path

import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

_log = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

_TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
_SENDMAIL_URL = "https://graph.microsoft.com/v1.0/users/{sender}/sendMail"


class EmailService:
    """Envío de emails transaccionales del LMS vía Microsoft Graph API.

    Usa el flujo *client credentials* (app-only): obtiene un token con el
    ``graph_client_secret`` y envía el correo como ``graph_sender`` mediante
    el endpoint ``/users/{sender}/sendMail``.

    En entornos sin Graph configurado (``settings.graph_client_secret`` vacío),
    no se intenta enviar nada: el email se loguea en consola para inspección
    durante desarrollo.
    """

    async def _get_token(self) -> str:
        url = _TOKEN_URL.format(tenant=settings.graph_tenant_id)
        data = {
            "client_id": settings.graph_client_id,
            "client_secret": settings.graph_client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, data=data)
            resp.raise_for_status()
            return resp.json()["access_token"]

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

        if not settings.graph_client_secret:
            _log.warning(
                "[EmailService] Graph no configurado (modo dev). Email NO enviado.\n"
                "  Para: %s\n  Asunto: %s\n  Link de contraseña: %s",
                to_email,
                subject,
                reset_link,
            )
            return

        token = await self._get_token()
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": html_body},
                "from": {
                    "emailAddress": {
                        "address": settings.graph_sender,
                        "name": settings.graph_from_name,
                    }
                },
                "toRecipients": [{"emailAddress": {"address": to_email}}],
            },
            "saveToSentItems": False,
        }
        url = _SENDMAIL_URL.format(sender=settings.graph_sender)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
        _log.info("[EmailService] Credenciales enviadas a %s vía Graph", to_email)
