"""Tests de _validate_token — validación del id_token SSO que el portal releva al LMS.

Cubre la brecha cerrada en fix/sso-jwt-validation:
- match ESTRICTO por kid (sin fallback a jwks[0]),
- verificación de aud (rechaza tokens con otra audiencia, p. ej. access tokens),
- verificación de iss cuando settings.sso_issuer está configurado.
"""
from __future__ import annotations

import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jose import jwk, jwt

from app.core.config import settings
from app.domains.auth.routes import sso

_KID = "test-kid-1"


def _keypair() -> tuple[str, dict]:
    """Genera un par RSA y devuelve (private_pem, jwk_dict_publico con kid)."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    pub = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    jwk_dict = jwk.construct(pub, "RS256").to_dict()
    jwk_dict["kid"] = _KID
    return priv, jwk_dict


def _mint(priv: str, *, aud: str = "portal", iss: str | None = None, kid: str = _KID) -> str:
    now = int(time.time())
    claims = {"email": "user@example.com", "aud": aud, "iat": now, "exp": now + 300}
    if iss is not None:
        claims["iss"] = iss
    return jwt.encode(claims, priv, algorithm="RS256", headers={"kid": kid})


def test_valid_token_passes():
    priv, pub_jwk = _keypair()
    token = _mint(priv)
    claims = sso._validate_token(token, [pub_jwk])
    assert claims["email"] == "user@example.com"


def test_wrong_audience_rejected():
    priv, pub_jwk = _keypair()
    token = _mint(priv, aud="academy")  # aud distinto de "portal"
    with pytest.raises(HTTPException) as exc:
        sso._validate_token(token, [pub_jwk])
    assert exc.value.status_code == 401


def test_unknown_kid_rejected_no_fallback():
    """Un token cuyo kid no está en el JWKS se rechaza (no cae a jwks[0])."""
    priv, pub_jwk = _keypair()
    token = _mint(priv, kid="otro-kid")
    with pytest.raises(HTTPException) as exc:
        sso._validate_token(token, [pub_jwk])
    assert exc.value.status_code == 401


def test_issuer_verified_when_configured(monkeypatch):
    priv, pub_jwk = _keypair()
    monkeypatch.setattr(settings, "sso_issuer", "https://id.miel-robotschool.com")
    # iss correcto → pasa
    ok = _mint(priv, iss="https://id.miel-robotschool.com")
    assert sso._validate_token(ok, [pub_jwk])["email"] == "user@example.com"
    # iss incorrecto → 401
    bad = _mint(priv, iss="https://evil.example.com")
    with pytest.raises(HTTPException) as exc:
        sso._validate_token(bad, [pub_jwk])
    assert exc.value.status_code == 401
