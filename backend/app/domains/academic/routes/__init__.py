"""ACADEMIC domain routers."""

from app.domains.academic.routes.schools import router as schools_router
from app.domains.academic.routes.grades import router as grades_router
from app.domains.academic.routes.courses import router as courses_router
from app.domains.academic.routes.units import router as units_router
from app.domains.academic.routes.materials import router as materials_router
from app.domains.academic.routes.assignments import router as assignments_router
from app.domains.academic.routes.submissions import router as submissions_router
from app.domains.academic.routes.students import router as students_router

__all__ = [
    "schools_router",
    "grades_router",
    "courses_router",
    "units_router",
    "materials_router",
    "assignments_router",
    "submissions_router",
    "students_router",
]
