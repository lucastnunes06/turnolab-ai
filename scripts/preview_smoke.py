"""Smoke test for the honest static preview in Chromium; no backend or LLM used."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / 'docs/preview/index.html').as_uri()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page(viewport={'width': 1280, 'height': 850}, locale='pt-BR')
            await page.goto(PAGE, wait_until='load')
            assert await page.title() == 'TurnoLab AI · Experimentos interativos'
            assert ' '.join((await page.locator('#cost').inner_text()).split()) == 'R$ 367,37'
            await page.get_by_role('tab', name='+ Simulação').click()
            assert ' '.join((await page.locator('#cost').inner_text()).split()) == 'R$ 303,31'
            assert await page.locator('#backlog').inner_text() == '11,92'
            await page.get_by_role('tab', name='+ Copiloto').click()
            assert ' '.join((await page.locator('#cost').inner_text()).split()) == 'R$ 303,31'
            images = await page.locator('img').evaluate_all('(imgs) => imgs.every((img) => img.complete && img.naturalWidth > 0)')
            assert images, 'One or more local screenshots are missing'
            await page.set_viewport_size({'width': 390, 'height': 844})
            await page.wait_for_timeout(100)
            width = await page.evaluate('document.documentElement.scrollWidth')
            assert width <= 390, f'Mobile preview overflows: {width}px'
            print('Static portfolio preview: desktop, interactions, images, and mobile 390px OK')
        finally:
            await browser.close()
if __name__ == '__main__':
    asyncio.run(main())
