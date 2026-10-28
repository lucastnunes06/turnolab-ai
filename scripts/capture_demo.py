"""Record 90 seconds of the actual interface and actual API as a GIF.
Requires an allowed Chromium process; no mocked API values or fabricated frames.
"""
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import httpx
from PIL import Image
from playwright.async_api import async_playwright
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.main import app

async def main():
    (ROOT / 'docs/media').mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='turnolab-capture-') as temp:
        frames = []
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://turnolab.local') as client:
            async with async_playwright() as p:
                browser = await p.chromium.launch(executable_path=os.getenv('CHROMIUM_EXECUTABLE', '/usr/bin/chromium') or None, headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
                context = await browser.new_context(viewport={'width': 1280, 'height': 920}, device_scale_factor=1)

                async def bridge(route):
                    request = route.request
                    url = httpx.URL(request.url)
                    if url.host != 'turnolab.local':
                        await route.abort()
                        return
                    r = await client.request(request.method, url.raw_path.decode(), content=request.post_data_buffer, headers=request.headers)
                    await route.fulfill(status=r.status_code, body=r.content, headers={k: v for k, v in r.headers.items() if k not in ['content-length', 'content-encoding', 'transfer-encoding']})
                await context.route('**/*', bridge)
                page = await context.new_page()
                await page.goto('http://turnolab.local', wait_until='networkidle')
                await page.get_by_text('Um olhar para o próximo turno', exact=True).wait_for()

                async def hold(seconds):
                    until = time.monotonic() + seconds
                    while time.monotonic() < until:
                        path = Path(temp) / f'{len(frames):04}.png'
                        await page.screenshot(path=str(path))
                        frames.append(path)
                        await asyncio.sleep(min(1, max(0, until - time.monotonic())))
                began = time.perf_counter()
                await hold(8)
                await page.locator('a.nav-item[href="#demand"]').click()
                await hold(9)
                await page.locator('a.nav-item[href="#inventory"]').click()
                await hold(8)
                await page.locator('a.nav-item[href="#scenarios"]').click()
                await page.locator('#kitchen_capacity').evaluate("node=>{node.value='100';node.dispatchEvent(new Event('input',{bubbles:true}));}")
                await page.locator('#stock_multiplier').evaluate("node=>{node.value='2';node.dispatchEvent(new Event('input',{bubbles:true}));}")
                await hold(9)
                await page.get_by_role('button', name='Comparar cenários', exact=True).click()
                await page.get_by_text('Atual vs. alternativa', exact=True).wait_for()
                await hold(10)
                await page.locator('a.nav-item[href="#copilot"]').click()
                await page.get_by_role('button', name='O que acontece se eu adicionar uma pessoa à equipe?', exact=True).click()
                await page.get_by_text('Fundamentado', exact=True).wait_for()
                await hold(10)
                await page.locator('.citations button').first.click()
                await hold(7)
                await page.get_by_role('button', name='Fechar referência', exact=True).click()
                await page.locator('a.nav-item[href="#scenarios"]').click()
                await page.get_by_role('button', name='Criar proposta', exact=True).click()
                await page.get_by_text('Aguardando revisão', exact=True).first.wait_for()
                await hold(6)
                await page.get_by_role('button', name='Rejeitar', exact=True).first.click()
                await page.get_by_text('Proposta rejeitada', exact=True).first.wait_for()
                await hold(7)
                await page.locator('a.nav-item[href="#models"]').click()
                await hold(max(5, 90 - (time.perf_counter() - began)))
                await context.close()
                await browser.close()
        images = [Image.open(path).convert('RGB') for path in frames]
        output = ROOT / 'docs/media/demo.gif'
        duration = int((time.perf_counter() - began) * 1000 / max(len(images), 1))
        images[0].save(output, save_all=True, append_images=images[1:], duration=duration, loop=0, optimize=True)
        for image in images:
            image.close()
        result = dict(path=str(output.relative_to(ROOT)), frames=len(frames), duration_seconds=len(frames) * duration / 1000, transport='actual browser and API via ASGI bridge', fabricated_frames=False)
        (ROOT / 'reports/demo.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
if __name__ == '__main__':
    asyncio.run(main())
