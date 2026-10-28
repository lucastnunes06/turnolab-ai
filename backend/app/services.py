import json
import uuid
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from backend.app.auth import authorize
from backend.app.config import DEMO_AS_OF
from backend.app.db import one, rows
from ml.inference import forecast, inventory
from simulator.engine import Scenario, compare

class ScenarioChanges(BaseModel):
    model_config = ConfigDict(extra='forbid')
    staff: int = Field(ge=1, le=30)
    kitchen_capacity: float = Field(gt=0, le=1000, allow_inf_nan=False)
    demand_multiplier: float = Field(1, ge=0.1, le=3, allow_inf_nan=False)
    promotion: float = Field(0, ge=0, le=1, allow_inf_nan=False)
    stock_multiplier: float = Field(1, ge=0, le=5, allow_inf_nan=False)
    replenishment_orders: float = Field(0, ge=0, le=10000, allow_inf_nan=False)
    replenishment_after: int = Field(2, ge=1, le=24)
    wage_per_hour: float = Field(24, ge=0, le=1000, allow_inf_nan=False)
    backlog_cost: float = Field(8, ge=0, le=1000, allow_inf_nan=False)
    stockout_cost: float = Field(15, ge=0, le=1000, allow_inf_nan=False)

def get_restaurant(db, rid):
    r = one(db, 'SELECT * FROM restaurants WHERE id=?', (rid,))
    if r is None:
        raise HTTPException(404, 'Restaurant not found')
    return r

def audit(db, rid, actor, event, entity, details):
    db.execute('INSERT INTO audit_logs(restaurant_id,actor,event,entity_id,details) VALUES(?,?,?,?,?)', (rid, actor, event, entity, json.dumps(details)))

def run_simulation(db, rid, changes, actor='human-operator', precomputed=None):
    restaurant = get_restaurant(db, rid)
    demand, stock = precomputed or (forecast(db, rid), inventory(db, rid))
    stock_orders = max(0, min(((s['on_hand'] - s['safety_stock']) / s['consumption_rate'] for s in stock['items'])))
    current = Scenario(staff=demand['current']['staff'], kitchen_capacity=restaurant['kitchen_capacity'], demand=[f['point'] for f in demand['forecasts']], stock_orders=stock_orders, wage_per_hour=changes.wage_per_hour, backlog_cost=changes.backlog_cost, stockout_cost=changes.stockout_cost)
    alternative = Scenario(staff=changes.staff, kitchen_capacity=changes.kitchen_capacity, demand=[x * changes.demand_multiplier for x in current.demand], promotion=changes.promotion, stock_orders=stock_orders * changes.stock_multiplier, replenishment_orders=changes.replenishment_orders, replenishment_after=changes.replenishment_after, wage_per_hour=changes.wage_per_hour, backlog_cost=changes.backlog_cost, stockout_cost=changes.stockout_cost)
    result = compare(current, alternative)
    result['changes'] = changes.model_dump()
    result['id'] = str(uuid.uuid4())
    result['restaurant_id'] = rid
    result['origin'] = DEMO_AS_OF
    result['forecast_model'] = demand['forecasts'][0]['model_version']
    result['input_current'] = current.model_dump()
    result['input_alternative'] = alternative.model_dump()
    result['forecast_evidence'] = demand
    result['policy_warning'] = 'Policy suggests at most two extra people.' if changes.staff > current.staff + 2 else None
    db.execute('INSERT INTO simulation_runs(id,restaurant_id,model_id,origin,inputs,results) VALUES(?,?,?,?,?,?)', (result['id'], rid, result['forecast_model'], DEMO_AS_OF, json.dumps({'current': current.model_dump(), 'alternative': alternative.model_dump()}), json.dumps(result)))
    audit(db, rid, actor, 'simulation.created', result['id'], {'model': result['forecast_model'], 'origin': DEMO_AS_OF})
    return result

def create_proposal(db, rid, simulation_id, actor):
    s = one(db, 'SELECT * FROM simulation_runs WHERE id=? AND restaurant_id=?', (simulation_id, rid))
    if not s:
        raise HTTPException(404, 'Simulation not found in scope')
    result = json.loads(s['results'])
    alt = result['input_alternative']
    title = f"Revisar cenário: {alt['staff']} pessoas · capacidade {alt['kitchen_capacity']:.0f}/30 min"
    aid = str(uuid.uuid4())
    db.execute('INSERT INTO action_proposals(id,restaurant_id,simulation_id,title,created_by) VALUES(?,?,?,?,?)', (aid, rid, simulation_id, title, actor))
    audit(db, rid, actor, 'proposal.created', aid, {'simulation_id': simulation_id, 'status': 'pending'})
    return one(db, 'SELECT * FROM action_proposals WHERE id=?', (aid,))

def decide_proposal(db, rid, aid, status, user):
    authorize(user, rid)
    if not user.reviewer or user.actor.startswith('ai-'):
        raise HTTPException(403, 'Human reviewer required')
    action = one(db, 'SELECT * FROM action_proposals WHERE id=? AND restaurant_id=?', (aid, rid))
    if not action:
        raise HTTPException(404, 'Proposal not found in scope')
    if action['created_by'].startswith('ai-') and user.actor == action['created_by']:
        raise HTTPException(403, 'Self-approval forbidden')
    if status not in ['approved', 'rejected']:
        raise HTTPException(422, 'Invalid decision')
    cursor = db.execute("UPDATE action_proposals SET status=?,decided_by=? WHERE id=? AND restaurant_id=? AND status='pending'", (status, user.actor, aid, rid))
    if cursor.rowcount != 1:
        raise HTTPException(409, 'Proposal already decided')
    audit(db, rid, user.actor, 'proposal.' + status, aid, {'previous': 'pending', 'simulation_id': action['simulation_id'], 'execution': 'audit only; no operational mutation'})
    return one(db, 'SELECT * FROM action_proposals WHERE id=?', (aid,))
