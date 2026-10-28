"""Optional bounded LLM adapter. Offline templates do not impersonate a local LLM."""
import asyncio
import json
import os
import re
import time
from typing import Protocol
import httpx
from pydantic import BaseModel, ConfigDict, Field
from backend.app.config import ROOT

class Explanation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    explanation: str = Field(max_length=1800)
    citation_ids: list[str] = Field(max_length=5)

class Provider(Protocol):

    async def explain(self, evidence: dict) -> dict:
        ...

class OfflineProvider:

    async def explain(self, evidence):
        return dict(provider='offline-template', generative=False, explanation='A interpretação usa templates e evidências estruturadas. Confirme as hipóteses e a cobertura dos intervalos antes de decidir.', citation_ids=[h['document_id'] for h in evidence.get('documents', [])], estimated_tokens=0, latency_ms=0.0, fallback=False)

class ExternalProvider:

    def __init__(self, provider):
        if provider not in ['groq', 'gemini']:
            raise ValueError('Provider not allowed')
        self.provider = provider

    async def explain(self, evidence):
        start = time.perf_counter()
        prompt = (ROOT / 'ai/prompts/coordinator-v1.txt').read_text()
        data = json.dumps(evidence, ensure_ascii=False)[:14000]
        key = os.getenv('LLM_API_KEY', '')
        if not key:
            raise RuntimeError('No provider key')
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(8.0), follow_redirects=False, trust_env=True) as client:
                    if self.provider == 'groq':
                        model = os.getenv('LLM_MODEL') or 'llama-3.3-70b-versatile'
                        response = await client.post('https://api.groq.com/openai/v1/chat/completions', headers={'Authorization': 'Bearer ' + key}, json={'model': model, 'messages': [{'role': 'system', 'content': prompt}, {'role': 'user', 'content': data}], 'temperature': 0, 'max_tokens': 600, 'response_format': {'type': 'json_object'}})
                        response.raise_for_status()
                        body = response.json()
                        content = body['choices'][0]['message']['content']
                        tokens = body.get('usage', {}).get('total_tokens', 0)
                    else:
                        model = os.getenv('LLM_MODEL') or 'gemini-2.5-flash'
                        if not re.fullmatch('[a-zA-Z0-9._-]{1,80}', model):
                            raise ValueError('Invalid model')
                        response = await client.post('https://generativelanguage.googleapis.com/v1beta/models/' + model + ':generateContent', headers={'x-goog-api-key': key}, json={'system_instruction': {'parts': [{'text': prompt}]}, 'contents': [{'parts': [{'text': data}]}], 'generationConfig': {'temperature': 0, 'maxOutputTokens': 600, 'responseMimeType': 'application/json'}})
                        response.raise_for_status()
                        body = response.json()
                        content = body['candidates'][0]['content']['parts'][0]['text']
                        tokens = body.get('usageMetadata', {}).get('totalTokenCount', 0)
                output = Explanation.model_validate_json(content)
                allowed = {h['document_id'] for h in evidence.get('documents', [])}
                if not set(output.citation_ids) <= allowed:
                    raise ValueError('Citation outside evidence')
                if re.search('\\d', output.explanation):
                    raise ValueError('External numerical claims forbidden')
                return dict(provider=self.provider, generative=True, **output.model_dump(), estimated_tokens=tokens or (len(prompt) + len(data) + len(content)) // 4, latency_ms=(time.perf_counter() - start) * 1000, fallback=False, prompt_version='coordinator-v1')
            except (httpx.HTTPError, ValueError, KeyError, IndexError):
                if attempt == 1:
                    raise
                await asyncio.sleep(0.15)

async def explain(evidence):
    chosen = os.getenv('LLM_PROVIDER', 'offline')
    if chosen == 'offline':
        return await OfflineProvider().explain(evidence)
    start = time.perf_counter()
    try:
        return await asyncio.wait_for(ExternalProvider(chosen).explain(evidence), timeout=18.0)
    except (Exception, asyncio.TimeoutError):
        fallback = await OfflineProvider().explain(evidence)
        fallback.update(fallback=True, latency_ms=(time.perf_counter() - start) * 1000, reason='Provider unavailable or output failed validation')
        return fallback
