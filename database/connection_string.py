from app.core.settings import get_settings, Settings
settings: Settings = get_settings()


def connection_string():
    connection_string_async = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost:5432/{settings.POSTGRES_DATABASE}"
    return connection_string_async
