# Tests

To run the tests:

```shell
pytest -vv --gherkin-terminal-reporter
```

To create new tests, write files in [Gherkin](https://cucumber.io/docs/gherkin/reference)
syntax (the `*.feature` files), and then, if necessary, add Python code to
implement the steps mentioned in those files. See the already existing `.feature` files and
the `*_test.py` files.

Currently available Gherkin steps are:

* Given:
    * "the Polar file {filename}": (see `forward_auth_gitclub.feature`) Installs a Polar file in the engine, by
      providing its file path
    * "a Polar file with contents {docstring}": (see `forward_auth.feature`)  Receives a Polar file directly inside the
      test file, using [a Doc String](https://cucumber.io/docs/gherkin/reference#doc-strings)
* When:
    * "{username} tries to {action} repo {repo_name}": Checks whether the provided user can perform an action on a repo,
      stores the result for the Then steps
* Then:
    * "action succeeds": Asserts that the When before was authorized
    * "action fails": Asserts that the When before was NOT authorized

You're encouraged to define more specific Given, When and Then steps for each test file's specific
data model (for example, `forwardauth_gitclub_test.py` defines the
entire [GitClub](https://github.com/osohq/gitclub/blob/main/backends/flask-sqlalchemy-oso/app/models.py)
data model in the `flask-sqlalchemy-oso` variant, including Repos, Orgs, Issues, Users, RepoRoles and OrgRoles)

## Tips

### Put "database" setup on Given

If you need objects to exist so they can be referenced later, use Given steps
to create the objects. For example:

```gherkin
Given a User with username alice and role admin
```

This interacts with the following Python code:

```py
import dataclasses

import pytest
from pytest_bdd import given, parsers


@dataclasses.dataclass
class User:
    username: str
    role: str


@pytest.fixture
def users() -> dict[str, User]:
    return {}


@given(parsers.parse("a User with username {username} and role {role}"))
def create_user(users, username, role):
    users[username] = User(username, role)
```

After the Given step runs, the `users` fixture (which is a dictionary
indexing users by their usernames) will contain a User object. The `users`
fixture can then be used on any other steps that refer to users by username,
such as "when {user} reads {repo}".

### Use a container fixture for repeated Givens

If you want to create multiple objects of the same kind (which means using
the same Given repeatedly), use a fixture and mutate it to hold all the objects,
[as suggested here](https://github.com/pytest-dev/pytest-bdd/issues/157#issuecomment-149137198).
This is done in the example above, where the `users` fixture is a dictionary
and each invocation of the "a User with username {username} and role {role}" safely
adds another user.

### Don't touch the Polar files!

You shouldn't need to do _any_ changes to the real Polar files in order to test them.
Try at all costs to keep them exactly as in the application under test, so the
real authorization checks are tested.

For the classes that should be registered with Oso, prefer to also reuse the application's
classes if they exist (such as SQLAlchemy ORM classes or
Pydantic/[MongoEngine](https://github.com/MongoEngine/mongoengine)
classes for this plugin). If you need to create the classes from scratch, simple [
`dataclasses`-based classes](https://docs.python.org/3/library/dataclasses.html)
should work fine, and they're fairly easy to write. You don't need to replicate _all_ the fields
of the original data, just the fields that are used to make authorization decisions.

## So why Gherkin?

For no particular reason, other than I wanted to try it. Trial seems to have been successful:
the whole idea of setting up the stage with a few objects and their attributes in Given steps,
and then executing authz checks on Then steps, seems to be very clear:

```gherkin
Example: roles on folders bubble down to files in subfolders
Given that user Samir is a reader of folder tps-reports
And a folder tps-reports/1999 stored inside tps-reports
And a file tps-reports/1999/peter.txt stored in folder tps-reports/1999
Then Samir can read folder tps-reports
```

The Given steps create the required objects (e.g. `Given that user Samir is a reader of folder tps-reports` creates a
User with name=Samir, and a Folder with name=tps-reports, and adds Samir to the `readers` property of the tps-reports
folder) or set attributes on an object (e.g. `Given that file text.txt is public` creates a File with name=test.txt and
sets its `public` property to True).

The Then step tries to run an authz check with the provided user, action and resource (using [Oso's
`is_allowed`](https://www.osohq.com/docs/oss/guides/enforcement/resource.html), which returns a boolean), and checks
whether the authz check successfully failed, successfully passed, or unexpectedly passed/failed.

This project [uses `pytest-bdd`](https://pytest-bdd.readthedocs.io/en/stable/) to integrate the Gherkin language with Pytest.