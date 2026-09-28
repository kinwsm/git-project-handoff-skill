"""Opt-in live smoke test: uses one signed-in Codex turn in a temporary project."""
import asyncio
import hashlib
import json
from pathlib import Path
import tempfile
import uuid

from app_server import AppServer, Handoffs


def snapshot(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            if p.is_file() else '<directory>' for p in root.rglob('*')}


async def verify():
    with tempfile.TemporaryDirectory(prefix='handoff-verify-') as directory:
        base = Path(directory)
        root = base / 'project'
        root.mkdir()
        (root / 'README.md').write_text('Isolated handoff verification fixture.\n', encoding='utf-8')
        before = snapshot(root)
        server = AppServer()
        bridge = Handoffs(base / 'ledger.sqlite3', server, root, title_prefix='Handoff verification | ')
        request_id = 'verify_' + uuid.uuid4().hex[:16]
        try:
            await server.start()
            account = await server.call('account/read', {'refreshToken': False})
            if account.get('requiresOpenaiAuth') and not account.get('account'):
                raise RuntimeError('Sign in with codex login before running the live test')
            result = await bridge.send(request_id,
                'This is an isolated runtime acceptance test. Do not use tools, read files, '
                'edit files, or create agents. Reply with exactly HANDOFF_RUNTIME_OK.')
            print(json.dumps({'delivery': result['status'], 'thread_id': result.get('thread_id')}, ensure_ascii=False), flush=True)
            if result['status'] != 'accepted':
                raise RuntimeError('Delivery uncertain; inspect the printed thread before retrying')
            async with asyncio.timeout(180):
                while True:
                    await asyncio.sleep(2)
                    result = await bridge.status(request_id)
                    if result.get('execution_status') in ('completed', 'failed', 'interrupted'):
                        break
            evidence = {'execution': result.get('execution_status'),
                        'marker_present': 'HANDOFF_RUNTIME_OK' in result.get('response', ''),
                        'project_unchanged': before == snapshot(root)}
            print(json.dumps(evidence), flush=True)
            if not (evidence['execution'] == 'completed' and evidence['marker_present'] and evidence['project_unchanged']):
                raise RuntimeError('Live Codex verification failed')
        finally:
            await server.close()
            bridge.db.close()


if __name__ == '__main__':
    asyncio.run(verify())
