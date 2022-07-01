import logging

from polar.data.adapter.adapter import DataAdapter
from polar.data.filter import Projection
from pydantic import BaseModel

logger = logging.getLogger("oso.adapter.mongo")

class MongoAdapter(DataAdapter):
    def __init__(self, database):
        self.database = database

    def build_query(self, filter):
        types = filter.types

        relation_prefixes = {filter.model: []}
        lookups = []
        for rel in filter.relations:
            typ = types[rel.left]
            rec = typ.fields[rel.name]
            left = typ.cls
            right = types[rec.other_type].cls

            relation_prefixes[right] = relation_prefixes[left] + [rel.name]

            if rec.other_field:  # This is an actual join (a $lookup in Mongo), not a dot-style accesor for an embedded document
                assert right.__coll_name__, f"{right} must have a __coll_name__ attribute"
                lookups += [
                    {"$lookup": {
                        "from": right.__coll_name__,
                        "localField": rec.my_field,
                        "foreignField": rec.other_field,
                        "as": rel.name
                    }},
                    {"$unwind": {
                        "path": f"${rel.name}",
                        "preserveNullAndEmptyArrays": True
                    }},
                ]

        # if len(filter.conditions) == 0:
        #     disj = {"_id": {"$exists": 0}}
        # elif len(filter.conditions) == 1:
        #     disj = {"$and": [
        #         MongoAdapter.mongoize(conj, relation_prefixes) for
        #             conj in filter.conditions[0]
        #     ]}
        # else:
        #     disj = {"$or": [
        #         {"_id": {"$exists": 1}} if not conjs else {
        #             "$and": [MongoAdapter.mongoize(conj, relation_prefixes) for
        #                      conj in conjs]}
        #         for conjs in filter.conditions
        #     ]}
        disj = MongoAdapter.join_with_or(
            conditions=[
                MongoAdapter.join_with_and(
                    conditions=[MongoAdapter.mongoize(conj, relation_prefixes) for
                             conj in conjs], 
                    default={"_id": {"$exists": 1}})
                for conjs in filter.conditions],
            default={"_id": {"$exists": 0}}
        )
        cmd = lookups + [{"$match": disj}]

        query = self.database[filter.model.__coll_name__]
        logger.debug(cmd)
        return {"model": query, "pipeline": cmd}

    def execute_query(self, query):
        return list(query["model"].aggregate(query["pipeline"]))

    @staticmethod
    def mongoize(cond, relation_prefixes):
        op = cond.cmp
        lhs = MongoAdapter.add_side(cond.left, relation_prefixes)
        rhs = MongoAdapter.add_side(cond.right, relation_prefixes)
        if isinstance(cond.right, Projection):
            lhs, rhs = rhs, lhs  # Swap so the projection (AKA field name) is on the left side

        if op == "Eq":
            return {lhs: {"$eq": rhs}}
        elif op == "Neq":
            return {lhs: {"$neq": rhs}}
        elif op == "In":
            if not isinstance(rhs, list):
                rhs = [rhs]
            return {lhs: {"$in": rhs}}
        elif op == "Nin":
            if not isinstance(rhs, list):
                rhs = [rhs]
            return {lhs: {"$nin": rhs}}

    @staticmethod
    def add_side(side, relation_prefixes):
        if isinstance(side, Projection):
            accesor = ".".join(relation_prefixes[side.source] + [side.field])
            return accesor
        elif isinstance(side, BaseModel):  # Property of object
            # Sorry, this is not implemented :(
            raise Exception(
                "Don't compare to object! Use some unique key of the object instead")
            # return getattr(side, side.__primary_key__)
        else:  # Immediate value, just return it
            return side

    @staticmethod
    def join_with_or(conditions, default):
        if len(conditions) == 0:
            return default
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$or": conditions}
    @staticmethod
    def join_with_and(conditions, default):
        if len(conditions) == 0:
            return default
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}