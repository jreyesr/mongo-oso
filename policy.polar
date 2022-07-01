actor User {}
resource Org {}
resource OwnerInfo {}
resource Repo {}

# You can read ALL orgs if you are a superuser
has_permission(user: User, "read", _org: Org) if
  user.is_superuser;
# You can read public orgs
has_permission(_user: User, "read", org: Org) if
  org.is_public;
# You can read all orgs on which you are a direct owner
has_permission(user: User, "read", org: Org) if
  user.username in org.owner.owners;
# You can read all orgs that belong to the same company and department as you
has_permission(user: User, "read", org: Org) if
  user.company = org.owner.company and
  user.department = org.owner.department;
# You can read all orgs in your department if you belong to the Audit department
has_permission(user: User, "read", org: Org) if
  user.department = "Audit" and org.owner.company = user.company;

# You can read all repos in an org to which you have access
has_permission(user: User, "read", repo: Repo) if
  has_permission(user, "read", repo.org);


# Main entry point
allow(actor, action, resource) if has_permission(actor, action, resource);
