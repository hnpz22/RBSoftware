"""Audit domain routers."""

from app.domains.audit.routes.logs import router as audit_router

__all__ = ["audit_router"]
