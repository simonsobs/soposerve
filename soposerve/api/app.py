"""
The main FastAPI endpoints.
"""

from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.middleware.cors import CORSMiddleware

from soposerve.api.product import product_router
from soposerve.api.relationships import relationship_router
from soposerve.api.users import users_router
from soposerve.database import BEANIE_MODELS
from soposerve.settings import SETTINGS
from soposerve.storage import Storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application services."""
    app.db = AsyncIOMotorClient(SETTINGS.mongo_uri).account
    await init_beanie(app.db, document_models=BEANIE_MODELS)
    app.storage = Storage(
        url=SETTINGS.minio_url,
        access_key=SETTINGS.minio_access,
        secret_key=SETTINGS.minio_secret,
    )

    if SETTINGS.create_test_user:
        from soposerve.service import users

        user = await users.create(name="admin", privileges=list(users.Privilege))
        await user.set({users.User.api_key: "TEST_API_KEY"})
        print(
            f"Created test user: {user.name} with API key: {user.api_key}. "
            "You should NOT see this message in production."
        )

    print("Startup complete")
    yield
    print("Shutdown complete")


app = FastAPI(
    title=SETTINGS.title,
    description=SETTINGS.description,
    lifespan=lifespan,
    docs_url="/docs" if SETTINGS.debug else None,
    redoc_url="/redoc" if SETTINGS.debug else None,
)

# Routers
app.include_router(users_router)
app.include_router(product_router)
app.include_router(relationship_router)

if SETTINGS.web:  # pragma: no cover
    from soposerve.web import web_router

    app.include_router(web_router)

if SETTINGS.add_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
