# This file comes from Oso's oso-drive sample app
# See https://github.com/osohq/sample-apps-node/blob/main/oso-drive/scripts/main.polar

actor User { }

resource Organization {
    roles = ["admin", "member"];

    "member" if "admin";
}

resource Folder {
    permissions = ["read", "write"];
    roles = ["reader", "writer"];
    relations = {
        folder: Folder,
        organization: Organization,
        owner: User
    };

    "writer" if "owner";

    "reader" if "reader" on "folder";
    "writer" if "writer" on "folder";
    "writer" if "admin" on "organization";

    "read" if "write";
    "read"  if "reader";
    "write" if "writer";
}

resource File {
    permissions = ["read", "write"];
    roles = ["reader", "writer"];
    relations = {
        folder: Folder,
        owner: User
    };

    "writer" if "owner";

    "reader" if "reader" on "folder";
    "writer" if "writer" on "folder";

    "read" if "write";
    "read"  if "reader";
    "write" if "writer";
}

allow(actor: User, action, resource) if
    print(actor, action, resource) and
    has_permission(actor, action, resource);

has_role(user: User, "reader", folder: Folder) if
    organization matches Organization and
    is_readable_by_org(folder) and
    has_role(user, "member", organization);

has_role(user: User, "reader", file: File) if
    organization matches Organization and
    is_readable_by_org(file) and
    has_role(user, "member", organization);

has_role(user: User, "reader", file: File) if
    organization matches Organization and
    folder matches Folder and
    is_readable_by_org(folder) and
    has_relation(file, "folder", folder) and
    has_role(user, "member", organization);

has_permission(_user: User, "read", file: File) if
    is_public(file);

# NEWLY ADDED
# Required to make the Polar file compatible with the ABAC/OSS Oso model
# Originally it worked fine with Oso Cloud's "facts" model, where facts about entities are recorded as separate assertions
# e.g.
# * has_relation(File{"tps-reports/tps-report-1999.txt"}, "owner", User{"Peter"})
# * is_public(File{"tps-reports/tps-report-1999.txt"})
# rather than as attributes on the actual entities, such as
# File{name="tps-reports/tps-report-1999.txt", owner=User{name="Peter"}, public=True}

has_role(subject: User, "member", org: Organization) if
    org in subject.orgs and subject in org.members;
has_role(subject: User, "admin", org: Organization) if
    subject in org.admins;
has_role(subject: User, "reader", folder: Folder) if
    subject in folder.readers;
has_role(subject: User, "writer", folder: Folder) if
    subject in folder.writers;

has_relation(subject: User, "owner", object: Folder) if
    object.owner = subject;
has_relation(subject: Organization, "organization", object: Folder) if
    object.organization = subject;
has_relation(subject: Folder, "folder", object: Folder) if
    object.parent_folder = subject;
has_relation(subject: Folder, "folder", object: File) if
    object.folder = subject;
has_relation(subject: User, "owner", object: File) if
    object.owner = subject;

is_public(file) if file.public;
is_readable_by_org(item) if item.org_readable;