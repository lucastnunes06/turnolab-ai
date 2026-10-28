"""Bounded role separation vs simple tool calling. Both use exactly the same evidence."""
import json
import re
import time
import uuid
from pydantic import BaseModel, ConfigDict, Field
from backend.app.services import ScenarioChanges
from ai.providers import explain
from ai.tools import ToolBroker

class Question(BaseModel):
    model_config = ConfigDict(extra='forbid')
    message: str = Field(min_length=2, max_length=1500)
    architecture: str = Field('roles', pattern='^(roles|simple)$')
INJECTION = re.compile('ignore.*(instru|anterior|previous)|system prompt|reveal.*secret|api.key|senha|segredo|execute.*(sql|shell|comando)|outro restaurante|restaurant_id|apro[vb].*(automatic|sozinh)|drop table', re.I)
OPERATIONAL = re.compile('demanda|pedidos|prev|estoque|ingrediente|cozinha|equipe|pessoa|capacidade|backlog|cenario|cenário|recomenda|ação|acao|proposta|pico|reposi|politica|política|cancel|copiloto|modelo|offline|custo|fila|incerteza|document|frango|arroz|folhas|pão|pao', re.I)

async def respond(db, user, rid, question):
    began = time.perf_counter()
    cid = str(uuid.uuid4())

    def finish(result):
        db.execute('INSERT INTO agent_conversations(id,restaurant_id,question,response) VALUES(?,?,?,?)', (cid, rid, question.message, json.dumps(result)))
        return result
    if INJECTION.search(question.message):
        return finish(dict(id=cid, answer='Não posso executar instruções que alterem permissões, revelem segredos ou aprovem ações. Reformule a pergunta sobre a operação autorizada.', facts=[], citations=[], tools=[], abstained=True, blocked=True, provider='offline-template', generative=False, latency_ms=(time.perf_counter() - began) * 1000))
    if not OPERATIONAL.search(question.message):
        return finish(dict(id=cid, answer='Não há evidência operacional suficiente para responder a essa pergunta no corpus do TurnoLab.', facts=[], citations=[], tools=[], abstained=True, provider='offline-template', generative=False, latency_ms=(time.perf_counter() - began) * 1000))
    broker = ToolBroker(db, user, rid)

    def call(name, **kwargs):
        return broker.call(dict(name=name, arguments=dict(restaurant_id=rid, **kwargs)))
    demand = call('get_demand_forecast')
    stocks = call('get_inventory_risks')
    capacity = call('get_kitchen_capacity')
    docs = call('search_documents', query=question.message)
    q = question.message.lower()
    sim = None
    proposal = None
    if re.search('pessoa|equipe|cenário|cenario|backlog|recomenda|proposta|simul', q):
        changes = ScenarioChanges(staff=demand['current']['staff'] + 1, kitchen_capacity=capacity['kitchen_capacity'])
        sim = call('simulate_scenario', changes=changes.model_dump())
    if sim and re.search('(crie|criar|proponha|gerar).*proposta', q):
        proposal = call('create_action_proposal', simulation_id=sim['id'])
    critical = [s['name'] for s in stocks['items'] if s['critical']]
    f = demand['forecasts'][0]
    facts = [dict(label='Demanda · próximo intervalo', value=f['point'], unit='pedidos', source=f['model_version'], interval=[f['lower'], f['upper']]), dict(label='Capacidade física', value=capacity['kitchen_capacity'], unit='pedidos/30 min', source='restaurants'), dict(label='Ingredientes em risco', value=', '.join(critical) or 'Nenhum acima do limiar', unit='', source='inventory-v1')]
    if sim:
        facts.extend([dict(label='Backlog atual', value=round(sim['current']['backlog'], 2), unit='pedidos', source=sim['id']), dict(label='Backlog alternativo', value=round(sim['alternative']['backlog'], 2), unit='pedidos', source=sim['id'])])
    evidence = dict(documents=docs['hits'], facts=facts, limitations=demand['limitations'])
    external = await explain(evidence)
    if docs['hits']:
        answer = 'A recomendação considera previsão, capacidade e estoque. ' + docs['hits'][0]['text']
    else:
        answer = 'As ferramentas retornaram os dados abaixo. Não encontrei uma política documental que sustente uma recomendação; confirme as hipóteses antes de decidir.'
    if sim:
        answer += ' Adicionar uma pessoa ' + ('reduz a fila neste cenário.' if sim['delta']['backlog'] < -0.01 else 'não reduz a fila neste cenário; verifique o limite físico e os ingredientes.')
    result = dict(id=cid, answer=answer, interpretation=external['explanation'], facts=facts, citations=docs['hits'], tools=broker.trace, provider=external['provider'], generative=external['generative'], fallback=external['fallback'], estimated_tokens=external['estimated_tokens'], prompt_version='coordinator-v1', abstained=docs['abstained'], blocked=False, simulation_id=sim['id'] if sim else None, proposal=proposal, architecture=question.architecture, roles=['Analysis', 'Knowledge', 'Coordinator'] if question.architecture == 'roles' else ['tool-calling'], architecture_note='Deterministic role separation; no independent autonomous LLM agents.', warnings=demand['limitations'], latency_ms=(time.perf_counter() - began) * 1000)
    db.execute('INSERT INTO agent_conversations(id,restaurant_id,question,response) VALUES(?,?,?,?)', (cid, rid, question.message, json.dumps(result)))
    return result
