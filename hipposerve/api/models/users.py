"""
Request and response models for the users endpoints.
"""

from pydantic import BaseModel

from hipposerve.service.users import Privilege


class CreateUserRequest(BaseModel):
    privileges: list[Privilege]
    password: str | None
    compliance: str | None


class CreateUserResponse(BaseModel):
    api_key: str | None


class ReadUserResponse(BaseModel):
    name: str
    privileges: list[Privilege]
    compliance: str | None


class UpdateUserRequest(BaseModel):
    privileges: list[Privilege] | None = None
    refresh_key: bool = False
    password: str | None = None
    compliance: str | None = None


class UpdateUserResponse(BaseModel):
    api_key: str | None
    compliance: str | None = None
