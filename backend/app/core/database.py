from sqlmodel import create_engine, Session
from app.core.config import settings

engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=280,
)

def get_session():
    with Session(engine) as session:
        yield session