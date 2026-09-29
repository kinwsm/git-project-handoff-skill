"""Opt-in coding acceptance: real Codex, isolated project, local handoff transport."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from git_handoff import Watcher, parse_document, render_document, BEGIN, END

ROOT = Path(__file__).resolve().parents[1]


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True).stdout.decode('utf-8').strip()


def files(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts}


class LocalHandoff:
    """Only replaces GitHub transport; no account/permission claims."""
    def __init__(self, path, root):
        self.path, self.root = path, root

    async def verify_visibility(self):
        pass

    async def api(self, endpoint):
        sha = endpoint.rsplit('/', 1)[-1]
        git(self.root, 'cat-file', '-e', sha + '^{commit}')
        return {'sha': sha}

    async def read(self):
        text = self.path.read_text(encoding='utf-8')
        return hashlib.sha256(text.encode()).hexdigest(), text, parse_document(text, 'acceptance')

    async def publish(self, original, receipt, state):
        _, text, data = await self.read()
        item = next(r for r in data['requests'] if r['request_id'] == original['request_id'])
        item.update(status=state, receipt=receipt)
        self.path.write_text(render_document(text, data), encoding='utf-8')


async def verify(output=None, model=None, effort=None):
    base = (output or ROOT / '.handoff-state' / 'acceptance' / uuid.uuid4().hex[:12]).resolve()
    base.mkdir(parents=True, exist_ok=False)
    root = base / 'project'
    shutil.copytree(ROOT / 'examples' / 'coding-demo', root)
    git(root, 'init', '-q')
    git(root, 'add', '.')
    git(root, '-c', 'user.name=Handoff acceptance', '-c', 'user.email=acceptance@example.invalid', 'commit', '-qm', 'Acceptance fixture')
    command = [sys.executable, '-B', '-m', 'unittest', '-v']
    initial = subprocess.run(command, cwd=root, capture_output=True)
    if initial.returncode == 0:
        raise RuntimeError('Fixture must fail before Codex implements it')
    before = files(root)
    request = {'request_id': 'coding_' + uuid.uuid4().hex[:16], 'status': 'pending',
               'base_commit': git(root, 'rev-parse', 'HEAD'),
               'task': 'Read README.md and implement normalize_whitespace in text_tools.py. Only change text_tools.py. '
                       'Run the six existing tests with Python -B (no bytecode). Do not modify tests, create other files, '
                       'install dependencies, contact external services or spawn agents. This isolated coding task is authorized.',
               'acceptance': 'All six tests pass; only text_tools.py changes. Final response includes HANDOFF_CODING_OK and test evidence.'}
    handoff = base / 'HANDOFF.md'
    data = {'schema_version': 1, 'project_id': 'acceptance', 'requests': [request]}
    handoff.write_text(BEGIN + '\n```json\n' + json.dumps(data) + '\n```\n' + END, encoding='utf-8')
    project = {'id': 'acceptance', 'name': 'Coding acceptance', 'local_root': str(root),
               'repository': 'local/acceptance', 'branch': 'main', 'path': 'HANDOFF.md',
               'model': model, 'reasoning_effort': effort}
    watcher = Watcher(project, base, github=LocalHandoff(handoff, root))
    print(json.dumps({'output': str(base), 'transport': 'local_fixture_not_github'}), flush=True)
    try:
        async with asyncio.timeout(300):
            while True:
                await watcher.tick()
                _, _, document = await watcher.github.read()
                item = document['requests'][0]
                if item['status'] in ('completed', 'failed', 'blocked', 'unknown'):
                    break
                await asyncio.sleep(2)
        result = subprocess.run(command, cwd=root, capture_output=True, timeout=60)
        after = files(root)
        changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
        evidence = {'transport': 'local_fixture_not_github', 'state': item['status'],
                    'tests_exit_code': result.returncode, 'changed_files': changed,
                    'marker_present': 'HANDOFF_CODING_OK' in item['receipt']['response'],
                    'metrics': item['receipt'].get('metrics')}
        (base / 'test-output.txt').write_bytes(result.stdout + result.stderr)
        (base / 'evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(evidence, ensure_ascii=False), flush=True)
        if not (item['status'] == 'completed' and result.returncode == 0 and changed == ['text_tools.py'] and evidence['marker_present']):
            raise RuntimeError('Coding acceptance failed; inspect output directory, do not blindly resend')
    finally:
        await watcher.server.close()
        watcher.db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New directory only; existing directories are refused')
    parser.add_argument('--model')
    parser.add_argument('--effort')
    args = parser.parse_args()
    asyncio.run(verify(args.output, args.model, args.effort))
