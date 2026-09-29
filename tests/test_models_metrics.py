from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
from app_server import AppServer, Handoffs, SetupError, validate_selection


class Server:
    def __init__(self):
        self.calls = []
        self.observations = {}
        self.initializing = False

    async def start(self):
        pass

    async def call(self, method, params):
        self.calls.append((method, params))
        if method == 'model/list':
            if not params.get('cursor'):
                return {'data': [], 'nextCursor': 'page2'}
            return {'data': [{'id': 'demo-model', 'model': 'demo-model',
                             'supportedReasoningEfforts': [{'reasoningEffort': 'medium'}]}]}
        if method == 'thread/start':
            return {'thread': {'id': 'thread'}, 'model': 'demo-model', 'reasoningEffort': 'medium'}
        if method == 'turn/start':
            return {'turn': {'id': 'turn'}}
        if method == 'thread/read':
            if self.initializing:
                raise RuntimeError('rollout at path is empty')
            return {'thread': {'turns': [{'id': 'turn', 'status': 'completed',
                                         'items': [{'type': 'agentMessage', 'text': 'OK'}]}]}}
        return {}


class Tests(unittest.IsolatedAsyncioTestCase):
    async def test_selection_is_validated_and_forwarded(self):
        with tempfile.TemporaryDirectory() as tmp:
            server = Server()
            h = Handoffs(Path(tmp)/'ledger.db', server, tmp, model='demo-model', effort='medium')
            try:
                await h.send('request_123', 'test')
                turn = next(p for m, p in server.calls if m == 'turn/start')
                self.assertEqual((turn['model'], turn['effort']), ('demo-model', 'medium'))
                self.assertEqual(len([m for m, _ in server.calls if m == 'model/list']), 2)
            finally:
                h.db.close()

    async def test_invalid_selection_never_dispatches(self):
        for model, effort in [('missing', None), ('demo-model', 'unsupported'), (None, 'medium')]:
            with self.subTest(model=model, effort=effort):
                server = Server()
                with self.assertRaises(SetupError):
                    await validate_selection(server, model, effort)
                self.assertFalse(any(m == 'thread/start' for m, _ in server.calls))

    async def test_unavailable_model_leaves_no_dispatch_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = Handoffs(Path(tmp)/'ledger.db', Server(), tmp, model='missing')
            try:
                with self.assertRaises(SetupError):
                    await h.send('request_123', 'test')
                self.assertEqual(h.db.execute('SELECT COUNT(*) FROM handoffs').fetchone()[0], 0)
            finally:
                h.db.close()

    async def test_metrics_survive_restart_and_config_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'ledger.db'
            server = Server()
            h = Handoffs(path, server, tmp)
            try:
                await h.send('request_123', 'test')
                server.observations[('thread', 'turn')] = {'tokens': {'inputTokens': 100, 'outputTokens': 5},
                                                         'attention_required': 'approval_required'}
                result = await h.status('request_123')
                self.assertEqual(result['metrics']['tokens']['inputTokens'], 100)
                self.assertGreaterEqual(result['metrics']['wall_seconds'], 0)
            finally:
                h.db.close()
            restarted = Server()
            h = Handoffs(path, restarted, tmp, model='missing')
            try:
                result = await h.send('request_123', 'test')
                self.assertEqual(result['metrics']['tokens']['inputTokens'], 100)
                self.assertEqual(result['metrics']['resolved_model'], 'demo-model')
                self.assertEqual(restarted.calls, [])
            finally:
                h.db.close()

    async def test_missing_usage_is_not_zero_and_startup_race_does_not_resend(self):
        with tempfile.TemporaryDirectory() as tmp:
            server = Server()
            h = Handoffs(Path(tmp)/'ledger.db', server, tmp)
            try:
                await h.send('request_123', 'test')
                server.initializing = True
                result = await h.status('request_123')
                self.assertEqual(result['execution_status'], 'inProgress')
                server.initializing = False
                result = await h.status('request_123')
                self.assertIsNone(result['metrics']['tokens'])
                self.assertEqual(len([m for m, _ in server.calls if m == 'turn/start']), 1)
            finally:
                h.db.close()

    def test_legacy_ledger_migrates_without_losing_deduplication(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'ledger.db'
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE handoffs (request_id TEXT PRIMARY KEY, digest TEXT, status TEXT, thread_id TEXT, turn_id TEXT, error TEXT)')
                db.execute("INSERT INTO handoffs VALUES ('old_request', 'hash', 'unknown', NULL, NULL, NULL)")
            db.close()
            h = Handoffs(path, Server(), tmp)
            try:
                self.assertEqual(h.get('old_request')['status'], 'unknown')
                self.assertEqual(h.get('old_request')['metrics'], {})
            finally:
                h.db.close()

    def test_usage_notifications_replace_cumulative_counts(self):
        server = AppServer()
        for total in (10, 20):
            server.observe('thread/tokenUsage/updated', {'threadId': 't', 'turnId': 'u',
                'tokenUsage': {'total': {'totalTokens': total, 'private_text': 'omit'}}})
        self.assertEqual(server.observations[('t', 'u')]['tokens'], {'totalTokens': 20})


if __name__ == '__main__':
    unittest.main()
