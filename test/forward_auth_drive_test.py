import dataclasses
from dataclasses import field
from typing import Optional

import pytest
from pytest_bdd import scenarios, given, parsers, when, then

from conftest import DDict

scenarios("forward_auth_drive.feature")


@dataclasses.dataclass
class User:
    id: str
    orgs: list["Organization"] = field(default_factory=list)


@dataclasses.dataclass
class File:
    name: str
    owner: Optional[User] = None
    folder: Optional["Folder"] = None

    readers: list[User] = field(default_factory=list)
    writers: list[User] = field(default_factory=list)

    public: bool = False
    org_readable: bool = False


@dataclasses.dataclass
class Folder:
    name: str
    owner: Optional[User] = None
    organization: Optional["Organization"] = None
    parent_folder: Optional["Folder"] = None
    readers: list[User] = field(default_factory=list)
    writers: list[User] = field(default_factory=list)

    org_readable: bool = False


@dataclasses.dataclass
class Organization:
    name: str
    members: list[User] = field(default_factory=list)
    admins: list[User] = field(default_factory=list)


@pytest.fixture
def oso_classes():
    return [User, File, Folder, Organization]


@pytest.fixture
def users() -> DDict[User]:
    return DDict(User, "id")


@pytest.fixture
def files() -> DDict[File]:
    return DDict(File, "name")


@pytest.fixture
def folders() -> DDict[Folder]:
    return DDict(Folder, "name")


@pytest.fixture
def orgs() -> DDict[Organization]:
    return DDict(Organization, "name")


@given(parsers.parse("a User with id {username}"))
def _(users, username):
    users[username] = User(username)


@given(parsers.parse("a File {file_name} owned by {user_id}"))
def _(files, users, file_name, user_id):
    files[file_name] = File(file_name, owner=users[user_id])


@given(parsers.parse("a Folder {folder_name} owned by {user_id}"))
def _(users, folders, folder_name, user_id):
    folders[folder_name] = Folder(folder_name, owner=users[user_id])


@given(parsers.parse("a Folder {folder_name} owned by org {org_name}"))
def _(orgs, folders, folder_name, org_name):
    folders[folder_name] = Folder(folder_name, organization=orgs[org_name])


@given(parsers.parse("that Folder {folder_name} is org-readable"))
def _(folders, folder_name):
    folders[folder_name].org_readable = True


@given(parsers.parse("that file {file_name} is public"))
def _(files, file_name):
    files[file_name].public = True


@given(parsers.parse("a File {file_name} stored in folder {folder_name}"))
def _(files, folders, file_name, folder_name):
    files[file_name] = File(file_name, folder=folders[folder_name])


@given(parsers.parse("that user {user_id} is a member of {org_name}"))
def _(users, orgs, user_id, org_name):
    user = users[user_id]
    org = orgs[org_name]
    user.orgs.append(org)
    org.members.append(user)


@given(parsers.parse("that user {user_id} is a reader of folder {folder_name}"))
def _(users, folders, user_id, folder_name):
    folders[folder_name].readers.append(users[user_id])


@given(parsers.parse("that user {user_id} is a writer of folder {folder_name}"))
def _(users, folders, user_id, folder_name):
    folders[folder_name].writers.append(users[user_id])


@given(parsers.parse("that user {user_id} is a reader of file {file_name}"))
def _(users, files, user_id, file_name):
    files[file_name].readers.append(users[user_id])


@given(parsers.parse("that user {user_id} is a writer of file {file_name}"))
def _(users, files, user_id, file_name):
    files[file_name].writers.append(users[user_id])


@given(parsers.parse("a folder {folder_name} stored inside {parent_folder_name}"))
def _(folders, folder_name, parent_folder_name):
    folders[folder_name].parent_folder = folders[parent_folder_name]


@when(parsers.parse("{user_id} tries to {action} file {file_name}"), target_fixture="enforcement_result")
def _(files, users, polar_engine, user_id, action, file_name):
    return polar_engine.is_allowed(users[user_id], action, files[file_name])


@when(parsers.parse("{user_id} tries to {action} folder {folder_name}"), target_fixture="enforcement_result")
def _(folders, users, polar_engine, user_id, action, folder_name):
    return polar_engine.is_allowed(users[user_id], action, folders[folder_name])


@then(parsers.parse("{user_id} can {action} file {file_name}"))
def _(files, users, polar_engine, user_id, action, file_name):
    assert polar_engine.is_allowed(users[user_id], action, files[file_name]), f"{user_id} should be able to {action} file {file_name}"


@then(parsers.parse("{user_id} can {action} folder {folder_name}"))
def _(folders, users, polar_engine, user_id, action, folder_name):
    assert polar_engine.is_allowed(users[user_id], action, folders[folder_name]), f"{user_id} should be able to {action} folder {folder_name}"


@then(parsers.parse("{user_id} cannot {action} file {file_name}"))
def _(files, users, polar_engine, user_id, action, file_name):
    assert not polar_engine.is_allowed(users[user_id], action, files[file_name]), f"{user_id} should NOT be able to {action} file {file_name}"


@then(parsers.parse("{user_id} cannot {action} folder {folder_name}"))
def _(folders, users, polar_engine, user_id, action, folder_name):
    assert not polar_engine.is_allowed(users[user_id], action, folders[folder_name]), f"{user_id} should NOT be able to {action} folder {folder_name}"
