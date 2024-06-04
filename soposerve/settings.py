"""
Server settings, uses pydantic settings models.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    minio_url: str
    minio_access: str
    minio_secret: str

    mongo_uri: str

    title: str
    description: str

    add_cors: bool = True
    debug: bool = True
    web: bool = False


SETTINGS = Settings()
