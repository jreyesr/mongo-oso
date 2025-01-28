Feature: Single-resource authorization checks for the Gitclub example app

  This Feature ensures that authorization checks for the Gitclub example app work
  for single-resource situations, where the User and the Resource are known ahead of time.

  This Feature isn't actually testing the mongo-oso code, it's mostly to ensure that the testing
  harness is correctly in place and working as expected.

  Background:
    Given a User with id alice
    And a user with id bob
    And the Repo jreyesr/mongo-oso
    And the Repo osohq/polar
    And the Polar file test/gitclub.polar

  Scenario Outline: Actions on repos
    Given alice has repo_role <role> on <repo>
    When alice tries to <action> repo <repo>
    Then action <result>

    Examples:
      | role       | repo        | action                  | result   |
      | reader     | osohq/polar | read                    | succeeds |
      | maintainer | osohq/polar | read                    | succeeds |
      | admin      | osohq/polar | read                    | succeeds |
      | reader     | osohq/polar | create_role_assignments | fails    |
      | maintainer | osohq/polar | create_role_assignments | fails    |
      | admin      | osohq/polar | create_role_assignments | succeeds |

  Scenario Outline: Actions on issues
    Given an Issue #1 on osohq/polar created by alice
    Given alice has repo_role <role> on osohq/polar
    When alice tries to <action> issue #1 on osohq/polar
    Then action <result>

    Examples:
      | role       | action | result   |
      | reader     | read   | succeeds |
      | maintainer | read   | succeeds |
      | admin      | read   | succeeds |
      | reader     | close  | succeeds |
      | maintainer | close  | succeeds |
      | admin      | close  | succeeds |

  Scenario Outline: Bob's actions on issues
    Given an Issue #1 on osohq/polar created by alice
    Given bob has repo_role reader on osohq/polar
    When bob tries to <action> issue #1 on osohq/polar
    Then action <result>

    Examples:
      | action | result   |
      | read   | succeeds |
      | close  | fails    |