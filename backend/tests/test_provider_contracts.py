"""Exercise both external HTTP adapters with deterministic transports, not real LLMs."""
import json
import os
import unittest
from unittest.mock import patch
import httpx
from ai.providers import explain

class ProviderContractTests(unittest.IsolatedAsyncioTestCase):

    async def run_provider(self, provider, payload=None, status=200, error=None, model=''):
        calls = []

        async def handler(request):
            calls.append(request)
            if error:
                raise error('Synthetic transport failure', request=request)
            content = json.dumps(payload if payload is not None else {'explanation': 'A capacidade e o estoque limitam a operação.', 'citation_ids': ['capacity']})
            if provider == 'groq':
                result = {'choices': [{'message': {'content': content}}], 'usage': {'total_tokens': 17}}
            else:
                result = {'candidates': [{'content': {'parts': [{'text': content}]}}], 'usageMetadata': {'totalTokenCount': 17}}
            return httpx.Response(status, json=result, request=request)
        transport = httpx.MockTransport(handler)
        client_class = httpx.AsyncClient

        def client_factory(**kwargs):
            return client_class(transport=transport, **kwargs)
        with patch.dict(os.environ, {'LLM_PROVIDER': provider, 'LLM_API_KEY': 'synthetic-test-token', 'LLM_MODEL': model}), patch('ai.providers.httpx.AsyncClient', side_effect=client_factory):
            result = await explain({'documents': [{'document_id': 'capacity', 'text': 'Corpus fictício para teste de contrato.'}]})
        return (result, calls)

    async def test_groq_request_and_structured_success(self):
        result, calls = await self.run_provider('groq')
        self.assertTrue(result['generative'])
        self.assertFalse(result['fallback'])
        self.assertEqual(len(calls), 1)
        self.assertEqual(str(calls[0].url), 'https://api.groq.com/openai/v1/chat/completions')
        self.assertEqual(calls[0].headers['Authorization'], 'Bearer synthetic-test-token')
        request = json.loads(calls[0].content)
        self.assertEqual(request['response_format'], {'type': 'json_object'})
        self.assertNotIn('tools', request)
        self.assertEqual(result['citation_ids'], ['capacity'])

    async def test_gemini_request_and_structured_success(self):
        result, calls = await self.run_provider('gemini')
        self.assertTrue(result['generative'])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].url.host, 'generativelanguage.googleapis.com')
        self.assertEqual(calls[0].headers['x-goog-api-key'], 'synthetic-test-token')
        self.assertEqual(json.loads(calls[0].content)['generationConfig']['responseMimeType'], 'application/json')

    async def test_unsupported_citation_rejected_after_bounded_retry(self):
        result, calls = await self.run_provider('groq', {'explanation': 'Texto sem suporte.', 'citation_ids': ['invented-document']})
        self.assertTrue(result['fallback'])
        self.assertFalse(result['generative'])
        self.assertEqual(len(calls), 2)

    async def test_new_operational_numbers_rejected(self):
        result, calls = await self.run_provider('gemini', {'explanation': 'Contrate 99 pessoas.', 'citation_ids': ['capacity']})
        self.assertTrue(result['fallback'])
        self.assertEqual(len(calls), 2)
        self.assertNotIn('99', result['explanation'])

    async def test_extra_schema_fields_rejected(self):
        result, calls = await self.run_provider('groq', {'explanation': 'Texto.', 'citation_ids': [], 'tool': 'approve_action'})
        self.assertTrue(result['fallback'])
        self.assertEqual(len(calls), 2)

    async def test_http_failure_has_two_attempt_limit(self):
        result, calls = await self.run_provider('groq', status=503)
        self.assertTrue(result['fallback'])
        self.assertEqual(len(calls), 2)

    async def test_timeout_falls_back_without_leaking_exception_text(self):
        result, calls = await self.run_provider('gemini', error=httpx.ReadTimeout)
        self.assertTrue(result['fallback'])
        self.assertEqual(len(calls), 2)
        self.assertNotIn('Synthetic transport failure', json.dumps(result))

    async def test_invalid_gemini_model_cannot_change_request_destination(self):
        result, calls = await self.run_provider('gemini', model='../attacker?key=anything')
        self.assertTrue(result['fallback'])
        self.assertEqual(len(calls), 0)

    async def test_unknown_provider_never_opens_http(self):
        result, calls = await self.run_provider('arbitrary-url')
        self.assertTrue(result['fallback'])
        self.assertEqual(len(calls), 0)
