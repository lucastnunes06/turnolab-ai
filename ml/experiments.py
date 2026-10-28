"""Pre-specified policy ablation on held-out demand outcomes; no LLM does arithmetic."""
import hashlib
import json
import time
from itertools import product
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from backend.app.config import REPORTS
from ai.rag import retriever
from ml.tracking import log_run
from simulator.engine import Scenario, simulate
SEED = 20261028
STRATEGIES = [('fixed', 'Regras fixas'), ('forecast', 'Regras + previsão'), ('simulator', 'Previsão + simulador'), ('rag', 'Previsão + simulador + RAG'), ('copilot', 'Previsão + simulador + copiloto')]

def experiment(n=400):
    rng = np.random.default_rng(SEED)
    p = pd.read_csv(REPORTS / 'demand_predictions.csv')
    a = p[p.horizon_minutes == 30][['restaurant_id', 'origin', 'hour', 'y', 'prediction']]
    b = p[p.horizon_minutes == 60][['restaurant_id', 'origin', 'y', 'prediction']]
    data = a.merge(b, on=['restaurant_id', 'origin'], suffixes=('_30', '_60'))
    data = data[(data.hour >= 16) & (data.hour <= 21)].sample(n=n, random_state=SEED).reset_index(drop=True)
    retrieval = retriever().search('Qual o limite de pessoas adicionais durante picos de pedidos?')
    citations = [x['document_id'] for x in retrieval['hits']]
    records = []
    for i, row in data.iterrows():
        staff = int(rng.integers(2, 6))
        physical = float(rng.uniform(35, 85))
        stock = float(rng.uniform(20, 160))
        backlog = float(rng.uniform(0, 20))
        wage = float(rng.uniform(20, 32))
        delay_cost = float(rng.uniform(3, 12))
        stock_cost = float(rng.uniform(8, 20))
        lead = int(rng.choice([1, 2, 3]))
        purchase_cost = float(rng.uniform(0.3, 0.9))
        expected = [row.prediction_30, row.prediction_60]
        actual = [row.y_30, row.y_60]
        base = dict(staff=staff, kitchen_capacity=physical, stock_orders=stock, initial_backlog=backlog, wage_per_hour=wage, backlog_cost=delay_cost, stockout_cost=stock_cost, replenishment_after=lead)
        options = list(product(range(4), [0.0, 60.0]))

        def run(action, demand):
            extra, replen = action
            result = simulate(Scenario(**{**base, 'staff': staff + extra, 'replenishment_orders': replen, 'demand': demand}))
            result['total_cost'] += extra * 8 + (20 + replen * purchase_cost if replen else 0)
            return result
        t = time.perf_counter()
        fixed = (int(row.hour >= 18), 0.0)
        heuristic = (int(np.clip(np.ceil(max(expected) / 12) - staff, 0, 2)), 60.0 if sum(expected) > stock and lead == 1 else 0.0)
        best = min(options, key=lambda action: run(action, expected)['total_cost'])
        chosen = {'fixed': fixed, 'forecast': heuristic, 'simulator': best, 'rag': best, 'copilot': best}
        solver_ms = (time.perf_counter() - t) * 1000
        oracle = min((run(action, actual)['total_cost'] for action in options))
        for strategy, label in STRATEGIES:
            action = chosen[strategy]
            r = run(action, actual)
            records.append(dict(scenario=i, strategy=strategy, label=label, restaurant_id=int(row.restaurant_id), origin=row.origin, extra_staff=action[0], replenishment=action[1], backlog=r['backlog'], cost=r['total_cost'], regret=r['total_cost'] - oracle, policy_compliance=action[0] <= 2, document_support=strategy in ['rag', 'copilot'] and 'peaks' in citations, solver_ms=solver_ms, forecast_total=sum(expected), actual_total=sum(actual), base_staff=staff, physical_capacity=physical, stock_orders=stock, delivery_lead=lead, initial_backlog=backlog, wage_per_hour=wage, backlog_cost=delay_cost, stockout_cost=stock_cost, purchase_cost=purchase_cost, forecast_30=expected[0], forecast_60=expected[1], actual_30=actual[0], actual_60=actual[1]))
    frame = pd.DataFrame(records)
    sensitivity = []
    for demand_factor in [0.8, 1.0, 1.2]:
        for cost_factor in [0.5, 1.0, 2.0]:
            for key, label in STRATEGIES[:3]:
                costs = []
                queues = []
                for r in frame[frame.strategy == key].itertuples():
                    scenario = Scenario(staff=r.base_staff + r.extra_staff, kitchen_capacity=r.physical_capacity, stock_orders=r.stock_orders, initial_backlog=r.initial_backlog, wage_per_hour=r.wage_per_hour, backlog_cost=r.backlog_cost * cost_factor, stockout_cost=r.stockout_cost, replenishment_after=r.delivery_lead, replenishment_orders=r.replenishment, demand=[r.actual_30 * demand_factor, r.actual_60 * demand_factor])
                    out = simulate(scenario)
                    costs.append(out['total_cost'] + r.extra_staff * 8 + (20 + r.replenishment * r.purchase_cost if r.replenishment else 0))
                    queues.append(out['backlog'])
                sensitivity.append(dict(strategy=key, demand_multiplier=demand_factor, backlog_cost_multiplier=cost_factor, mean_cost=float(np.mean(costs)), mean_backlog=float(np.mean(queues))))
    pd.DataFrame(sensitivity).to_csv(REPORTS / 'decision_sensitivity.csv', index=False)
    results = []
    fixed_cost = frame[frame.strategy == 'fixed'].sort_values('scenario').cost.to_numpy()
    for key, label in STRATEGIES:
        g = frame[frame.strategy == key].sort_values('scenario')
        differences = g.cost.to_numpy() - fixed_cost
        boot = np.array([rng.choice(differences, len(differences), replace=True).mean() for _ in range(1000)])
        result = dict(strategy=key, label=label, mean_backlog=float(g.backlog.mean()), mean_cost=float(g.cost.mean()), mean_regret=float(g.regret.mean()), policy_compliance=float(g.policy_compliance.mean()), document_support=float(g.document_support.mean()), paired_cost_delta=float(differences.mean()), bootstrap_95_ci=[float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))], solver_mean_ms=float(g.solver_ms.mean()))
        results.append(result)
        log_run('decision-ablation', dict(strategy=key, seed=SEED, n=n), result, '')
    assert frame[frame.strategy == 'simulator'].cost.reset_index(drop=True).equals(frame[frame.strategy == 'rag'].cost.reset_index(drop=True))
    report = dict(sensitivity=sensitivity, seed=SEED, n_scenarios=n, strategies=results, document_ids=citations, hypotheses=['H1: forecast-informed policies reduce cost vs fixed rules on held-out synthetic outcomes.', 'H2: solver improves chosen objective over a forecast threshold heuristic.', 'H3: RAG improves documentary support; identical numeric outputs are required by design.', 'H4: deterministic role labels do not improve decisions over simple tool calling.'], development='Rules written without reading sampled test outcomes. Test origins start day 72. Seed differs from data generation.', conclusion='RAG e copiloto mantêm o resultado operacional do simulador por construção. Sua contribuição aqui é o suporte documental; não há evidência de ganho operacional adicional por IA generativa.', limitations=['Synthetic outcomes and fluid simulator; no external validity claim.', 'Oracle and simulator share structural assumptions.', 'Bootstrap is scenario-level and ignores restaurant correlation.', 'Forecast errors are temporally correlated.', 'Policy compliance is measured as a separate check; retrieval does not enforce staffing policy in this ablation.', 'No external LLM executed. Offline coordinator is an evidence presentation layer.'], protocol_hash=hashlib.sha256(b'turnolab-fixed-forecast-simulator-same-numerics-rag-v1').hexdigest())
    frame.to_csv(REPORTS / 'decision_scenarios.csv', index=False)
    (REPORTS / 'experiments.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), layout='constrained')
    labels = ['Fixed', 'Forecast rule', 'Simulator', '+ RAG', '+ Copilot']
    axes[0].bar(labels, [r['mean_cost'] for r in results], color=['#b3bbc6', '#829ab2', '#32977a', '#7eb69c', '#abcbb9'])
    axes[0].set(title='Held-out synthetic operational cost', ylabel='Hypothetical BRL / scenario')
    axes[0].tick_params(axis='x', rotation=15)
    axes[1].bar(labels, [r['mean_backlog'] for r in results], color='#83b79f')
    axes[1].set(title='Remaining backlog', ylabel='Orders / scenario')
    axes[1].tick_params(axis='x', rotation=15)
    fig.savefig(REPORTS / 'decision_ablation.png', dpi=160)
    plt.close(fig)
    print(json.dumps(report, indent=2, ensure_ascii=False))
if __name__ == '__main__':
    experiment()
