# oso-mongo-adapter

A [Data Adapter](https://docs.osohq.com/reference/frameworks/data_filtering.html) that integrates the [Oso authorization library](https://www.osohq.com/) with MongoDB databases.

## What works?

Data filtering :)

Data filtering allows you to call `oso.authorized_resources(user, "read", ResourceClass)` and get back a list of all objects of type `ResourceClass` that the `user` can `read`. Obtaining an authorized query (i.e., the raw DB query that would generate the list) is also supported, in case you want to apply further filtering, sorting or pagination, for example.

See below (the [Limitations section](#limitations)) for what _doesn't_ work

## How to use?

See `main.py` for a working example.

1. Write your policy as normal.
2. Implement [Pydantic models](https://pydantic-docs.helpmanual.io/) for each collection and nested document. The classes that correspond to collections must have a `__coll_name__ = "collection_name"` attribute-.
3. Instantiate a [MongoClient from the pymongo library](https://pymongo.readthedocs.io/en/stable/tutorial.html).
4. Register a `MongoAdapter` instance with Oso,, passing it a database connection.
5. Register the Pydantic classes with `oso.register_class`. You only need to declare the fields that are used for policy decisions.
6. 
    For nested documents, when registering the outer class, declare the inner field as a `Relation` with `kind=one`, `my_field` set to the key of the nested document, and `other_field` set to an empty string (this is the marker that the library uses to determine that the relation is a nested field and not a lookup). For example, consider the following MongoDB document (data model taken from [here](https://www.mongodb.com/docs/manual/tutorial/model-embedded-one-to-many-relationships-between-documents/#std-label-one-to-many-embedded-document-pattern)):
    ```js
    {
        _id: "joe",
        name: "Joe Bookreader",
        address: {
            street: "123 Fake Street",
            city: "Faketon",
            state: "MA",
            zip: "12345"
        }
    }
    ```
    This resource would be registered with Oso as
    ```py
    # Register the inner/nested class
    oso.register_class(Address, fields={"street": str, "city": str, "state": str, "zip": str})

    # Register the outer class
    oso.register_class(Patron, fields={
        "_id": str, "name": str, 
        "address": Relation(kind="one", other_type="Address", my_field="address", other_field="")
    })
    ```
7. 
    For one-to-many relationships that use document references, use the same pattern as when registering a SQL model. The `Relation` should have `other_field` set to `_id`. For example, for the following model (adapted from [here](https://www.mongodb.com/docs/manual/tutorial/model-referenced-one-to-many-relationships-between-documents/)):
    ```js
    // publishers collection
    {
        _id: "oreilly",
        name: "O'Reilly Media",
        founded: 1980,
        location: "CA"
    }

    // books collection
    {
        _id: 123456789,
        title: "MongoDB: The Definitive Guide",
        author: [ "Kristina Chodorow", "Mike Dirolf" ],
        published_date: ISODate("2010-09-24"),
        pages: 216,
        language: "English",
        publisher_id: "oreilly"
    }
    ```
    The `publisher` field in the `books` collection is a link to the `_id` in the `publishers` collection. This would be expressed in your code as:
    ```py
    # Declare the Pydantic models
    class Publisher(BaseModel):
        _id: str
        name: str
        founded: int
        location: str

    class Book(BaseModel):
        _id: int
        title: str
        author: List[str]
        published_date: datetime.datetime
        pages: int
        language: str
        publisher_id: str
    
    # Register the related-to class
    oso.register_class(Publisher, fields={"_id": str, "name": str, "founded": int, "location": str})

    # Register the class with the relationship
    # NOTE datetime.datetime cannot be (easily?) used, so skip the published_date field
    oso.register_class(Book, fields={
        "_id": int, "title": str, "author": list, "pages": int, "language": str,
        "publisher": Relation(kind="one", other_type="Publisher", my_field="publisher_id", other_field="_id")
    })
    ```
8. Call `oso.load_files(["policy.polar"])`
9. Whenever you need to authorize data access, call `oso.authorized_query(user, "permission", Model)`, add any further clauses, if required, and then call `.aggregate()` on the computed pipeline and return the results.

### Logging
The `oso.adapter.mongo` logger prints all authorization queries at DEBUG level. Enable them if you wish to see the queries that are computed by the Oso engine.

## Limitations

- [Request-level enforcement](https://docs.osohq.com/guides/enforcement/request.html) is completely untested. I have hope it would work with no changes, since it should not touch the Adapter code at all, but who knows...
- Only works with pymongo and Pydantic (sorry, everyone else!)
- [Resource-level enforcement](https://docs.osohq.com/guides/enforcement/resource.html) (i.e., calling `oso.authorize(user, "read", some_object)`) doesn't work. To emulate it, apply [the data filtering API](https://docs.osohq.com/guides/data_filtering.html) to obtain the required authorization queries, and then append a new query to filter by `_id` or however else you would have obtained `some_object` otherwise:
    ```py
    # This ID probably comes from a URL segment, if developing a web application
    org_id = 12345

    q = oso.authorized_query(user, "read", Org)
    pipeline = q["pipeline"] + [
        {"$match": {"_id": org_id}},
    ]
    try:
        # Run the query and return the first element, if t exists
        return next(q["model"].aggregate(pipeline))
    except StopIteration:
        # Treat missing data just as unauthorized access, to leak no information to an attacker
        # Do whatever your web framework does to raise an HTTP status code 404
        raise Exception("404")
    ```
- Relations across collections (implemented with ObjectID keys) are only tested in the simplest case (a single ID as a foreign key replacement in the root level of the document). The most exotic relationship patterns (as documented [here](https://www.mongodb.com/docs/manual/tutorial/model-embedded-one-to-one-relationships-between-documents/)) may or may not work.
- Extremely untested! (Basically, it only implements the functionality required for my own use cases, and no more)

## Internals

The adapter uses MongoDB aggregation pipelines to express the conditions.

### Gotcha: `oso.authorized_query` is somewhat different to the official relational adapters

For the SQL (relational) adapters, `oso.authorized_query(me, "read", Org)` would return a pre-authorized query to which you could append more conditions if required:
```py
# NOTE This is code for the SQLAlchemy adapter, it doesn't work for Mongo
q = oso.authorized_query(user, "read", Org)
q = q.skip(0).limit(10)
return q.all()
```
However, this relies on the SQLAlchemy and Django ORMs allowing chaining of operations (for example, on Django, `Org.objects.filter(name="").filter(num_members__lt=50)[:10]` is a valid query, and it employs some sort of [fluent interface](https://www.martinfowler.com/bliki/FluentInterface.html) pattern. SQLAlchemy does more or less the same). However, on Mongo, doing `db["collname"].aggregate(...)` does NOT return an object on which further `.find()`s, `.skip()`s or `.aggregate()`s can be called, but a cursor that is already (more or less) a finalized query. Therefore, the `authorized_query()` method returns a different set of data:
```py
>>> oso.authorized_query(user, "read", Org)
{'model': Collection(Database(...), 'mydb'), 'orgs'), 'pipeline': [{'$match': {'$or': [...]}}]}
```
The method returns a dictionary with two keys: `model`, that returns the base/root model for the query (the result of `db["mycoll"]`); and `pipeline`, that returns a dictionary that can be plugged into a `.aggregate()` method call or extended with further stages beforehand. An example of usage with search and skip-limit pagination would be:
```
# These could come from the query string, if developing a web application
search_term = "Inc."
skip = 0
limit = 10

# SQLAlchemy adapter
ilike = "%{}%".format(search_term)
q = oso.authorized_query(user, "read", Org).filter(Org.name.ilike(ilike)).limit(limit).offset(skip)
return q.all()

# Django adapter
q = oso.authorized_query(user, "read", Org).filter(name__icontains=search_term)
return q[skip:limit]

# MongoAdapter
q = oso.authorized_query(user, "read", Org)
# Extend the pipeline with some more filter and pagination stages
pipeline = q["pipeline"] + [
    {"$match": {"name": re.compile(search_term, re.IGNORECASE)}},
    { "$skip": skip },
    { "$limit": limit },
]
return list(q["model"].aggregate(pipeline))
```

### Filtering

A single [`$match` stage](https://www.mongodb.com/docs/manual/reference/operator/aggregation/match/) is used to apply the filters. Inside the stage, the conditions are expressed as a disjunction of conjunctions, AKA `(x1 AND x2) OR (y1) OR (z1 AND z2 AND z3) OR ...`, AKA [conjunctive normal form](https://en.wikipedia.org/wiki/Conjunctive_normal_form). 

Some optimizations are used to remove useless operators: for example, in `OR(AND(x1, x2), AND(y1), AND(z1, z2, z3), ...)`, the `AND(y1)` part can be replaced by `y1`.

### Lookups (cross-collection data)

In case your policies require jumping across collections, [`$lookup` stages](https://www.mongodb.com/docs/manual/reference/operator/aggregation/lookup/) and [`$unwind` stages](https://www.mongodb.com/docs/manual/reference/operator/aggregation/unwind/) are added as required. These serve the function of a `JOIN` statement in a SQL database, in that they take an ID field in a document and replace it with a full document that comes from another collection.