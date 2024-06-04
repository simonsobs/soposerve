"""
Request and response models for the users endpoints.
"""

from pydantic import BaseModel

from soposerve.service.users import Privilege


class CreateUserRequest(BaseModel):
    privileges: list[Privilege]
    # TODO: Compliance


class CreateUserResponse(BaseModel):
    api_key: str | None


class ReadUserResponse(BaseModel):
    name: str
    privileges: list[Privilege]
    # TODO: Compliance


class UpdateUserRequest(BaseModel):
    privileges: list[Privilege] | None
    refresh_key: bool


class UpdateUserResponse(BaseModel):
    api_key: str | None
