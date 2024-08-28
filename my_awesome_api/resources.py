from ast import literal_eval
from typing import Any, Generator

import settings as settings
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from boto3.session import Session
from database import SQLDatabase
from sqlalchemy.orm import Session as SQLSession

_aws_session: Session = None
_secrets_manager: Any = None
_secret_cache: SecretCache = None
_database: SQLDatabase = None


def get_aws_session(region, use_profile=None):
    global _aws_session
    if _aws_session is None:
        _aws_session = Session(region_name=region, profile_name=use_profile)
    return _aws_session


def get_secrets_manager(region, use_profile=None):
    global _secrets_manager
    if _secrets_manager is None:
        boto_session = get_aws_session(region, use_profile)
        _secrets_manager = boto_session.client("secretsmanager", region_name=region)
    return _secrets_manager


def get_secret_cache(region, use_profile=None):
    global _secret_cache
    if _secret_cache is None:
        client = get_secrets_manager(region, use_profile)
        cache_config = SecretCacheConfig()
        _secret_cache = SecretCache(config=cache_config, client=client)
    return _secret_cache


def get_database(use_proxy=False, use_secret_cache=None) -> SQLDatabase:
    """
    Helper function (works for fastapi dependency injection) to fetch
    singleton instance of database connected to given endpoint

    Args:
        use_proxy (bool): Enables switching between RDS Proxy and direct RDS connection
        use_secret_cache (SecretCache): Fetch database secrets from Secrets Manager
        instead from local .env file

    Returns:
        SQLDatabase: SQLAlchemy database instance connected to database
    """
    global _database
    if _database is None:
        if use_proxy:
            database_endpoint = settings.RDS_PROXY_ENDPOINT
        else:
            database_endpoint = settings.DATABASE_ENDPOINT
        if use_secret_cache:
            database_credentials = literal_eval(
                use_secret_cache.get_secret_string(settings.AWS_SECRET_NAME)
            )
            database_username = database_credentials["username"]
            database_password = database_credentials["password"]
        else:
            database_username = settings.DATABASE_USERNAME
            database_password = settings.DATABASE_PASSWORD
        _database = SQLDatabase(
            username=database_username,
            password=database_password,
            endpoint=database_endpoint,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
        )
        print(f"Connection established to database: {_database.engine.url}")
    return _database


def database_session() -> Generator[SQLSession, None, None]:
    _db: SQLDatabase = get_database()
    with _db.create_session() as session:
        yield session
