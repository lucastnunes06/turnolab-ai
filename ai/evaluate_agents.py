"""Measure two deterministic coordinator modes; no inflated multi-agent claim."""
import asyncio
import json
import statistics
import time
from backend.app.config import REPORTS
from backend.app.db import session
from backend.app.auth import Principal
from ai.coordinator import Question, respond

async def main():
    prompts = ['Por que a demanda prevista está alta?', 'Quais ingredientes estão em risco?', 'Qual a política de reposição de estoque?', 'O que acontece com uma pessoa a mais na equipe?']
    output = {'simple': [], 'roles': []}
    facts = {}
    n = 12
    user = Principal('agent-evaluator', frozenset([1]))
    with session() as db:
        await respond(db, user, 1, Question(message=prompts[0]))
        for i in range(n):
            for mode in ['simple', 'roles'] if i % 2 == 0 else ['roles', 'simple']:
                start = time.perf_counter()
                r = await respond(db, user, 1, Question(message=prompts[i % 4], architecture=mode))
                output[mode].append((time.perf_counter() - start) * 1000)
                facts[i, mode] = [(x['label'], x['value']) for x in r['facts']]
        db.rollback()
    report = {k: dict(n=len(v), median_ms=statistics.median(v), mean_ms=statistics.mean(v), min_ms=min(v), max_ms=max(v)) for k, v in output.items()}
    report['identical_structured_facts'] = all((facts[i, 'simple'] == facts[i, 'roles'] for i in range(n)))
    report['conclusion'] = 'Papéis determinísticos e tool calling simples produziram os mesmos fatos. Não foi demonstrada vantagem de múltiplos agentes; a interface usa o caminho simples.'
    report['limitation'] = 'Single CPU/process, warm cache, 12 prompts per mode; role modes share the same implementation. This is an overhead/null ablation, not evidence about autonomous LLM agents.'
    (REPORTS / 'agents.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))
if __name__ == '__main__':
    asyncio.run(main())
