"""Allowlisted typed tools. No SQL, shell, arbitrary HTTP or approval tool."""
import time
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from fastapi import HTTPException
from backend.app.auth import authorize
from backend.app.db import one
from backend.app.services import ScenarioChanges, create_proposal, get_restaurant, run_simulation
from ml.inference import forecast, inventory
from ai.rag import retriever

class Scope(BaseModel):
    model_config = ConfigDict(extra='forbid')
    restaurant_id: int = Field(ge=1, le=20)

class Search(Scope):
    query: str = Field(min_length=2, max_length=1000)
    k: int = Field(3, ge=1, le=5)

class Simulate(Scope):
    changes: ScenarioChanges

class Proposal(Scope):
    simulation_id: str = Field(pattern='^[a-f0-9-]{36}$')

class Status(Scope):
    action_id: str = Field(pattern='^[a-f0-9-]{36}$')

class ToolCall(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: Literal['get_demand_forecast', 'get_inventory_risks', 'get_kitchen_capacity', 'simulate_scenario', 'search_documents', 'create_action_proposal', 'get_action_status']
    arguments: dict
SCHEMAS = {'get_demand_forecast': Scope, 'get_inventory_risks': Scope, 'get_kitchen_capacity': Scope, 'simulate_scenario': Simulate, 'search_documents': Search, 'create_action_proposal': Proposal, 'get_action_status': Status}

class ToolBroker:

    def __init__(self, db, user, restaurant_id):
        self.db, self.user, self.restaurant_id = (db, user, restaurant_id)
        self.trace = []

    def call(self, call):
        call = ToolCall.model_validate(call)
        args = SCHEMAS[call.name].model_validate(call.arguments)
        authorize(self.user, args.restaurant_id)
        if args.restaurant_id != self.restaurant_id:
            raise HTTPException(403, 'Tool scope mismatch')
        start = time.perf_counter()
        rid = args.restaurant_id
        if call.name == 'get_demand_forecast':
            result = forecast(self.db, rid)
        elif call.name == 'get_inventory_risks':
            result = inventory(self.db, rid)
        elif call.name == 'get_kitchen_capacity':
            r = get_restaurant(self.db, rid)
            result = {k: r[k] for k in ['staff', 'kitchen_capacity']}
        elif call.name == 'search_documents':
            result = retriever().search(args.query, args.k)
        elif call.name == 'simulate_scenario':
            result = run_simulation(self.db, rid, args.changes, 'ai-analysis')
        elif call.name == 'create_action_proposal':
            result = create_proposal(self.db, rid, args.simulation_id, 'ai-coordinator')
        else:
            result = one(self.db, 'SELECT * FROM action_proposals WHERE id=? AND restaurant_id=?', (args.action_id, rid))
            if not result:
                raise HTTPException(404, 'Action not found')
        self.trace.append(dict(tool=call.name, restaurant_id=rid, latency_ms=(time.perf_counter() - start) * 1000, validated=True))
        return result
