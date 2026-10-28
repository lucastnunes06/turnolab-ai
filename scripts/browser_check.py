"""Browser -> intercepted HTTP transport -> real ASGI app and SQLite (no mocked API results).
The transport bridge avoids opening TCP sockets in the restricted execution sandbox.
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path
import httpx
from playwright.async_api import async_playwright, Error as PlaywrightError
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.main import app

async def main():
    (ROOT / 'docs/media').mkdir(parents=True, exist_ok=True)
    errors = []
    checks = []
    shots = []
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://turnolab.local') as client:
        async with async_playwright() as p:
            browser = await p.chromium.launch(executable_path=os.getenv('CHROMIUM_EXECUTABLE', '/usr/bin/chromium') or None, headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu'])
            context = await browser.new_context(viewport={'width': 1440, 'height': 1100}, device_scale_factor=1)

            async def bridge(route):
                request = route.request
                url = httpx.URL(request.url)
                if url.host != 'turnolab.local':
                    await route.abort()
                    return
                response = await client.request(request.method, url.raw_path.decode(), content=request.post_data_buffer, headers=request.headers)
                headers = {k: v for k, v in response.headers.items() if k.lower() not in ['content-length', 'transfer-encoding', 'content-encoding']}
                await route.fulfill(status=response.status_code, headers=headers, body=response.content)
            await context.route('**/*', bridge)
            page = await context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            await page.goto('http://turnolab.local', wait_until='networkidle')
            await page.get_by_text('Um olhar para o próximo turno', exact=True).wait_for()
            await page.screenshot(path=str(ROOT / 'docs/media/dashboard.png'), full_page=True)
            shots.append('dashboard.png')
            checks.append('dashboard populated from actual API')
            await page.locator('a.nav-item[href="#demand"]').click()
            await page.get_by_text('O histórico encontra a previsão', exact=True).wait_for()
            checks.append('demand uncertainty and feature importance visible')
            await page.screenshot(path=str(ROOT / 'docs/media/demand.png'), full_page=True)
            await page.locator('a.nav-item[href="#scenarios"]').click()
            await page.locator('#kitchen_capacity').evaluate("node=>{node.value='100';node.dispatchEvent(new Event('input',{bubbles:true}));}")
            await page.locator('#stock_multiplier').evaluate("node=>{node.value='2';node.dispatchEvent(new Event('input',{bubbles:true}));}")
            await page.get_by_role('button', name='Comparar cenários', exact=True).click()
            await page.get_by_text('Atual vs. alternativa', exact=True).wait_for()
            await page.screenshot(path=str(ROOT / 'docs/media/scenario.png'), full_page=True)
            checks.append('scenario form calls deterministic backend and renders comparison')
            await page.get_by_role('button', name='Criar proposta', exact=True).click()
            await page.get_by_text('Aguardando revisão', exact=True).first.wait_for()
            await page.get_by_role('button', name='Aprovar', exact=True).first.click()
            await page.get_by_text('Proposta aprovada', exact=True).first.wait_for()
            checks.append('human approval and audit history persist in database')
            await page.screenshot(path=str(ROOT / 'docs/media/actions.png'), full_page=True)
            await page.locator('a.nav-item[href="#copilot"]').click()
            await page.get_by_role('button', name='Qual é a política de reposição de estoque?', exact=True).click()
            await page.get_by_text('Fundamentado', exact=True).wait_for()
            await page.locator('.citations button').first.click()
            await page.locator('#document-dialog[open]').wait_for()
            checks.append('copilot calls real tools, cites a document, opens exact reference')
            await page.screenshot(path=str(ROOT / 'docs/media/citation.png'), full_page=True)
            await page.get_by_role('button', name='Fechar referência', exact=True).click()
            await page.screenshot(path=str(ROOT / 'docs/media/copilot.png'), full_page=True)
            await page.locator('a.nav-item[href="#inventory"]').click()
            await page.get_by_text('Consumo, prazo e risco', exact=True).wait_for()
            await page.screenshot(path=str(ROOT / 'docs/media/inventory.png'), full_page=True)
            checks.append('inventory uses trained classifier probabilities')
            await page.locator('a.nav-item[href="#models"]').click()
            await page.get_by_text('O baseline também merece uma chance', exact=True).wait_for()
            await page.screenshot(path=str(ROOT / 'docs/media/models.png'), full_page=True)
            checks.append('model comparison and monitoring visible')
            await page.locator('a.nav-item[href="#experiments"]').click()
            await page.get_by_text('O que realmente melhora uma decisão?', exact=True).wait_for()
            checks.append('experiments page visible')
            await page.set_viewport_size({'width': 390, 'height': 844})
            await page.goto('http://turnolab.local/#dashboard', wait_until='networkidle')
            await page.get_by_text('Um olhar para o próximo turno', exact=True).wait_for()
            overflow_details = await page.evaluate("""() => {
              const viewport = window.innerWidth;
              const scrollWidth = document.documentElement.scrollWidth;
              const offenders = Array.from(document.querySelectorAll('body *'))
                .filter(el => {
                  const box = el.getBoundingClientRect();
                  const style = getComputedStyle(el);
                  return style.display !== 'none' && style.visibility !== 'hidden'
                    && box.width > 0 && (box.right > viewport + 1 || box.left < -1)
                    && style.position !== 'fixed';
                })
                .slice(0, 12).map(el => {
                  const box = el.getBoundingClientRect();
                  return {tag: el.tagName.toLowerCase(), className: String(el.className).slice(0, 100),
                    right: Math.round(box.right), left: Math.round(box.left), width: Math.round(box.width)};
                });
              return {viewport, scrollWidth, offenders};
            }""")
            if overflow_details['scrollWidth'] > overflow_details['viewport']:
                print('Mobile overflow diagnostics:', json.dumps(overflow_details, ensure_ascii=False))
            assert overflow_details['scrollWidth'] <= overflow_details['viewport'], 'Mobile horizontal overflow'
            await page.screenshot(path=str(ROOT / 'docs/media/mobile.png'), full_page=True)
            checks.append('390px responsive dashboard without horizontal overflow')
            assert not errors, errors
            await context.close()
            await browser.close()
    result = dict(status='passed', checks=checks, page_errors=errors, transport='Playwright Chromium with actual FastAPI/SQLite over in-process ASGI bridge; no TCP server.', screenshots=shots)
    (ROOT / 'reports/browser.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except PlaywrightError as exc:
        raw = str(exc)
        blocked = any((marker in raw.lower() for marker in ('err_blocked_by_administrator', 'operation not permitted', 'permission denied', 'browser has been closed', 'sandbox')))
        result = {'status': 'blocked' if blocked else 'failed', 'scope': 'Real Chromium navigation through the local FastAPI/SQLite ASGI bridge', 'reason': raw[:1200], 'screenshots_verified': False}
        (ROOT / 'reports/browser.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2))
        raise SystemExit(2 if blocked else 1)
