import dataclasses
from collections import defaultdict
from typing import Literal

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from oso import Oso

scenarios("forward_auth_gitclub.feature")


@dataclasses.dataclass
class Org:
    id: str


@dataclasses.dataclass
class OrgRole:
    name: Literal["owner", "member"]
    org_id: str


@dataclasses.dataclass
class Repo:
    id: str
    org: Org


@dataclasses.dataclass
class RepoRole:
    name: Literal["admin", "maintainer", "reader"]
    repo_id: str


@dataclasses.dataclass
class Issue:
    creator_id: str
    repo: Repo


@dataclasses.dataclass
class User:
    id: str
    org_roles: list[OrgRole]
    repo_roles: list[RepoRole]


@pytest.fixture
def oso_classes():
    return [User, Repo, Org, Issue, OrgRole, RepoRole]


@pytest.fixture
def users() -> dict[str, User]:
    return {}


@pytest.fixture
def repos() -> dict[str, Repo]:
    return {}


@pytest.fixture
def issues() -> dict[(str, int), Issue]:
    return {}


@pytest.fixture
def orgs() -> dict[str, Org]:
    return defaultdict(Org)


@given(parsers.parse("a User with id {username}"))
def _(users, username):
    users[username] = User(username, org_roles=[], repo_roles=[])


@given(parsers.parse("the Repo {repo_id}"))
def _(repos, orgs, repo_id: str):
    org_id = repo_id.split("/")[0]
    repos[repo_id] = Repo(repo_id, orgs.get(org_id, ))


@given(parsers.parse("{username} has org_role {role} on {org_id}"))
def _(users, username, role, org_id):
    users[username].org_roles.append(OrgRole(role, org_id))


@given(parsers.parse("{username} has repo_role {role} on {repo_id}"))
def _(users, username, role, repo_id):
    users[username].repo_roles.append(RepoRole(role, repo_id))


@given(parsers.parse("an Issue #{issue_num:d} on {repo_id} created by {creator}"))
def _(repos, issues, issue_num: int, repo_id: str, creator: str):
    issues[(repo_id, issue_num)] = Issue(creator, repos[repo_id])


@when(parsers.parse("{username} tries to {action} issue #{issue_num:d} on {repo_id}"), target_fixture="enforcement_result")
def _(issues, users, polar_engine, username, action, issue_num, repo_id):
    return polar_engine.is_allowed(users[username], action, issues[(repo_id, issue_num)])

