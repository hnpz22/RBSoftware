from app.domains.inventory.routes.components import router as inventory_components_router
from app.domains.inventory.routes.inventory import router as inventory_router
from app.domains.inventory.routes.locations import router as inventory_locations_router

__all__ = [
    "inventory_locations_router",
    "inventory_router",
    "inventory_components_router",
]
