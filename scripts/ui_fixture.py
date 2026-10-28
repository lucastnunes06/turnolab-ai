"""Generate component test inputs from the real ASGI API, never invented UI metrics."""
import asyncio, json, sys
from pathlib import Path
import httpx
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.main import app

async def main():
    paths = {'data': '/restaurants/1/overview', 'models': '/models', 'experiments': '/experiments', 'monitoring': '/restaurants/1/monitoring', 'actions': '/restaurants/1/actions', 'audit': '/restaurants/1/audit', 'restaurants': '/restaurants'}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://test') as c:
        output = {}
        for key, path in paths.items():
            r = await c.get('/api' + path, headers={'Authorization': 'Bearer turnolab-demo'})
            r.raise_for_status()
            output[key] = r.json()
        r = await c.post('/api/restaurants/1/simulations', headers={'Authorization': 'Bearer turnolab-demo'}, json={'staff': 5, 'kitchen_capacity': 80})
        r.raise_for_status()
        output['simulation'] = r.json()
    (ROOT / '.data/ui_fixture.json').write_text(json.dumps(output))
asyncio.run(main())
