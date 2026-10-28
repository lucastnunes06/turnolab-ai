"""FastAPI entry point. Serve API and the local frontend from one origin."""
import json
import logging
import sqlite3
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Annotated, Literal
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from backend.app.auth import User, authorize
from backend.app.config import ARTIFACTS, DEMO_AS_OF, ROOT
from backend.app.db import get_db, one, rows
from backend.app.services import ScenarioChanges, create_proposal, decide_proposal, get_restaurant, run_simulation
from ml.inference import drift, forecast, inventory, report
from ai.coordinator import Question, respond
from ai.rag import retriever
app = FastAPI(docs_url=None, redoc_url=None, title='TurnoLab AI', version='0.1.0', description='Synthetic restaurant decision laboratory. No iFood affiliation. Replay data, not production.')
Db = Annotated[sqlite3.Connection, Depends(get_db)]
logger = logging.getLogger('turnolab')
logging.basicConfig(level=logging.INFO, format='%(message)s')
latencies = deque(maxlen=2000)
counters = {'requests': 0, 'errors': 0}

@app.middleware('http')
async def telemetry(request: Request, call_next):
    start = time.perf_counter()
    request_id = str(uuid.uuid4())
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(json.dumps(dict(event='unexpected_error', request_id=request_id, kind=type(exc).__name__)))
        response = JSONResponse(status_code=500, content={'detail': 'Unexpected application error; consult the request ID'})
    ms = (time.perf_counter() - start) * 1000
    latencies.append(ms)
    counters['requests'] += 1
    if response.status_code >= 400:
        counters['errors'] += 1
    response.headers['X-Request-ID'] = request_id
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    logger.info(json.dumps(dict(event='http', request_id=request_id, path=request.url.path, method=request.method, status=response.status_code, latency_ms=round(ms, 3))))
    return response

@app.exception_handler(ValueError)
async def invalid_value(request, exc):
    logger.warning(json.dumps(dict(event='validation_error', kind=type(exc).__name__)))
    return JSONResponse(status_code=422, content={'detail': 'Invalid or insufficient data for this operation'})

@app.exception_handler(sqlite3.Error)
async def database_error(request, exc):
    logger.error(json.dumps(dict(event='database_error', kind=type(exc).__name__)))
    return JSONResponse(status_code=503, content={'detail': 'Database unavailable; run bootstrap and retry'})

@app.get('/docs', include_in_schema=False)
async def api_documentation():
    return FileResponse(ROOT / 'frontend/api-docs.html')

@app.get('/health')
async def health():
    return {'status': 'ok', 'product': 'TurnoLab AI'}

@app.get('/ready')
async def ready(db: Db):
    count = db.execute('SELECT COUNT(*) FROM restaurants').fetchone()[0]
    if count != 20 or not (ARTIFACTS / 'registry.json').exists() or (not (ARTIFACTS / 'inventory-v1.joblib').exists()):
        raise HTTPException(503, 'Bootstrap/training incomplete')
    return dict(status='ready', restaurants=count, mode='synthetic-replay', as_of=DEMO_AS_OF)

@app.get('/api/restaurants')
async def restaurants(db: Db, user: User, offset: int=Query(0, ge=0), limit: int=Query(20, ge=1, le=100)):
    data = rows(db, 'SELECT * FROM restaurants ORDER BY id')
    data = [r for r in data if r['id'] in user.restaurants]
    return dict(items=data[offset:offset + limit], total=len(data), as_of=DEMO_AS_OF, mode='synthetic-replay')

def scope(db, user, rid):
    authorize(user, rid)
    return get_restaurant(db, rid)

@app.get('/api/restaurants/{rid}/history')
async def history(rid: int, db: Db, user: User, limit: int=Query(48, ge=1, le=336)):
    scope(db, user, rid)
    items = rows(db, 'SELECT timestamp,orders,cancellations,capacity,prep_minutes,promotion,staff FROM order_events WHERE restaurant_id=? AND timestamp<=? ORDER BY timestamp DESC LIMIT ?', (rid, DEMO_AS_OF, limit))
    return dict(items=list(reversed(items)), as_of=DEMO_AS_OF)

@app.get('/api/restaurants/{rid}/forecast')
async def demand(rid: int, db: Db, user: User):
    scope(db, user, rid)
    return forecast(db, rid)

@app.get('/api/restaurants/{rid}/inventory')
@app.get('/api/restaurants/{rid}/risks')
async def stocks(rid: int, db: Db, user: User):
    scope(db, user, rid)
    return inventory(db, rid)

@app.get('/api/restaurants/{rid}/overview')
async def overview(rid: int, db: Db, user: User):
    restaurant = scope(db, user, rid)
    f = forecast(db, rid)
    stock = inventory(db, rid)
    current = (await history(rid, db, user, 48))['items']
    day = [r for r in current if r['timestamp'][:10] == DEMO_AS_OF[:10]]
    return dict(restaurant=restaurant, forecast=f, inventory=stock, history=current, metrics=dict(orders_today=sum((x['orders'] for x in day)), cancellations_today=sum((x['cancellations'] for x in day)), critical_ingredients=sum((s['critical'] for s in stock['items'])), capacity_utilization=f['forecasts'][0]['point'] / max(min(restaurant['kitchen_capacity'], f['current']['staff'] * 12), 1), demand_60_minutes=f['sum_60_minutes']), as_of=DEMO_AS_OF)

@app.post('/api/restaurants/{rid}/simulations')
async def simulate_endpoint(rid: int, changes: ScenarioChanges, db: Db, user: User):
    scope(db, user, rid)
    return run_simulation(db, rid, changes, user.actor)

@app.get('/api/restaurants/{rid}/simulations')
async def simulations(rid: int, db: Db, user: User, limit: int=Query(20, ge=1, le=100)):
    scope(db, user, rid)
    items = rows(db, 'SELECT id,origin,created_at,results FROM simulation_runs WHERE restaurant_id=? ORDER BY created_at DESC LIMIT ?', (rid, limit))
    return {'items': [{**s, 'results': json.loads(s['results'])} for s in items]}

@app.post('/api/restaurants/{rid}/copilot')
async def copilot(rid: int, question: Question, db: Db, user: User):
    scope(db, user, rid)
    return await respond(db, user, rid, question)

@app.get('/api/restaurants/{rid}/conversations')
async def conversations(rid: int, db: Db, user: User, limit: int=Query(20, ge=1, le=100)):
    scope(db, user, rid)
    return {'items': rows(db, 'SELECT id,created_at,question,response FROM agent_conversations WHERE restaurant_id=? ORDER BY created_at DESC LIMIT ?', (rid, limit))}

@app.get('/api/documents/search')
async def search_documents(user: User, q: str=Query(min_length=2, max_length=1000), k: int=Query(3, ge=1, le=5), strategy: Literal['lexical', 'lsa', 'hybrid']='lexical'):
    return retriever().search(q, k, strategy)

@app.get('/api/documents/{doc_id}')
async def document(doc_id: str, user: User):
    doc = retriever().docs.get(doc_id)
    if doc is None:
        raise HTTPException(404, 'Document not found')
    return doc

class ProposalBody(BaseModel):
    model_config = ConfigDict(extra='forbid')
    simulation_id: str = Field(pattern='^[a-f0-9-]{36}$')

class Decision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Literal['approved', 'rejected']

@app.post('/api/restaurants/{rid}/actions')
async def proposal(rid: int, body: ProposalBody, db: Db, user: User):
    scope(db, user, rid)
    return create_proposal(db, rid, body.simulation_id, user.actor)

@app.get('/api/restaurants/{rid}/actions')
async def actions(rid: int, db: Db, user: User, status: Literal['pending', 'approved', 'rejected'] | None=None, offset: int=Query(0, ge=0), limit: int=Query(25, ge=1, le=100)):
    scope(db, user, rid)
    condition = ' AND status=?' if status else ''
    params = (rid, status) if status else (rid,)
    items = rows(db, 'SELECT * FROM action_proposals WHERE restaurant_id=?' + condition + ' ORDER BY created_at DESC,id DESC LIMIT ? OFFSET ?', params + (limit, offset))
    total = db.execute('SELECT COUNT(*) FROM action_proposals WHERE restaurant_id=?' + condition, params).fetchone()[0]
    return dict(items=items, total=total)

@app.post('/api/restaurants/{rid}/actions/{aid}/decision')
async def decision(rid: int, aid: str, body: Decision, db: Db, user: User):
    scope(db, user, rid)
    return decide_proposal(db, rid, aid, body.status, user)

@app.get('/api/restaurants/{rid}/audit')
async def audit(rid: int, db: Db, user: User, offset: int=Query(0, ge=0), limit: int=Query(30, ge=1, le=100)):
    scope(db, user, rid)
    return dict(items=rows(db, 'SELECT * FROM audit_logs WHERE restaurant_id=? ORDER BY id DESC LIMIT ? OFFSET ?', (rid, limit, offset)))

@app.get('/api/models')
async def models(user: User):
    return dict(demand=report('demand'), inventory=report('stock'), rag=report('rag'))

@app.get('/api/experiments')
async def experiments(user: User):
    return dict(operational=report('experiments'), agents=report('agents'), rag=report('rag'))

@app.get('/api/restaurants/{rid}/monitoring')
async def monitoring(rid: int, db: Db, user: User):
    scope(db, user, rid)
    inference = one(db, 'SELECT SUM(count) count,SUM(total_ms) total_ms FROM inference_aggregates WHERE restaurant_id=?', (rid,))
    conv = rows(db, 'SELECT response FROM agent_conversations WHERE restaurant_id=?', (rid,))
    responses = [json.loads(c['response']) for c in conv]
    return dict(drift=drift(db, rid), api=dict(**counters, mean_ms=sum(latencies) / max(len(latencies), 1), sample_n=len(latencies), scope='process-local rolling window'), inference=inference, copilot=dict(conversations=len(responses), fallbacks=sum((r.get('fallback', False) for r in responses)), abstentions=sum((r.get('abstained', False) for r in responses)), estimated_tokens=sum((r.get('estimated_tokens', 0) for r in responses)), tool_calls=sum((len(r.get('tools', [])) for r in responses))), actions=rows(db, 'SELECT status,COUNT(*) count FROM action_proposals WHERE restaurant_id=? GROUP BY status', (rid,)))

@app.post('/api/restaurants/{rid}/evaluate')
async def operational_evaluation(rid: int, db: Db, user: User):
    scope(db, user, rid)
    risk = inventory(db, rid)
    event = dict(id=str(uuid.uuid4()), restaurant_id=rid, type='operational.risk', critical=[s['name'] for s in risk['items'] if s['critical']], origin=DEMO_AS_OF)
    db.execute('INSERT INTO operational_alerts(id,restaurant_id,payload) VALUES(?,?,?)', (event['id'], rid, json.dumps(event)))
    return event

@app.get('/api/restaurants/{rid}/alerts')
async def alerts(rid: int, db: Db, user: User):
    scope(db, user, rid)
    return {'items': rows(db, 'SELECT * FROM operational_alerts WHERE restaurant_id=? ORDER BY created_at DESC LIMIT 50', (rid,))}
front = ROOT / 'frontend'
if front.exists():
    app.mount('/', StaticFiles(directory=str(front), html=True), name='frontend')
