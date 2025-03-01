from collections import UserDict

import pytest
from oso import Oso
from pytest_bdd import parsers, when, then, given


class DDict[T](UserDict[str, T]):
    def __init__(self, klass: type[T], field: str):
        super().__init__()
        self.klass = klass
        self.field = field

    def __getitem__(self, item: str):
        if item in self.data:
            return super().__getitem__(item)
        else:
            new_element: T = self.klass(**{self.field: item})  # create the new element
            super().__setitem__(item, new_element)  # store on backing dict
            return new_element  # and return


@given(parsers.cfparse("the Polar file {fname}"), target_fixture="polar_file")
def _(fname):
    with open("./" + fname) as f:
        return f.read()


# placeholder so we get typing, it'll be filled by the @when below
@pytest.fixture
def docstring() -> str:
    pass


@given("the following Polar file:", target_fixture="polar_file")
def _(docstring: str) -> str:
    return docstring


@pytest.fixture
def oso_classes() -> list[type]:
    raise NotImplementedError("To be redefined on each class that needs it")


@pytest.fixture
def polar_engine(polar_file, oso_classes) -> Oso:
    oso = Oso()
    for klass in oso_classes:
        oso.register_class(klass)
    oso.load_str(polar_file)
    return oso


# placeholder so we get typing, it'll be filled by the @when below
@pytest.fixture
def enforcement_result() -> bool:
    pass


@when(parsers.cfparse("{username} tries to {action} repo {repo_name}"), target_fixture="enforcement_result")
def _(username, action, repo_name, polar_engine, users, repos):
    return polar_engine.is_allowed(users[username], action, repos[repo_name])


@then("action succeeds")
def _(enforcement_result):
    assert enforcement_result is True, "action should have succeeded"


@then("action fails")
def _(enforcement_result):
    assert enforcement_result is False, "action shouldn't have succeeded"
