from uuid import UUID

from fastapi import HTTPException


def parse_public_id(value: str, *, detail: str = "Identificador inválido") -> UUID:
    """Convierte un string a UUID; lanza HTTP 400 si el formato es inválido."""
    try:
        return UUID(value)
    except (ValueError, TypeError):
        raise HTTPException(400, detail)
