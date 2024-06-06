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

    create_test_user: bool = False
    "Create a test user with API key 'TEST_API_KEY' and all privaleges on startup."


SETTINGS = Settings()
