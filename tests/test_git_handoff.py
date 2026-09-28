import copy
import json
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
import unittest

from git_handoff import BEGIN, END, GitHub, Watcher, parse_document, render_document

ITEM = {'request_id': 'check_20260923', 'status': 'pending', 'task': 'Only reply ACK',
        'acceptance': 'Reply ACK without changes', 'base_commit': 'a'*40}
PROJECT = {'id': 'demo', 'name': 'Demo', 'local_root': str(Path.cwd()),
           'repository': 'demo/project-share', 'branch': 'main', 'path': 'HANDOFF.md'}


def doc(items):
    return 'prose\n'+BEGIN+'\n```json\n'+json.dumps({'schema_version': 1, 'project_id': 'demo', 'requests': items})+'\n```\n'+END+'\ntail'


class FakeServer:
    def __init__(self, uncertain=False):
        self.calls = []
        self.uncertain = uncertain
        self.done = False

    async def start(self):
        pass

    async def call(self, method, params):
        self.calls.append((method, params))
        if method == 'thread/start':
            return {'thread': {'id': 'test-thread'}}
        if method == 'thread/name/set':
            return {}
        if method == 'turn/start':
            if self.uncertain:
                raise RuntimeError('uncertain delivery')
            return {'turn': {'id': 'test-turn'}}
        if method == 'thread/read':
            return {'thread': {'turns': [{'id': 'test-turn', 'status': 'completed' if self.done else 'inProgress',
                                        'items': [{'type': 'agentMessage', 'text': 'ACK'}] if self.done else []}]}}


class FakeGitHub:
    def __init__(self, items):
        self.data = {'schema_version': 1, 'project_id': 'demo', 'requests': copy.deepcopy(items)}
        self.fail_publish = False
        self.published = []
        self.private = True

    async def verify_visibility(self):
        if not self.private:
            raise ValueError('Public project repository refused')

    async def api(self, endpoint):
        return {'sha': 'a'*40}

    async def read(self):
        return 'sha', doc(self.data['requests']), copy.deepcopy(self.data)

    async def publish(self, original, receipt, state):
        if self.fail_publish:
            raise RuntimeError('offline')
        item = next(i for i in self.data['requests'] if i['request_id'] == original['request_id'])
        item['status'] = state
        item['receipt'] = copy.deepcopy(receipt)
        self.published.append(state)


class Tests(unittest.IsolatedAsyncioTestCase):
    def test_protocol_and_preservation(self):
        text = doc([ITEM])
        data = parse_document(text, 'demo')
        rendered = render_document(text, data)
        self.assertTrue(rendered.startswith('prose\n'))
        self.assertTrue(rendered.endswith('\ntail'))
        with self.assertRaises(ValueError):
            parse_document(doc([ITEM, ITEM]), 'demo')
        with self.assertRaises(ValueError):
            parse_document(text, 'different-project')

    async def test_exactly_once_and_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            server, remote = FakeServer(), FakeGitHub([ITEM])
            w = Watcher(PROJECT, Path(tmp), server, remote)
            await w.tick()
            await w.tick()
            server.done = True
            await w.tick()
            self.assertEqual(sum(m == 'turn/start' for m,p in server.calls), 1)
            self.assertEqual(remote.data['requests'][0]['receipt']['response'], 'ACK')
            self.assertEqual(remote.data['requests'][0]['status'], 'completed')
            w.db.close()

    async def test_visibility_change_stops_polling(self):
        with tempfile.TemporaryDirectory() as tmp:
            server, remote = FakeServer(), FakeGitHub([ITEM])
            remote.private = False
            w = Watcher(PROJECT, Path(tmp), server, remote)
            with self.assertRaises(ValueError):
                await w.tick()
            self.assertEqual(server.calls, [])
            w.db.close()

    async def test_publish_failure_restart_does_not_resend(self):
        with tempfile.TemporaryDirectory() as tmp:
            server, remote = FakeServer(), FakeGitHub([ITEM])
            remote.fail_publish = True
            w = Watcher(PROJECT, Path(tmp), server, remote)
            with self.assertRaises(RuntimeError):
                await w.tick()
            w.db.close()
            remote.fail_publish = False
            w = Watcher(PROJECT, Path(tmp), server, remote)
            await w.tick()
            self.assertEqual(sum(m == 'turn/start' for m,p in server.calls), 1)
            w.db.close()

    async def test_unknown_delivery_never_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            server, remote = FakeServer(True), FakeGitHub([ITEM])
            w = Watcher(PROJECT, Path(tmp), server, remote)
            await w.tick()
            w.db.close()
            w = Watcher(PROJECT, Path(tmp), server, remote)
            await w.tick()
            self.assertEqual(sum(m == 'turn/start' for m,p in server.calls), 1)
            self.assertEqual(remote.data['requests'][0]['status'], 'unknown')
            w.db.close()

    async def test_changed_id_rejected_and_draft_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            server, remote = FakeServer(), FakeGitHub([{**ITEM, 'status': 'draft'}])
            w = Watcher(PROJECT, Path(tmp), server, remote)
            await w.tick()
            self.assertEqual(server.calls, [])
            remote.data['requests'][0]['status'] = 'pending'
            await w.tick()
            remote.data['requests'][0].update(status='pending', task='changed')
            with self.assertRaises(ValueError):
                await w.tick()
            self.assertEqual(sum(m == 'turn/start' for m,p in server.calls), 1)
            w.db.close()

    async def test_compare_and_swap_preserves_concurrent_request(self):
        class ConcurrentGitHub(GitHub):
            def __init__(self):
                self.project = PROJECT
                self.text = doc([ITEM])
                self.writes = 0
            async def read(self):
                return str(self.writes), self.text, parse_document(self.text, 'demo')
            async def api(self, endpoint, body=None):
                import base64
                self.writes += 1
                if self.writes == 1:
                    self.text = doc([ITEM, {**ITEM, 'request_id': 'another_20260923'}])
                    raise RuntimeError('SHA conflict')
                self.text = base64.b64decode(body['content']).decode()
        remote = ConcurrentGitHub()
        await remote.publish(ITEM, {'state': 'running'}, 'running')
        data = parse_document(remote.text, 'demo')
        self.assertEqual(len(data['requests']), 2)
        self.assertEqual(data['requests'][1]['status'], 'pending')


    def test_shipped_template_matches_config(self):
        root = Path(__file__).resolve().parents[1]
        config = json.loads((root/'examples'/'config.example.json').read_text(encoding='utf-8'))
        project_id = config['projects'][0]['id']
        template = (root/'examples'/'HANDOFF.example.md').read_text(encoding='utf-8')
        self.assertEqual(parse_document(template, project_id)['requests'], [])
        self.assertFalse(config['projects'][0]['allow_public_repository'])

    async def test_public_repo_requires_explicit_opt_in(self):
        class PublicGitHub(GitHub):
            def __init__(self, project):
                self.project = project
            async def api(self, endpoint):
                return {'private': False}
        remote = PublicGitHub(dict(PROJECT))
        with self.assertRaises(ValueError):
            await remote.verify_visibility()
        remote.project['allow_public_repository'] = True
        await remote.verify_visibility()


if __name__ == '__main__':
    unittest.main()
