"""
Server settings, uses pydantic settings models.
"""

from datetime import timedelta

from passlib.context import CryptContext
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    minio_url: str
    minio_access: str
    minio_secret: str

    mongo_uri: str

    title: str
    description: str

    crypt_context: CryptContext = CryptContext("bcrypt")

    add_cors: bool = True
    debug: bool = True

    create_test_user: bool = False
    "Create a test user with API key 'test_user_api_key' and all privaleges on startup."
    test_user_password: str = "TEST_PASSWORD"
    "Password for the test user."
    test_user_api_key: str = "TEST_API_KEY"

    web: bool = False
    "Serve the web frontend."

    web_jwt_secret: str | None = None
    "Secret key for JWT (32 bytes hex)"
    web_jwt_algorithm: str = "HS256"
    "Algorithm for JWT"
    web_jwt_expires: timedelta = timedelta(hours=1)
    "Expiration time for JWT"

    web_allow_github_login: bool = False
    "Allow login with GitHub"
    web_github_client_id: str | None = None
    "GitHub client ID"
    web_github_client_secret: str | None = None
    "GitHub client secret"
    web_github_required_organisation_membership: str | None = None
    "Required GitHub organisation membership for login, if None any organisation is allowed."


SETTINGS = Settings()
