from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class SQLDatabase:
    def __init__(
        self,
        *,
        username,
        password,
        endpoint,
        port,
        database,
        ssl=False,
        pool_pre_ping=True,
    ):
        ssl_mode = "require" if ssl else "disable"
        self.engine = create_engine(
            f"postgresql+psycopg2://{username}:{password}@{endpoint}:{port}/{database}?sslmode={ssl_mode}",
            pool_pre_ping=pool_pre_ping,
        )
        self.session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)

    @contextmanager
    def create_session(self):
        session = self.session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
