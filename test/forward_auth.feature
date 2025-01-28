Feature: Checking a single resource against a single user

  Oso can directly check if a certain user can perform a certain action on a certain resource.
  We call this "forward auth" since it's a straightforward evaluation of the authorization rules
  to find if there's any that match the user+action+resource combo.

  This Feature isn't actually testing the mongo-oso code, it's mostly to ensure that the testing
  harness is correctly in place and working as expected.

  Background:
    Given a User with username alice and role admin
    And a User with username bob and role user
    And the Repo jreyesr/mongo-oso that is Private
    And the Repo osohq/polar that is Public
    And the following Polar file:
      """
      actor User {}
      resource Repo {}

      allow(actor, action, resource) if
            has_permission(actor, action, resource);

      has_permission(user:User, _: String, _: Resource) if user.role == "admin";

      has_permission(_:User, "read", r: Repo) if r.access_level == "Public";
      """

  Example: alice tries to read public repo
    When alice tries to read repo osohq/polar
    Then action succeeds

  Example: bob tries to read public repo
    When bob tries to read repo osohq/polar
    Then action succeeds

  Example: bob tries to read private repo
    When bob tries to read repo jreyesr/mongo-oso
    Then action fails

  Example: admin tries to read private repo
    When alice tries to read repo jreyesr/mongo-oso
    Then action succeeds