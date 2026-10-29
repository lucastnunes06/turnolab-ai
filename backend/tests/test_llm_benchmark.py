"""Check benchmark honesty and that every prompt is provided with the evidence."""
import unittest
from scripts.llm_benchmark import CASES, prepare_cases, evaluate

class LlmBenchmarkTests(unittest.IsolatedAsyncioTestCase):

    async def test_offline_does_not_claim_a_real_llm(self):
        result = await evaluate('offline')
        self.assertEqual(result['evaluated_cases'], len(CASES))
        self.assertEqual(result['failed_cases'], 0)
        self.assertFalse(result['real_external_llm_executed'])
        self.assertEqual(result['provider'], 'offline')

    async def test_user_question_is_part_of_the_evidence(self):
        cases = list(prepare_cases())
        self.assertEqual(len(cases), len(CASES))
        for case in cases:
            self.assertEqual(case['question'], case['evidence']['question'])
            self.assertIsInstance(case['retrieved_ids'], list)
