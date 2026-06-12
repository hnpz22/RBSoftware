from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from alembic import context
from app.core.config import settings

# Importar los modelos de TODOS los dominios vivos para que SQLModel.metadata los
# conozca. El listado debe coincidir 1:1 con app/domains/ — si se agrega o retira
# un dominio, actualizar aquí.
from app.domains.audit import models as audit_models  # noqa: F401
from app.domains.auth import models as auth_models  # noqa: F401
from app.domains.academic import models as academic_models  # noqa: F401
from app.domains.training import models as training_models  # noqa: F401
from app.domains.rbac import models as rbac_models  # noqa: F401

# `repository` usa un paquete `models/` con __init__ vacío (no reexporta como los
# demás), así que hay que importar cada submódulo para registrar sus tablas.
from app.domains.repository.models import (  # noqa: F401
    program_repository_file,
    program_repository_folder,
    repository_file,
    repository_folder,
    repository_folder_share,
)

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def include_object(object, name, type_, reflected, compare_to):
    """Red de seguridad: nunca generar DROP de una tabla que existe en la BD
    pero ya no tiene modelo en el código.

    En prod siguen aplicadas las migraciones de dominios retirados del LMS
    (catalog, commercial, production, inventory, fulfillment, integrations — ver
    'LMS Saneamiento Interno') y sus tablas se conservan como respaldo pasivo.
    Sin este filtro, un `alembic revision --autogenerate` las marcaría para DROP,
    junto con cualquier otra tabla huérfana. Política de este repo: las tablas se
    borran a mano con una migración explícita, nunca vía autogenerate.

    Efecto: autogenerate solo propone CREATE/ALTER aditivos, jamás DROP de tabla.
    """
    if type_ == "table" and reflected and compare_to is None:
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
