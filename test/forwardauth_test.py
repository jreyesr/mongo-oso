import dataclasses
from typing import Literal

import pytest
from pytest_bdd import scenarios, given, parsers

scenarios("forward_auth.feature")


@dataclasses.dataclass
class User:
    username: str
    role: str


@dataclasses.dataclass
class Repo:
    name: str
    access_level: Literal["Public", "Private"]


@pytest.fixture
def users() -> dict[str, User]:
    return {}


@pytest.fixture
def repos() -> dict[str, Repo]:
    return {}


@given(parsers.parse("a User with username {username} and role {role}"))
def create_user(users, username, role):
    users[username] = User(username, role)


@pytest.fixture
def oso_classes():
    return [User, Repo]


@given(parsers.re(r"the Repo (?P<repo>.+) that is (?P<access_level>Public|Private)"))
def _(repos, repo, access_level: Literal["Public", "Private"]):
    repos[repo] = Repo(repo, access_level)
