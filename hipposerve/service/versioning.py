"""
Tools for version management.
"""

from enum import Enum


class VersioningError(Exception):
    pass


class VersionRevision(Enum):
    MAJOR = 0
    MINOR = 1
    PATCH = 2
    VISIBILITY_REV= -1



def revise_version(current: str, level: VersionRevision) -> str:
    if level.value == -1:
        return current

    split = [int(x) for x in current.split(".")]

    split[level.value] = split[level.value] + 1

    for index in range(level.value + 1, len(split)):
        split[index] = 0

    return ".".join([f"{x}" for x in split])
