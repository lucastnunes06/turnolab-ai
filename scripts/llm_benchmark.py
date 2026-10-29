"""Audit optional generative explanations without disguising templates as LLM results.

Offline: python scripts/llm_benchmark.py --provider offline
Real API (requires credentials): LLM_API_KEY=... python scripts/llm_benchmark.py --provider groq --live
Never commit credentials or raw user data. This benchmark uses synthetic evidence only.
"""
import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai.providers import ExternalProvider, OfflineProvider
from ai.rag import retriever

CASES = [
    ("Como funciona a política de reposição de ingredientes?", "replenishment"),
    ("Que cuidados considerar no prazo de entrega?", "replenishment"),
    ("Como o turno deve reagir a picos de pedidos?", "peaks"),
    ("Adicionar pessoas sempre aumenta a capacidade?", "capacity"),
    ("Como a capacidade física limita a produção?", "capacity"),
    ("Posso cancelar pedidos automaticamente?", "cancellation"),
    ("Quem pode aprovar uma ação proposta?", "governance"),
    ("Como lidar com dados de um restaurante não autorizado?", "governance"),
    ("Quem venceu a Copa do Mundo em 2022?", None),
    ("Qual é a cotação do bitcoin agora?", None),
]

def prepare_cases():
    engine = retriever()
    for i, (question, gold) in enumerate(CASES):
        retrieval = engine.search(question, k=3)
        yield {
            "id": f"case-{i + 1:02d}",
            "question": question,
            "gold_document_id": gold,
            "retrieved_ids": [d["document_id"] for d in retrieval["hits"]],
            "retrieval_abstained": retrieval["abstained"],
            "evidence": {
                "question": question,
                "documents": retrieval["hits"],
                "facts": [],
                "limitations": ["Dados sintéticos; nenhuma ação comercial real autorizada."],
            },
        }

async def evaluate(provider_name):
    provider = OfflineProvider() if provider_name == "offline" else ExternalProvider(provider_name)
    rows = []
    for case in prepare_cases():
        t0 = time.perf_counter()
        try:
            answer = await provider.explain(case["evidence"])
            cited = answer["citation_ids"]
            allowed = set(case["retrieved_ids"])
            valid = set(cited).issubset(allowed)
            latency = (time.perf_counter() - t0) * 1000
            rows.append({
                "case": case["id"],
                "gold": case["gold_document_id"],
                "retrieved": case["retrieved_ids"],
                "retrieval_gold_in_top3": case["gold_document_id"] in case["retrieved_ids"] if case["gold_document_id"] else None,
                "retrieval_abstained": case["retrieval_abstained"],
                "citation_ids": cited,
                "citations_within_retrieved_evidence": valid,
                "cites_gold_document": case["gold_document_id"] in cited if case["gold_document_id"] else None,
                "generated": bool(answer.get("generative")),
                "estimated_tokens": answer.get("estimated_tokens"),
                "latency_ms": round(latency, 2),
                "status": "ok",
            })
        except Exception as exc:
            # Do not expose provider responses, tokens or exception text in a report.
            rows.append({"case": case["id"], "status": "error", "error_type": type(exc).__name__})
    successful = [r for r in rows if r["status"] == "ok"]
    positives = [r for r in successful if r["gold"]]
    negatives = [r for r in successful if not r["gold"]]
    report = {
        "provider": provider_name,
        "real_external_llm_executed": provider_name != "offline" and bool(successful) and any(r["generated"] for r in successful),
        "data_source": "Synthetic prompts and five fictional TurnoLab policies",
        "evaluated_cases": len(rows),
        "successful_cases": len(successful),
        "failed_cases": len(rows) - len(successful),
        "retrieval_hit_at_3": round(sum(r["retrieval_gold_in_top3"] for r in positives) / len(positives), 3) if positives else None,
        "retrieval_correct_abstention": round(sum(r["retrieval_abstained"] for r in negatives) / len(negatives), 3) if negatives else None,
        "citation_ids_allowed_rate": round(sum(r["citations_within_retrieved_evidence"] for r in successful) / len(successful), 3) if successful else None,
        "gold_citation_rate": round(sum(r["cites_gold_document"] for r in positives) / len(positives), 3) if positives else None,
        "latency_median_ms": round(statistics.median(r["latency_ms"] for r in successful), 2) if successful else None,
        "estimated_total_tokens": sum(r.get("estimated_tokens") or 0 for r in successful),
        "limitations": [
            "Ten hand-authored synthetic cases, not a blind or independent benchmark.",
            "Citation checks validate IDs, not semantic entailment or factual correctness.",
            "Offline provider uses templates, not a local LLM.",
            "Latency measured on this environment; no production SLA or cost claim.",
        ],
        "cases": rows,
    }
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=("offline", "groq", "gemini"), default="offline")
    parser.add_argument("--live", action="store_true", help="Required before any external API calls")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if args.provider != "offline":
        if not args.live:
            parser.error("External provider requires --live; no external calls were made.")
        if not os.environ.get("LLM_API_KEY"):
            parser.error("LLM_API_KEY is required for live evaluation.")
    elif args.live:
        parser.error("--live is only for external providers, not offline templates.")
    report = asyncio.run(evaluate(args.provider))
    target = args.output or (ROOT / "reports" / ("llm_benchmark_" + args.provider + ".json"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2, ensure_ascii=False))
    print("Report:", target)
    if report["failed_cases"]:
        raise SystemExit(1)
    if args.provider != "offline" and not report["real_external_llm_executed"]:
        raise SystemExit("No real generative responses were verified")

if __name__ == "__main__":
    main()
