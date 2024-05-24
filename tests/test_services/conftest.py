"""
The goal of this testing module is simple: just test the
services in isolation, and do not interact at all with the
web endpoints.
"""

import pytest_asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from testcontainers.mongodb import MongoDbContainer

from soposerve.database import BEANIE_MODELS

### -- Container Fixtures -- ###

@pytest_asyncio.fixture(scope="session")
def database_container():
    kwargs = {
        "username": "root",
        "password": "password",
        "port": 27017,
        "dbname": "sopo_test",
    }

    with MongoDbContainer(**kwargs) as container:
        kwargs["url"] = container.get_connection_url()
        yield kwargs


### -- Dependency Injection Fixtures -- ###

@pytest_asyncio.fixture(scope="session", autouse=True)
async def database(database_container):
    db = AsyncIOMotorClient(database_container["url"])
    await init_beanie(
        database=db.db_name,
        document_models=BEANIE_MODELS,
    )

    yield db

### -- Data Service Fixtures -- ###

@pytest_asyncio.fixture(scope="session")
async def created_user(database):
    from soposerve.service import users

    user = await users.create(
        name="test_user",
        privileges=[users.Privilege.LIST]
    )

    yield user

    await users.delete(user.name)
