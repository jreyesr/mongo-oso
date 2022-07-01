import logging
from typing import List, Optional

from oso import Oso, Relation
from pymongo import MongoClient
from bson.objectid import ObjectId
from pydantic import BaseModel, Field

from mongo_adapter import MongoAdapter

logging.basicConfig(level=logging.DEBUG)

class User(BaseModel):
    username: str
    is_superuser: bool
    company: str
    department: str
    permissions: List[str] = []


class OwnerInfo(BaseModel):
    owners: List[str]
    department: str
    company: str
 

class Org(BaseModel):
    __coll_name__ = "orgs"
    # id: ObjectID
    owner: OwnerInfo
    is_public: bool


class Repo(BaseModel):
    __coll_name__ = "repos"
    # id: ObjectID
    # org_id: ObjectID

client = MongoClient()
oso = Oso()
oso.set_data_filtering_adapter(MongoAdapter(client["testdb"]))

oso.register_class(OwnerInfo, fields={"owners": list, "department": str, "company": str})
oso.register_class(Org, fields={"is_public": bool, "owner": Relation(
    kind="one", other_type="OwnerInfo", my_field="owner", other_field=""
)})
oso.register_class(Repo, fields={"org": Relation(
    kind="one", other_type="Org", my_field="org_id", other_field="_id"
)})

oso.register_class(User, fields={"username": str, "is_superuser": bool, "company": str, "department": str, "permissions": list})


oso.load_files(["policy.polar"])

print("=====ME=====")
me = User(username="me", is_superuser=False, company="ACME", department="Audit", permissions=[])
print(me)

print("=====MY ORGS=====")
my_orgs = [Org(**r) for r in oso.authorized_resources(me, "read", Org)]
print(my_orgs)

print("=====MY REPOS=====")
my_repos = [Repo(**s) for s in oso.authorized_resources(me, "read", Repo)]
print(my_repos)

print("===SINGLE TESTS===")
one_org = client["testdb"]["orgs"].find_one({"_id": ObjectId("62bd11722c77337894d0e754")})

# oso.authorize(me, "read", Org(**one_org))  # NOTE: This doesn't work :(
q = oso.authorized_query(me, "read", Org)
print(q)
# This does work, however
print(list(client["testdb"]["orgs"].aggregate(q + [{"$match": {"_id": one_org["_id"]}}])))

print("=====DIFFERENT USERS=====")
# NOTE All this will print the query on DEBUG level
print("superuser")
oso.authorized_resources(User(username="big.boss", is_superuser=True, company="Big Corp", department="Boring Dept."), "read", Repo)
print("Normal user")
oso.authorized_resources(User(username="joe.average", is_superuser=False, company="Big Corp", department="Boring Dept."), "read", Repo)
print("auditor")
oso.authorized_resources(User(username="nosy.nick", is_superuser=False, company="Big Corp", department="Audit"), "read", Repo)