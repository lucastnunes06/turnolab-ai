"""CI evidence is accepted only for a matching real commit, using test HTTP fixtures here."""
import unittest
from unittest.mock import patch
import httpx
from scripts.release_check import github_check

class ReleaseEvidenceTests(unittest.TestCase):

    def test_unconfigured_ci_is_never_marked_passed(self):
        self.assertEqual(github_check()['status'], 'blocked')

    def test_arbitrary_url_is_rejected(self):
        self.assertEqual(github_check('https://attacker.invalid/actions/runs/1')['status'], 'failed')

    def verify_run(self, sha, conclusion='success'):

        def local_command(args, **kwargs):
            return {'status': 'passed', 'output': 'a' * 40 if args[1] == 'rev-parse' else ''}

        def handler(request):
            self.assertEqual(request.url.host, 'api.github.com')
            return httpx.Response(200, json={'head_sha': sha, 'status': 'completed', 'conclusion': conclusion}, request=request)
        client_class = httpx.Client

        def factory(**kwargs):
            return client_class(transport=httpx.MockTransport(handler), **kwargs)
        with patch('scripts.release_check.command', side_effect=local_command), patch('scripts.release_check.httpx.Client', side_effect=factory):
            return github_check('https://github.com/example/turnolab/actions/runs/1')

    def test_unrelated_successful_workflow_does_not_verify_source(self):
        self.assertEqual(self.verify_run('b' * 40)['status'], 'failed')

    def test_matching_commit_and_successful_run_are_required(self):
        self.assertEqual(self.verify_run('a' * 40)['status'], 'passed')
        self.assertEqual(self.verify_run('a' * 40, 'failure')['status'], 'failed')
