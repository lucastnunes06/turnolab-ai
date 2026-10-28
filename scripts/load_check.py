"""Measured ASGI load; transport and concurrency limits are explicit."""
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path
import httpx
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.main import app

async def main():
    sem = asyncio.Semaphore(4)
    latencies = []
    statuses = []
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
        await client.get('/api/restaurants/1/forecast', headers={'Authorization': 'Bearer turnolab-demo'})

        async def request(i):
            async with sem:
                began = time.perf_counter()
                path = '/api/restaurants/1/' + ['history', 'forecast', 'inventory', 'actions'][i % 4]
                r = await client.get(path, headers={'Authorization': 'Bearer turnolab-demo'})
                latencies.append((time.perf_counter() - began) * 1000)
                statuses.append(r.status_code)
        began = time.perf_counter()
        await asyncio.gather(*(request(i) for i in range(80)))
        seconds = time.perf_counter() - began
    ordered = sorted(latencies)
    result = dict(requests=len(latencies), concurrency=4, errors=sum((x != 200 for x in statuses)), elapsed_seconds=seconds, requests_per_second=len(latencies) / seconds, median_ms=statistics.median(latencies), p95_ms=ordered[int(0.95 * (len(ordered) - 1))], max_ms=max(latencies), transport='in-process httpx ASGITransport, warm caches, no TCP overhead', limitation='Synchronous ML/SQLite work runs inside the event loop for this local demo. Concurrency is cooperative, not parallel CPU inference.')
    (ROOT / 'reports/load.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    assert result['errors'] == 0
if __name__ == '__main__':
    asyncio.run(main())
